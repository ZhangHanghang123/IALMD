"""指标仪表盘 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
from ..database import get_db
from ..models import IalmdIndicatorDefine, IalmdIndicatorValue, IalmdBankInstitution
from ..schemas.common import ResponseBase
from ..schemas.indicator_dashboard import (
    IndicatorDashboardRequest,
    IndicatorDashboardOut,
    IndicatorDashboardKpi,
    IndicatorCategorySummary,
    IndicatorTrendData,
    IndicatorRankingItem,
    IndicatorComparisonData,
    IndicatorDistributionData,
    IndicatorTrendRequest,
    IndicatorRankingRequest,
    IndicatorComparisonRequest,
    IndicatorDistributionRequest,
    IndicatorDetailOut,
    BankIndicatorSnapshot,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/indicators-dashboard", tags=["指标仪表盘"])

# 指标分类名称映射
CATEGORY_NAMES = {
    "SCALE": "规模指标",
    "PROFIT": "盈利指标",
    "RISK": "风险指标",
    "CAPITAL": "资本指标",
    "LIQUIDITY": "流动性指标",
    "ESG": "ESG指标",
}


def get_current_year():
    """获取当前年份"""
    return datetime.now().year


@router.get("", response_model=ResponseBase)
def get_dashboard(
    year: int | None = Query(None, description="年份筛选，默认为当前年份"),
    bank_type: str | None = Query(None, description="机构类型筛选"),
    category_code: str | None = Query(None, description="指标分类编码"),
    indicator_code: str | None = Query(None, description="指标编码"),
    db: Session = Depends(get_db),
):
    """
    获取指标仪表盘概览数据

    返回KPI、各分类汇总、趋势数据、排名和分布情况
    """
    # 默认使用当前年份
    if year is None:
        year = get_current_year()

    # ========== 1. KPI统计 ==========
    total_indicators = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
    ).count()

    total_banks = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.status == 1,
        IalmdBankInstitution.is_deleted == 0,
    ).count()

    category_count = db.query(
        IalmdIndicatorDefine.category_code
    ).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
    ).distinct().count()

    # 计算数据完整度 - 已审核数据占比
    total_values = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).count()

    approved_values = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
        IalmdIndicatorValue.verify_status == "APPROVED",
    ).count()

    data_completeness = round((approved_values / total_values * 100), 2) if total_values > 0 else 0.0

    kpi = IndicatorDashboardKpi(
        total_indicators=total_indicators,
        total_banks=total_banks,
        category_count=category_count,
        data_completeness=data_completeness,
    )

    # ========== 2. 各分类汇总 ==========
    category_summaries = []

    # 如果指定了分类，则只查询该分类
    category_filter = [IalmdIndicatorDefine.category_code]
    if category_code:
        category_filter = [category_code]

    categories = db.query(
        IalmdIndicatorDefine.category_code,
        func.count(IalmdIndicatorDefine.id).label('indicator_count'),
    ).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
        IalmdIndicatorDefine.category_code.in_(category_filter),
    ).group_by(IalmdIndicatorDefine.category_code).all()

    for cat_code, ind_count in categories:
        # 计算该分类下的指标平均值
        cat_indicators = db.query(IalmdIndicatorDefine).filter(
            IalmdIndicatorDefine.category_code == cat_code,
            IalmdIndicatorDefine.status == 1,
        ).all()
        indicator_ids = [ind.id for ind in cat_indicators]

        if indicator_ids:
            avg_result = db.query(
                func.avg(IalmdIndicatorValue.value_numeric).label('avg_value'),
                func.max(IalmdIndicatorValue.value_numeric).label('max_value'),
                func.min(IalmdIndicatorValue.value_numeric).label('min_value'),
                func.count(IalmdIndicatorValue.id).label('value_count'),
            ).filter(
                IalmdIndicatorValue.indicator_id.in_(indicator_ids),
                IalmdIndicatorValue.report_year == year,
                IalmdIndicatorValue.report_period == "FY",
                IalmdIndicatorValue.verify_status == "APPROVED",
                IalmdIndicatorValue.status == 1,
            ).first()

            summary = IndicatorCategorySummary(
                category_code=cat_code,
                category_name=CATEGORY_NAMES.get(cat_code, cat_code),
                indicator_count=ind_count,
                avg_value=round(float(avg_result.avg_value), 2) if avg_result.avg_value else None,
                max_value=round(float(avg_result.max_value), 2) if avg_result.max_value else None,
                min_value=round(float(avg_result.min_value), 2) if avg_result.min_value else None,
                value_count=avg_result.value_count or 0,
            )
        else:
            summary = IndicatorCategorySummary(
                category_code=cat_code,
                category_name=CATEGORY_NAMES.get(cat_code, cat_code),
                indicator_count=ind_count,
                avg_value=None,
                max_value=None,
                min_value=None,
                value_count=0,
            )
        category_summaries.append(summary)

    # ========== 3. 指标趋势数据 ==========
    indicator_trends = []

    # 获取所有启用的指标
    indicators = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
    ).order_by(IalmdIndicatorDefine.sort_order).limit(10).all()

    for ind in indicators:
        # 获取近5年数据
        trend_data = []
        for y in range(year - 4, year + 1):
            result = db.query(
                func.avg(IalmdIndicatorValue.value_numeric).label('avg')
            ).filter(
                IalmdIndicatorValue.indicator_id == ind.id,
                IalmdIndicatorValue.report_year == y,
                IalmdIndicatorValue.report_period == "FY",
                IalmdIndicatorValue.verify_status == "APPROVED",
                IalmdIndicatorValue.status == 1,
            ).first()

            if result.avg:
                trend_data.append({
                    "year": y,
                    "value": round(float(result.avg), 2),
                })

        if trend_data:
            indicator_trends.append(IndicatorTrendData(
                indicator_code=ind.indicator_code,
                indicator_name=ind.indicator_name,
                unit=ind.unit or "",
                trend=trend_data,
            ))

    # ========== 4. 排名数据（标杆银行与待提升银行） ==========
    top_performers = []
    bottom_performers = []

    # 使用ROE作为默认排名指标
    ranking_indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == "ROE",
        IalmdIndicatorDefine.status == 1,
    ).first()

    if ranking_indicator:
        # 查询所有银行的ROE值
        rankings = db.query(
            IalmdIndicatorValue,
            IalmdBankInstitution.short_name,
            IalmdBankInstitution.bank_type,
        ).join(
            IalmdBankInstitution,
            IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
        ).filter(
            IalmdIndicatorValue.indicator_id == ranking_indicator.id,
            IalmdIndicatorValue.report_year == year,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.verify_status == "APPROVED",
            IalmdIndicatorValue.status == 1,
            IalmdIndicatorValue.is_deleted == 0,
        ).order_by(IalmdIndicatorValue.value_numeric.desc()).all()

        # 前5名（标杆银行）
        for i, row in enumerate(rankings[:5]):
            top_performers.append(IndicatorRankingItem(
                rank=i + 1,
                bank_code=row[2].bank_code if row[2] else "",
                bank_name=row[1] or "",
                bank_type=row[2].bank_type if row[2] else "",
                value=round(float(row[0].value_numeric), 2) if row[0].value_numeric else None,
                unit=ranking_indicator.unit or "%",
            ))

        # 后5名（待提升银行）
        for i, row in enumerate(rankings[-5:]):
            bottom_performers.append(IndicatorRankingItem(
                rank=len(rankings) - 4 + i,
                bank_code=row[2].bank_code if row[2] else "",
                bank_name=row[1] or "",
                bank_type=row[2].bank_type if row[2] else "",
                value=round(float(row[0].value_numeric), 2) if row[0].value_numeric else None,
                unit=ranking_indicator.unit or "%",
            ))

    # ========== 5. 分布数据 ==========
    distribution = []

    # 资产规模分布
    asset_indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == "TOTAL_ASSETS",
        IalmdIndicatorDefine.status == 1,
    ).first()

    if asset_indicator:
        assets = db.query(IalmdIndicatorValue.value_numeric).filter(
            IalmdIndicatorValue.indicator_id == asset_indicator.id,
            IalmdIndicatorValue.report_year == year,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.verify_status == "APPROVED",
            IalmdIndicatorValue.status == 1,
            IalmdIndicatorValue.value_numeric.isnot(None),
        ).all()

        if assets:
            values = [float(a[0]) for a in assets if a[0]]
            if values:
                # 分成5个区间
                min_val = min(values)
                max_val = max(values)
                step = (max_val - min_val) / 5

                ranges = [
                    (min_val, min_val + step, "小于万亿"),
                    (min_val + step, min_val + 2*step, "1-2万亿"),
                    (min_val + 2*step, min_val + 3*step, "2-3万亿"),
                    (min_val + 3*step, min_val + 4*step, "3-5万亿"),
                    (min_val + 4*step, max_val, "5万亿以上"),
                ]

                for low, high, label in ranges:
                    count = len([v for v in values if low <= v < high])
                    distribution.append(IndicatorDistributionData(
                        category="资产规模",
                        range_label=label,
                        count=count,
                        percentage=round(count / len(values) * 100, 1),
                    ))

    result = IndicatorDashboardOut(
        kpi=kpi,
        category_summaries=category_summaries,
        indicator_trends=indicator_trends,
        top_performers=top_performers,
        bottom_performers=bottom_performers,
        distribution=distribution,
        last_updated=datetime.now(),
    )

    return ResponseBase(data=result.model_dump())


@router.get("/trends", response_model=ResponseBase)
def get_indicator_trends(
    indicator_code: str = Query(..., description="指标编码"),
    years: int = Query(5, description="查询年份数量"),
    db: Session = Depends(get_db),
):
    """获取指定指标的趋势数据"""
    current_year = get_current_year()

    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    trend_data = []
    for y in range(current_year - years + 1, current_year + 1):
        result = db.query(
            func.avg(IalmdIndicatorValue.value_numeric).label('avg'),
            func.max(IalmdIndicatorValue.value_numeric).label('max'),
            func.min(IalmdIndicatorValue.value_numeric).label('min'),
            func.count(IalmdIndicatorValue.id).label('count'),
        ).filter(
            IalmdIndicatorValue.indicator_id == indicator.id,
            IalmdIndicatorValue.report_year == y,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.verify_status == "APPROVED",
            IalmdIndicatorValue.status == 1,
        ).first()

        if result:
            trend_data.append({
                "year": y,
                "avg": round(float(result.avg), 2) if result.avg else None,
                "max": round(float(result.max), 2) if result.max else None,
                "min": round(float(result.min), 2) if result.min else None,
                "count": result.count or 0,
            })

    return ResponseBase(data={
        "indicator_code": indicator_code,
        "indicator_name": indicator.indicator_name,
        "unit": indicator.unit or "",
        "trend": trend_data,
    })


@router.get("/rankings", response_model=ResponseBase)
def get_indicator_rankings(
    indicator_code: str = Query(..., description="指标编码"),
    year: int = Query(None, description="年份，默认当前年"),
    bank_type: str | None = Query(None, description="机构类型筛选"),
    top_n: int = Query(10, ge=1, le=50, description="返回前N名"),
    db: Session = Depends(get_db),
):
    """获取银行排名数据"""
    if year is None:
        year = get_current_year()

    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    query = db.query(
        IalmdIndicatorValue,
        IalmdBankInstitution.short_name,
        IalmdBankInstitution.bank_type,
    ).join(
        IalmdBankInstitution,
        IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == year,
        IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    )

    if bank_type:
        query = query.filter(IalmdBankInstitution.bank_type == bank_type)

    rankings = query.order_by(IalmdIndicatorValue.value_numeric.desc()).all()

    result = []
    for i, row in enumerate(rankings[:top_n]):
        result.append({
            "rank": i + 1,
            "bank_code": row[2].bank_code if row[2] else "",
            "bank_name": row[1] or "",
            "bank_type": row[2].bank_type if row[2] else "",
            "value": round(float(row[0].value_numeric), 2) if row[0].value_numeric else None,
            "unit": indicator.unit or "",
        })

    return ResponseBase(data={
        "indicator_code": indicator_code,
        "indicator_name": indicator.indicator_name,
        "year": year,
        "rankings": result,
    })


@router.get("/comparison", response_model=ResponseBase)
def compare_indicators(
    indicator_codes: str = Query(..., description="指标编码列表，逗号分隔"),
    year: int = Query(None, description="年份，默认当前年"),
    db: Session = Depends(get_db),
):
    """对比多个指标的统计数据"""
    if year is None:
        year = get_current_year()

    codes = [c.strip() for c in indicator_codes.split(",") if c.strip()]

    result = []
    for code in codes:
        indicator = db.query(IalmdIndicatorDefine).filter(
            IalmdIndicatorDefine.indicator_code == code,
            IalmdIndicatorDefine.status == 1,
        ).first()

        if not indicator:
            continue

        stats = db.query(
            func.avg(IalmdIndicatorValue.value_numeric).label('avg'),
            func.max(IalmdIndicatorValue.value_numeric).label('max'),
            func.min(IalmdIndicatorValue.value_numeric).label('min'),
            func.count(IalmdIndicatorValue.id).label('count'),
        ).filter(
            IalmdIndicatorValue.indicator_id == indicator.id,
            IalmdIndicatorValue.report_year == year,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.verify_status == "APPROVED",
            IalmdIndicatorValue.status == 1,
        ).first()

        result.append(IndicatorComparisonData(
            indicator_code=code,
            indicator_name=indicator.indicator_name,
            unit=indicator.unit or "",
            avg=round(float(stats.avg), 2) if stats.avg else None,
            max=round(float(stats.max), 2) if stats.max else None,
            min=round(float(stats.min), 2) if stats.min else None,
            count=stats.count or 0,
        ))

    return ResponseBase(data=result)


@router.get("/distribution", response_model=ResponseBase)
def get_indicator_distribution(
    indicator_code: str = Query(..., description="指标编码"),
    year: int = Query(None, description="年份，默认当前年"),
    buckets: int = Query(5, ge=3, le=10, description="分组数量"),
    db: Session = Depends(get_db),
):
    """获取指标分布数据（直方图）"""
    if year is None:
        year = get_current_year()

    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    values = db.query(IalmdIndicatorValue.value_numeric).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == year,
        IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.value_numeric.isnot(None),
    ).all()

    if not values:
        return ResponseBase(data=[])

    numeric_values = [float(v[0]) for v in values if v[0]]
    if not numeric_values:
        return ResponseBase(data=[])

    min_val = min(numeric_values)
    max_val = max(numeric_values)
    step = (max_val - min_val) / buckets

    distribution = []
    for i in range(buckets):
        low = min_val + i * step
        high = min_val + (i + 1) * step
        if i == buckets - 1:
            high = max_val  # 包含最大值

        count = len([v for v in numeric_values if low <= v < high])
        distribution.append(IndicatorDistributionData(
            category=indicator.indicator_name,
            range_label=f"{round(low, 2)}-{round(high, 2)}",
            count=count,
            percentage=round(count / len(numeric_values) * 100, 1),
        ))

    return ResponseBase(data=distribution)


@router.get("/detail/{indicator_code}", response_model=ResponseBase)
def get_indicator_detail(
    indicator_code: str,
    year: int | None = Query(None, description="年份"),
    db: Session = Depends(get_db),
):
    """获取指标详情页面数据"""
    if year is None:
        year = get_current_year()

    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    # 基本信息
    detail = {
        "indicator_code": indicator.indicator_code,
        "indicator_name": indicator.indicator_name,
        "category_code": indicator.category_code,
        "category_name": CATEGORY_NAMES.get(indicator.category_code, indicator.category_code),
        "unit": indicator.unit or "",
        "description": indicator.description or "",
    }

    # 统计汇总
    stats = db.query(
        func.avg(IalmdIndicatorValue.value_numeric).label('avg'),
        func.max(IalmdIndicatorValue.value_numeric).label('max'),
        func.min(IalmdIndicatorValue.value_numeric).label('min'),
        func.count(IalmdIndicatorValue.id).label('count'),
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == year,
        IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
    ).first()

    detail["statistics"] = {
        "avg": round(float(stats.avg), 2) if stats.avg else None,
        "max": round(float(stats.max), 2) if stats.max else None,
        "min": round(float(stats.min), 2) if stats.min else None,
        "median": None,  # 需要单独计算
        "count": stats.count or 0,
    }

    # 各银行快照
    snapshots = db.query(
        IalmdIndicatorValue,
        IalmdBankInstitution.short_name,
        IalmdBankInstitution.bank_type,
    ).join(
        IalmdBankInstitution,
        IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == year,
        IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).order_by(IalmdIndicatorValue.value_numeric.desc()).all()

    detail["bank_snapshots"] = [
        BankIndicatorSnapshot(
            bank_code=row[2].bank_code if row[2] else "",
            bank_name=row[1] or "",
            bank_type=row[2].bank_type if row[2] else "",
            value=round(float(row[0].value_numeric), 2) if row[0].value_numeric else None,
            unit=indicator.unit or "",
            report_year=year,
            report_period="FY",
        )
        for row in snapshots
    ]

    # 历史趋势（近5年）
    trend = []
    for y in range(year - 4, year + 1):
        year_stats = db.query(
            func.avg(IalmdIndicatorValue.value_numeric).label('avg')
        ).filter(
            IalmdIndicatorValue.indicator_id == indicator.id,
            IalmdIndicatorValue.report_year == y,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.verify_status == "APPROVED",
            IalmdIndicatorValue.status == 1,
        ).first()

        if year_stats.avg:
            trend.append({
                "year": y,
                "value": round(float(year_stats.avg), 2),
            })

    detail["trend"] = trend

    return ResponseBase(data=detail)
