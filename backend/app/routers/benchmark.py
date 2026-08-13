"""同业对比分析 API"""
import os, shutil, tempfile
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import (
    IalmdIndicatorDefine, IalmdIndicatorValue, IalmdBankInstitution, IalmdBenchmarkCompare,
)
from ..schemas.common import ResponseBase
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/benchmark", tags=["同业对比"])


@router.get("/compare", response_model=ResponseBase)
def compare_banks(
    indicator_code: str = Query(..., description="指标编码"),
    report_year: int = Query(2025, description="数据年份"),
    bank_type: Optional[str] = Query(None, description="机构类型过滤"),
    bank_ids: Optional[str] = Query(None, description="指定机构ID，逗号分隔"),
    report_period: str = Query("FY", description="报告期间: FY/H1/Q3"),
    top_n: int = Query(47, ge=5, le=47, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """同业指标对比：排名 + 统计 + 分布"""
    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()
    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    query = db.query(
        IalmdIndicatorValue.value_numeric,
        IalmdIndicatorValue.report_year,
        IalmdBankInstitution.short_name,
        IalmdBankInstitution.bank_code,
        IalmdBankInstitution.bank_type,
        IalmdBankInstitution.id.label("institution_id"),
    ).join(
        IalmdBankInstitution,
        IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == report_year,
        IalmdIndicatorValue.report_period == report_period,
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
        IalmdBankInstitution.status == 1,
    )

    if bank_type:
        query = query.filter(IalmdBankInstitution.bank_type == bank_type)
    if bank_ids:
        ids = [int(x) for x in bank_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(IalmdBankInstitution.id.in_(ids))

    rows = query.order_by(
        IalmdIndicatorValue.value_numeric.is_(None),
        IalmdIndicatorValue.value_numeric.desc(),
    ).all()

    ranking, valid_values = [], []
    for idx, (val, year, name, code, btype, inst_id) in enumerate(rows[:top_n]):
        if val is not None:
            valid_values.append(float(val))
        ranking.append({
            "rank": idx + 1,
            "bank_name": name, "bank_code": code, "bank_type": btype,
            "institution_id": inst_id, "report_year": year,
            "value": round(float(val), indicator.decimal_places) if val is not None else None,
        })

    stats = {}
    if valid_values:
        sv = sorted(valid_values)
        n = len(sv)
        stats = {
            "max": round(max(valid_values), indicator.decimal_places),
            "min": round(min(valid_values), indicator.decimal_places),
            "avg": round(sum(valid_values) / n, indicator.decimal_places),
            "median": round(sv[n // 2], indicator.decimal_places) if n > 0 else None,
            "count": n,
            "p25": round(sv[n // 4], indicator.decimal_places),
            "p75": round(sv[3 * n // 4], indicator.decimal_places),
        }

    return ResponseBase(data={
        "indicator": {"code": indicator.indicator_code, "name": indicator.indicator_name, "unit": indicator.unit},
        "report_year": report_year, "report_period": report_period,
        "stats": stats, "ranking": ranking,
    })


@router.get("/available-years", response_model=ResponseBase)
def available_years(
    indicator_code: str = Query(..., description="指标编码"),
    report_period: str = Query("FY", description="报告期间"),
    db: Session = Depends(get_db),
):
    """获取某指标可用的年份列表"""
    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code, IalmdIndicatorDefine.status == 1,
    ).first()
    if not indicator:
        return ResponseBase(code=404, message="指标不存在")
    years = db.query(
        func.distinct(IalmdIndicatorValue.report_year)
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_period == report_period,
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).order_by(IalmdIndicatorValue.report_year.desc()).all()
    return ResponseBase(data=[y[0] for y in years])


@router.post("/save", response_model=ResponseBase)
def save_comparison(
    indicator_code: str = Query(...),
    report_year: int = Query(...),
    bank_ids: str = Query(...),
    report_period: str = Query("FY"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """保存一次对比记录"""
    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code, IalmdIndicatorDefine.status == 1,
    ).first()
    if not indicator:
        return ResponseBase(code=404, message="指标不存在")

    # 执行对比
    ids = [int(x) for x in bank_ids.split(",") if x.strip().isdigit()]
    values = db.query(
        IalmdIndicatorValue.value_numeric,
        IalmdBankInstitution.short_name,
    ).join(
        IalmdBankInstitution, IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == report_year,
        IalmdIndicatorValue.report_period == report_period,
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
        IalmdBankInstitution.id.in_(ids),
    ).all()

    ranking = [{"bank": name, "value": float(v) if v else None} for v, name in values]

    record = IalmdBenchmarkCompare(
        indicator_id=indicator.id,
        compare_type="PEER",
        institution_json=ids,
        result_json={"ranking": ranking, "stats": {}},
        report_year=report_year,
        report_period=report_period,
        created_by=current_user.get("id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ResponseBase(data={"id": record.id, "saved_at": str(record.created_at)}, message="对比记录已保存")


@router.get("/history", response_model=ResponseBase)
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查看历史对比记录"""
    q = db.query(IalmdBenchmarkCompare).filter(
        IalmdBenchmarkCompare.status == 1, IalmdBenchmarkCompare.is_deleted == 0,
    ).order_by(IalmdBenchmarkCompare.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return ResponseBase(data={
        "items": [{
            "id": i.id, "indicator_id": i.indicator_id,
            "result_json": i.result_json, "institution_json": i.institution_json,
            "report_year": i.report_year, "report_period": i.report_period,
            "created_at": str(i.created_at),
        } for i in items],
        "total": total, "page": page, "page_size": page_size,
    })


@router.post("/upload-report", response_model=ResponseBase)
async def upload_own_report(
    file: UploadFile = File(...),
    report_year: int = Form(...),
    bank_type: str = Form("JOINT_STOCK"),
    bank_name: str = Form("本行"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """上传本行年报 → 自动提取指标 → 返回对比结果"""
    # 1. 保存上传文件
    upload_dir = os.path.join(tempfile.gettempdir(), "ialmd_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    suffix = os.path.splitext(file.filename or "report.pdf")[1] or ".pdf"
    saved_path = os.path.join(upload_dir, f"own_report_{current_user.get('id', 0)}_{report_year}{suffix}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    # 2. 提取指标
    extracted = _extract_indicators_from_pdf(saved_path, report_year)

    # 3. 系统均值 / 同类型均值 / 先进银行对比
    indicators = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.status == 1,
    ).all()
    ind_map = {i.indicator_name: (i.id, i.indicator_code) for i in indicators}

    comparison = []
    for ind_name, val, unit, ind_code in extracted:
        if not val or ind_code not in [c for _, c in ind_map.values()]:
            continue

        # 系统全量均值
        sys_avg = db.query(func.avg(IalmdIndicatorValue.value_numeric)).join(
            IalmdBankInstitution, IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
        ).filter(
            IalmdIndicatorValue.indicator_code == ind_code,
            IalmdIndicatorValue.report_year == report_year,
            IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
        ).scalar()
        sys_avg = round(float(sys_avg), 2) if sys_avg else None

        # 同类型均值
        type_avg = db.query(func.avg(IalmdIndicatorValue.value_numeric)).join(
            IalmdBankInstitution, IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
        ).filter(
            IalmdIndicatorValue.indicator_code == ind_code,
            IalmdIndicatorValue.report_year == report_year,
            IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
            IalmdBankInstitution.bank_type == bank_type,
        ).scalar()
        type_avg = round(float(type_avg), 2) if type_avg else None

        # 先进银行 (前3名)
        top3 = db.query(
            IalmdIndicatorValue.value_numeric,
            IalmdBankInstitution.short_name,
        ).join(
            IalmdBankInstitution, IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
        ).filter(
            IalmdIndicatorValue.indicator_code == ind_code,
            IalmdIndicatorValue.report_year == report_year,
            IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
        ).order_by(IalmdIndicatorValue.value_numeric.desc()).limit(3).all()

        comparison.append({
            "indicator_name": ind_name,
            "indicator_code": ind_code,
            "unit": unit,
            "own_value": val,
            "sys_avg": sys_avg,
            "type_avg": type_avg,
            "type_label": type_map_display.get(bank_type, bank_type),
            "top3": [{"name": n, "value": round(float(v), 2) if v else None} for v, n in top3],
            "vs_avg_pct": round((val - sys_avg) / sys_avg * 100, 1) if sys_avg and sys_avg != 0 else None,
        })

    return ResponseBase(data={
        "bank_name": bank_name,
        "report_year": report_year,
        "indicators_found": len(extracted),
        "comparisons": len(comparison),
        "comparison": comparison,
    }, message=f"提取 {len(extracted)} 个指标，完成对比")


type_map_display = {
    "LARGE_STATE": "国有大行", "JOINT_STOCK": "股份制银行",
    "CITY_COMMERCIAL": "城商行", "RURAL_COMMERCIAL": "农商行", "POLICY": "政策性银行",
}


def _extract_indicators_from_pdf(filepath: str, report_year: int) -> list[tuple]:
    """从PDF中提取指标（简化版pypdf提取）"""
    results = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        full_text = ""
        for page in reader.pages[:20]:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        # 预处理
        text = full_text.replace("\n", " ")

        # 预定义指标提取规则（中文名+单位+code）
        patterns = [
            (r"营业收入\D*?([\d,.]+)\s*(百万元|亿元|元)", "营业收入", "PROFIT_REVENUE"),
            (r"营业利润\D*?([\d,.]+)\s*(百万元|亿元|元)", "营业利润", "PROFIT_OP_INC"),
            (r"(?:归[属于]?\s*)?净利润\D*?([\d,.]+)\s*(百万元|亿元|元)", "净利润", "PROFIT_NET_INC"),
            (r"净利息收入\D*?([\d,.]+)\s*(百万元|亿元|元)", "利息净收入", "PROFIT_NII"),
            (r"总资产\D*?([\d,.]+)\s*(百万元|亿元|元)", "总资产", "ASSET_LIAB_TOTAL_ASSET"),
            (r"总负债\D*?([\d,.]+)\s*(百万元|亿元|元)", "总负债", "ASSET_LIAB_TOTAL_LIAB"),
            (r"(?:不良贷款率|不良贷款比率)\D*?([\d,.]+)\s*%", "不良贷款率", "ASSET_QUALITY_NPL"),
            (r"拨备覆盖率\D*?([\d,.]+)\s*%", "拨备覆盖率", "ASSET_QUALITY_PCR"),
            (r"资本充足率\D*?([\d,.]+)\s*%", "资本充足率", "CAPITAL_ADEQUACY_CAR"),
            (r"核心一级资本充足率\D*?([\d,.]+)\s*%", "核心一级资本充足率", "CAPITAL_ADEQUACY_CET1_RATIO"),
            (r"(?:加权平均)?净资产收益率.*?([\d,.]+)\s*%", "净资产收益率(ROE)", "PROFITABILITY_ROE"),
            (r"净息差\D*?([\d,.]+)\s*%", "净息差", "PROFITABILITY_NIM"),
            (r"成本收入比\D*?([\d,.]+)\s*%", "成本收入比", "PROFITABILITY_CIR"),
            (r"存贷比\D*?([\d,.]+)\s*%", "存贷比", "LIQUID_LDR"),
            (r"流动性覆盖率.*?([\d,.]+)\s*%", "流动性覆盖率(LCR)", "LIQUID_LCR"),
        ]

        import re
        for pattern, name, code in patterns:
            m = re.search(pattern, text)
            if m:
                v = float(m.group(1).replace(",", ""))
                unit = m.group(2) if len(m.groups()) > 1 and m.group(2) in ["百万元", "亿元", "元", "%"] else "%" if "%" in pattern else ""
                if unit == "百万元":
                    pass  # keep as-is
                elif unit == "亿元":
                    v *= 100  # 亿元→百万元
                elif unit == "元":
                    v /= 1000000  # 元→百万元
                results.append((name, round(v, 2), "百万元" if unit not in ["%"] else "%", code))
    except Exception as e:
        pass

    return results
