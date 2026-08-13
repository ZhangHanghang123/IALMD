"""报告采集 API — 下载报告 + 指标提取 + 入库"""
import os, json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..database import get_db
from ..models.bank import IalmdBankInstitution
from ..models.ontology import IalmdBankReportLink, IalmdOntologyClass
from ..models.indicator import IalmdIndicatorDefine, IalmdIndicatorValue
from ..models.report import IalmdReportRecord
from ..schemas.common import ResponseBase, PageResponse
from ..dependencies import get_current_user
from ..services.report_collector import (
    extract_indicators_from_bank, batch_extract_all, DOWNLOAD_ROOT,
)

router = APIRouter(prefix="/api/report-collect", tags=["报告采集"])

# ==================== 1. 采集任务管理 ====================

@router.get("/tasks", response_model=PageResponse)
def list_tasks(
    page: int = 1, page_size: int = 20,
    institution_id: Optional[int] = None,
    report_type: Optional[str] = None,
    extraction_status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出采集任务/报告关联记录"""
    q = db.query(IalmdBankReportLink, IalmdBankInstitution).join(
        IalmdBankInstitution, IalmdBankReportLink.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdBankReportLink.is_deleted == 0,
        IalmdBankInstitution.is_deleted == 0,
    )
    if institution_id:
        q = q.filter(IalmdBankReportLink.institution_id == institution_id)
    if report_type:
        q = q.filter(IalmdBankReportLink.report_type == report_type)
    if extraction_status:
        q = q.filter(IalmdBankReportLink.extraction_status == extraction_status)
    if keyword:
        q = q.filter(IalmdBankInstitution.bank_name.like(f"%{keyword}%"))

    total = q.count()
    rows = q.order_by(desc(IalmdBankReportLink.report_year), IalmdBankInstitution.bank_code).offset(
        (page - 1) * page_size).limit(page_size).all()

    data = []
    for link, bank in rows:
        data.append({
            "id": link.id,
            "institution_id": link.institution_id,
            "bank_name": bank.bank_name,
            "bank_code": link.bank_code,
            "report_type": link.report_type,
            "report_year": link.report_year,
            "report_period": link.report_period,
            "file_name": link.file_name,
            "file_format": link.file_format,
            "file_size": link.file_size,
            "file_path": link.file_path,
            "extraction_status": link.extraction_status,
            "extracted_count": link.extracted_count,
            "last_extracted_at": link.last_extracted_at.isoformat() if link.last_extracted_at else None,
            "scan_time": link.scan_time.isoformat() if link.scan_time else None,
        })

    return PageResponse(data=data, total=total, page=page, page_size=page_size)


# ==================== 2. 触发采集 ====================

@router.post("/collect", response_model=ResponseBase)
def trigger_collection(
    bank_ids: str = Query(..., description="银行ID列表，逗号分隔"),
    report_types: str = Query("ANNUAL,HALF,QREPORT", description="报告类型"),
    years: str = Query("", description="年份"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """触发报告采集（当前版本：扫描本地已有文件并建索引，在线下载留待爬虫实现）"""
    bid_list = [int(x.strip()) for x in bank_ids.split(",") if x.strip().isdigit()]
    if not bid_list:
        raise HTTPException(status_code=400, detail="请提供银行ID")

    # 扫描本地文件夹，建立报告索引
    from app.models.bank import IalmdBankInstitution
    from app.models.ontology import IalmdBankReportLink
    import re

    type_dirs = {"ANNUAL":"年度报告","HALF":"半年度报告","QREPORT":"季度报告",
                 "EXPRESS":"业绩快报","CAPITAL":"资本充足率信息披露报告",
                 "ESG":"社会责任报告ESG","LIQUIDITY":"流动性风险信息披露报告"}
    pattern = re.compile(r"(\d{4})年.*\.(html|pdf)$", re.IGNORECASE)

    result = {"downloaded": 0, "skipped": 0, "banks": []}
    for bid in bid_list:
        bank = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.id == bid, IalmdBankInstitution.is_deleted == 0,
        ).first()
        if not bank: continue

        bank_dir = DOWNLOAD_ROOT / bank.bank_name
        if not bank_dir.exists(): continue

        for td_name, rtype in type_dirs.items():
            td = bank_dir / td_name
            if not td.exists(): continue
            for fn in td.iterdir():
                if not fn.is_file(): continue
                m = pattern.match(fn.name)
                if not m: continue
                year, fmt = int(m.group(1)), m.group(2).upper()
                period = "FY"
                if "半年" in fn.name: period = "H1"
                elif "三季" in fn.name: period = "Q3"

                exists = db.query(IalmdBankReportLink).filter(
                    IalmdBankReportLink.bank_code==bank.bank_code,
                    IalmdBankReportLink.report_type==rtype,
                    IalmdBankReportLink.report_year==year,
                    IalmdBankReportLink.file_format==fmt,
                ).first()
                if exists:
                    result["skipped"] += 1
                    continue
                try:
                    link = IalmdBankReportLink(
                        institution_id=bank.id, bank_code=bank.bank_code,
                        report_type=rtype, report_year=year, report_period=period,
                        file_format=fmt, file_name=fn.name,
                        file_path=str(fn.relative_to(DOWNLOAD_ROOT)).replace("\\", "/"),
                        file_size=fn.stat().st_size, exists_flag=1,
                        extraction_status="PENDING",
                    )
                    db.add(link)
                    result["downloaded"] += 1
                except: pass
        result["banks"].append({"id": bid, "name": bank.bank_name})
    db.commit()
    return ResponseBase(data=result, message=f"扫描完成: 新增 {result['downloaded']}，跳过 {result['skipped']}")


@router.post("/collect/{bank_id}", response_model=ResponseBase)
def trigger_single_collection(
    bank_id: int, report_types: str = Query(""), years: str = Query(""),
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    """单银行采集（重定向到批量）"""
    return trigger_collection(
        bank_ids=str(bank_id), report_types=report_types, years=years,
        db=db, current_user=current_user,
    )


# ==================== 3. 触发指标提取 ====================

@router.post("/extract/{bank_id}", response_model=ResponseBase)
def trigger_extraction(
    bank_id: int,
    years: str = Query("", description="年份列表"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """触发指标提取（从已有报告文件中提取）"""
    yr_list = [int(x.strip()) for x in years.split(",") if x.strip().isdigit()] if years else None
    result = extract_indicators_from_bank(bank_id, years=yr_list, db_session=db)
    return ResponseBase(data=result, message=f"提取完成: {result.get('extracted', 0)} 个指标值")


@router.post("/extract-all", response_model=ResponseBase)
def trigger_extract_all(
    bank_type: str = Query("", description="限定机构类型"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """批量提取所有银行的指标"""
    result = batch_extract_all(db, bank_type=bank_type or None)
    return ResponseBase(data=result, message=f"完成: {result['total_extracted']} 个指标值")


# ==================== 4. 提取结果 ====================

@router.get("/extract-results", response_model=PageResponse)
def list_extract_results(
    page: int = 1, page_size: int = 30,
    institution_id: Optional[int] = None,
    indicator_id: Optional[int] = None,
    report_year: Optional[int] = None,
    verify_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查看指标提取结果"""
    q = db.query(IalmdIndicatorValue, IalmdIndicatorDefine, IalmdBankInstitution).join(
        IalmdIndicatorDefine, IalmdIndicatorValue.indicator_id == IalmdIndicatorDefine.id,
    ).join(
        IalmdBankInstitution, IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.is_deleted == 0,
    )
    if institution_id:
        q = q.filter(IalmdIndicatorValue.institution_id == institution_id)
    if indicator_id:
        q = q.filter(IalmdIndicatorValue.indicator_id == indicator_id)
    if report_year:
        q = q.filter(IalmdIndicatorValue.report_year == report_year)
    if verify_status:
        q = q.filter(IalmdIndicatorValue.verify_status == verify_status)

    total = q.count()
    rows = q.order_by(desc(IalmdIndicatorValue.id)).offset((page - 1) * page_size).limit(page_size).all()

    data = []
    for val, ind, bank in rows:
        data.append({
            "id": val.id,
            "bank_name": bank.bank_name,
            "indicator_name": ind.indicator_name,
            "indicator_code": ind.indicator_code,
            "value": float(val.value_numeric) if val.value_numeric else val.value_text,
            "unit": ind.unit,
            "year": val.report_year,
            "confidence": float(val.confidence) if val.confidence else 0,
            "verify_status": val.verify_status,
            "source": val.extract_context[:100] if val.extract_context else "",
        })

    return PageResponse(data=data, total=total, page=page, page_size=page_size)


# ==================== 5. 手动上传 ====================

@router.post("/upload/{bank_id}", response_model=ResponseBase)
def upload_report(
    bank_id: int,
    report_type: str = Query(...),
    report_year: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """手动上传报告文件"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id, IalmdBankInstitution.is_deleted == 0,
    ).first()
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")

    type_map = {
        "ANNUAL": "年度报告", "HALF": "半年度报告", "QREPORT": "季度报告",
        "EXPRESS": "业绩快报", "CAPITAL": "资本充足率信息披露报告",
        "ESG": "社会责任报告ESG", "LIQUIDITY": "流动性风险信息披露报告",
        "INCLUSIVE": "普惠金融服务报告", "CONSUMER": "消费者权益保护工作报告",
        "GREEN": "绿色金融专项报告",
    }
    type_dir_name = type_map.get(report_type, report_type)
    target_dir = DOWNLOAD_ROOT / bank.bank_name / type_dir_name
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1]
    save_name = f"{report_year}年{type_dir_name}{ext}"
    save_path = target_dir / save_name

    with open(save_path, "wb") as f:
        f.write(file.file.read())

    rel_path = str(save_path.relative_to(DOWNLOAD_ROOT)).replace("\\", "/")

    # 注册到数据库
    link = IalmdBankReportLink(
        institution_id=bank.id, bank_code=bank.bank_code,
        report_type=report_type, report_year=report_year, report_period="FY",
        file_format=ext.upper().lstrip("."), file_name=save_name,
        file_path=rel_path,
        file_size=save_path.stat().st_size, exists_flag=1,
        extraction_status="PENDING",
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return ResponseBase(data={
        "id": link.id, "file_name": save_name, "file_path": rel_path,
    }, message="上传成功")


# ==================== 6. 下载报告 ====================

@router.get("/download/{bank_id}")
def download_report(
    bank_id: int,
    link_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """下载报告文件"""
    link = db.query(IalmdBankReportLink).filter(IalmdBankReportLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="记录不存在")

    full_path = DOWNLOAD_ROOT / link.file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(str(full_path), filename=link.file_name, media_type="application/octet-stream")


# ==================== 7. 统计 ====================

@router.get("/stats", response_model=ResponseBase)
def get_collect_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取采集统计"""
    total_reports = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.is_deleted == 0,
    ).scalar() or 0
    parsed = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.is_deleted == 0,
        IalmdBankReportLink.extraction_status == "PARSED",
    ).scalar() or 0
    pending = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.is_deleted == 0,
        IalmdBankReportLink.extraction_status == "PENDING",
    ).scalar() or 0
    indicator_count = db.query(func.count(IalmdIndicatorValue.id)).filter(
        IalmdIndicatorValue.is_deleted == 0,
    ).scalar() or 0

    # 按报告类型统计
    type_stats = {}
    rows = db.query(
        IalmdBankReportLink.report_type,
        func.count(IalmdBankReportLink.id),
    ).filter(IalmdBankReportLink.is_deleted == 0).group_by(IalmdBankReportLink.report_type).all()
    for rt, cnt in rows:
        type_stats[rt] = cnt

    return ResponseBase(data={
        "total_reports": total_reports, "parsed": parsed, "pending": pending,
        "extracted_indicators": indicator_count,
        "by_type": type_stats,
    })