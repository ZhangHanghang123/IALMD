"""首页仪表盘 API — 全部数据从数据库实时统计（Redis 缓存加速）"""
import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..database import get_db
from ..cache import redis_client
from ..models import (
    IalmdBankInstitution, IalmdIndicatorDefine, IalmdReportRecord,
    IalmdIndicatorValue, IalmdOntologyClass, IalmdOntologyRelation,
    IalmdChatSession, IalmdChatMessage, IalmdIndicatorMapping,
    IalmdReportFile, IalmdWorkflowDef, IalmdWorkflowExec,
    IalmdBankReportLink,
)
from ..schemas.common import ResponseBase
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])
logger = logging.getLogger(__name__)

DASHBOARD_CACHE_KEY = "dashboard:v2"
DASHBOARD_CACHE_TTL = 300  # 5 分钟


@router.get("", response_model=ResponseBase)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取首页仪表盘数据（Redis 缓存 5 分钟）"""

    # 1. 尝试从 Redis 读取缓存
    try:
        cached = redis_client.get(DASHBOARD_CACHE_KEY)
        if cached:
            logger.info("Dashboard: Redis cache hit")
            return ResponseBase(data=json.loads(cached))
    except Exception as e:
        logger.warning(f"Redis 读取缓存失败: {e}，回退到数据库查询")

    # ─── KPI 基础统计 ───
    bank_count = db.query(func.count(IalmdBankInstitution.id)).filter(
        IalmdBankInstitution.status == 1, IalmdBankInstitution.is_deleted == 0,
    ).scalar() or 0

    indicator_count = db.query(func.count(IalmdIndicatorDefine.id)).filter(
        IalmdIndicatorDefine.status == 1, IalmdIndicatorDefine.is_deleted == 0,
    ).scalar() or 0

    report_count = db.query(func.count(IalmdReportRecord.id)).filter(
        IalmdReportRecord.status == 1, IalmdReportRecord.is_deleted == 0,
    ).scalar() or 0

    report_file_count = db.query(func.count(IalmdReportFile.id)).filter(
        IalmdReportFile.status == 1, IalmdReportFile.is_deleted == 0,
    ).scalar() or 0
    # 如果无报告记录，使用报告链接表兜底
    link_file_count = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.status == 1, IalmdBankReportLink.is_deleted == 0,
    ).scalar() or 0
    if report_file_count == 0:
        report_file_count = link_file_count

    # ─── 指标值 & 本体统计 ───
    value_count = db.query(func.count(IalmdIndicatorValue.id)).filter(
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).scalar() or 0

    ontology_class_count = db.query(func.count(IalmdOntologyClass.id)).filter(
        IalmdOntologyClass.is_deleted == 0,
    ).scalar() or 0

    ontology_relation_count = db.query(func.count(IalmdOntologyRelation.id)).filter(
        IalmdOntologyRelation.is_deleted == 0,
    ).scalar() or 0

    mapping_count = db.query(func.count(IalmdIndicatorMapping.id)).filter(
        IalmdIndicatorMapping.is_deleted == 0,
    ).scalar() or 0

    # ─── 对话统计 ───
    session_count = db.query(func.count(IalmdChatSession.id)).filter(
        IalmdChatSession.is_deleted == 0,
    ).scalar() or 0

    message_count = db.query(func.count(IalmdChatMessage.id)).filter(
        IalmdChatMessage.is_deleted == 0,
    ).scalar() or 0

    # ─── 工作流统计 ───
    workflow_count = db.query(func.count(IalmdWorkflowDef.id)).filter(
        IalmdWorkflowDef.status == 1, IalmdWorkflowDef.is_deleted == 0,
    ).scalar() or 0

    exec_total = db.query(func.count(IalmdWorkflowExec.id)).filter(
        IalmdWorkflowExec.is_deleted == 0,
    ).scalar() or 0
    exec_success = db.query(func.count(IalmdWorkflowExec.id)).filter(
        IalmdWorkflowExec.is_deleted == 0, IalmdWorkflowExec.exec_status == "COMPLETED",
    ).scalar() or 0

    # ─── 抽取准确率 (有 verified_at 的值 / 总 APPROVED 值) ───
    approved_count = db.query(func.count(IalmdIndicatorValue.id)).filter(
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).scalar() or 0
    verified_count = db.query(func.count(IalmdIndicatorValue.id)).filter(
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.verified_by.isnot(None),
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).scalar() or 0
    accuracy_rate = round((verified_count / approved_count * 100), 1) if approved_count > 0 else 0.0

    # ─── 机构类型分布 ───
    bank_type_dist = []
    type_rows = db.query(
        IalmdBankInstitution.bank_type,
        func.count(IalmdBankInstitution.id),
    ).filter(
        IalmdBankInstitution.status == 1, IalmdBankInstitution.is_deleted == 0,
    ).group_by(IalmdBankInstitution.bank_type).all()
    type_label = {
        "GROUP": "保险集团", "POLICY": "政策性保险公司", "PNC": "财险公司",
        "REINSURANCE": "再保险公司", "LIFE": "寿险公司",
        "HEALTH": "健康险公司", "PENSION": "养老保险公司",
    }
    for bt, cnt in type_rows:
        bank_type_dist.append({"type": bt, "label": type_label.get(bt, bt), "count": cnt})

    # ─── 报告类型分布（优先 report_record，空则用 bank_report_link） ───
    report_type_dist = []
    rpt_rows = db.query(
        IalmdReportRecord.report_type, func.count(IalmdReportRecord.id),
    ).filter(
        IalmdReportRecord.status == 1, IalmdReportRecord.is_deleted == 0,
    ).group_by(IalmdReportRecord.report_type).all()
    if not rpt_rows:
        rpt_rows = db.query(
            IalmdBankReportLink.report_type, func.count(IalmdBankReportLink.id),
        ).filter(
            IalmdBankReportLink.status == 1, IalmdBankReportLink.is_deleted == 0,
        ).group_by(IalmdBankReportLink.report_type).all()
    rpt_label = {
        "ANNUAL": "年报", "HALF": "半年报", "Q1": "一季报", "Q3": "三季报",
        "EXPRESS": "业绩快报", "CAPITAL": "资本充足率", "LIQUIDITY": "流动性",
        "ESG": "ESG", "INCLUSIVE": "普惠金融", "CONSUMER": "消保", "GREEN": "绿色金融",
    }
    for rt, cnt in rpt_rows:
        report_type_dist.append({"type": rt, "label": rpt_label.get(rt, rt), "count": cnt})

    # ─── 指标分类分布 ───
    indicator_cat_dist = []
    cat_rows = db.query(
        IalmdIndicatorDefine.category_code,
        func.count(IalmdIndicatorDefine.id),
    ).filter(
        IalmdIndicatorDefine.status == 1, IalmdIndicatorDefine.is_deleted == 0,
    ).group_by(IalmdIndicatorDefine.category_code).all()
    cat_label = {
        "SCALE": "规模类", "PROFIT": "盈利类", "RISK": "风险类",
        "CAPITAL": "资本类", "LIQUIDITY": "流动性", "ESG": "ESG",
    }
    for cc, cnt in cat_rows:
        indicator_cat_dist.append({"code": cc, "label": cat_label.get(cc, cc), "count": cnt})

    # ─── 净息差(NIM)年度趋势（直接从指标值表取，无需 JOIN） ───
    nim_trend = []
    for year in range(2023, 2027):
        vals = db.query(func.avg(IalmdIndicatorValue.value_numeric)).filter(
            IalmdIndicatorValue.indicator_code == "PROFITABILITY_NIM",
            IalmdIndicatorValue.report_year == year, IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
        ).scalar()
        if vals:
            nim_trend.append({"period": str(year), "value": round(float(vals) * 100, 2)})

    # ─── 不良率(NPL)排行（2025 FY，按值升序 = 最优排第一） ───
    npl_ranking = []
    npl_rows = db.query(
        IalmdIndicatorValue.institution_id, func.avg(IalmdIndicatorValue.value_numeric).label('avg_val'),
    ).filter(
        IalmdIndicatorValue.indicator_code == "ASSET_QUALITY_NPL",
        IalmdIndicatorValue.report_year == 2025, IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).group_by(IalmdIndicatorValue.institution_id).order_by(func.avg(IalmdIndicatorValue.value_numeric).asc()).limit(10).all()

    for idx, (inst_id, val) in enumerate(npl_rows):
        bank = db.query(IalmdBankInstitution).filter(IalmdBankInstitution.id == inst_id).first()
        if bank:
            npl_ranking.append({
                "bank_name": bank.short_name or bank.bank_name,
                "bank_code": bank.bank_code, "value": round(float(val) * 100, 2), "rank": idx + 1,
            })

    # ─── ROE 趋势 ───
    roe_trend = []
    for year in range(2023, 2027):
        vals = db.query(func.avg(IalmdIndicatorValue.value_numeric)).filter(
            IalmdIndicatorValue.indicator_code == "PROFITABILITY_ROE",
            IalmdIndicatorValue.report_year == year, IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
        ).scalar()
        if vals:
            roe_trend.append({"period": str(year), "value": round(float(vals), 2)})

    # ─── 最近采集报告（优先 report_record，空则用 bank_report_link） ───
    recent_reports = []
    reports = db.query(IalmdReportRecord).filter(
        IalmdReportRecord.status == 1, IalmdReportRecord.is_deleted == 0,
    ).order_by(IalmdReportRecord.created_at.desc()).limit(10).all()
    for r in reports:
        bank = db.query(IalmdBankInstitution).filter(IalmdBankInstitution.id == r.institution_id).first()
        recent_reports.append({
            "id": r.id, "bank_name": bank.short_name if bank else "未知",
            "report_type": r.report_type, "report_year": r.report_year,
            "collect_status": r.collect_status,
            "publish_date": str(r.publish_date) if r.publish_date else None,
        })
    # 兜底：使用报告链接表
    if not recent_reports:
        links = db.query(IalmdBankReportLink).filter(
            IalmdBankReportLink.status == 1, IalmdBankReportLink.is_deleted == 0,
        ).order_by(IalmdBankReportLink.report_year.desc()).limit(10).all()
        for link in links:
            bank = db.query(IalmdBankInstitution).filter(
                IalmdBankInstitution.bank_code == link.bank_code
            ).first()
            recent_reports.append({
                "id": link.id,
                "bank_name": bank.short_name if bank else link.bank_code,
                "report_type": link.report_type,
                "report_year": link.report_year,
                "collect_status": "PARSED" if link.extraction_status == "DONE" else link.extraction_status,
                "publish_date": str(link.scan_time) if link.scan_time else None,
            })

    # ─── 最新指标数据时间 ───
    last_value = db.query(func.max(IalmdIndicatorValue.updated_at)).filter(
        IalmdIndicatorValue.status == 1, IalmdIndicatorValue.is_deleted == 0,
    ).scalar()

    dashboard_data = {
        "kpi": {
            "bank_count": bank_count,
            "indicator_count": indicator_count,
            "report_count": report_count,
            "report_file_count": report_file_count,
            "value_count": value_count,
            "ontology_class_count": ontology_class_count,
            "ontology_relation_count": ontology_relation_count,
            "mapping_count": mapping_count,
            "session_count": session_count,
            "message_count": message_count,
            "workflow_count": workflow_count,
            "exec_success_rate": round(exec_success / exec_total * 100, 1) if exec_total > 0 else 0,
            "accuracy_rate": accuracy_rate,
        },
        "bank_type_dist": bank_type_dist,
        "report_type_dist": report_type_dist,
        "indicator_cat_dist": indicator_cat_dist,
        "nim_trend": nim_trend,
        "roe_trend": roe_trend,
        "npl_ranking": npl_ranking,
        "recent_reports": recent_reports,
        "last_value_time": last_value.isoformat() if last_value else None,
    }

    # 2. 写入 Redis 缓存
    try:
        redis_client.setex(DASHBOARD_CACHE_KEY, DASHBOARD_CACHE_TTL, json.dumps(dashboard_data, ensure_ascii=False, default=str))
        logger.info("Dashboard: Redis cache updated")
    except Exception as e:
        logger.warning(f"Redis 写入缓存失败: {e}")

    return ResponseBase(data=dashboard_data)
