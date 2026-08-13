"""保险业务 Pydantic Schema"""
from pydantic import BaseModel
from datetime import datetime
from .common import TimestampMixin


class BankInstitutionOut(TimestampMixin):
    id: int
    bank_name: str
    short_name: str
    bank_code: str
    bank_type: str
    stock_code: str
    listing_market: str
    total_assets: float | None
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


class IndicatorDefineOut(TimestampMixin):
    id: int
    indicator_code: str
    indicator_name: str
    indicator_alias: str
    category_code: str
    unit: str
    decimal_places: int
    calc_formula: str
    sort_order: int

    class Config:
        from_attributes = True


class IndicatorValueOut(TimestampMixin):
    """指标值基础响应"""
    id: int
    indicator_code: str
    bank_code: str
    indicator_id: int | None
    institution_id: int | None
    report_id: int | None
    value_numeric: float | None
    value_text: str
    report_year: int
    report_period: str
    confidence: float
    extract_page: int | None
    extract_context: str | None
    verify_status: str
    verified_by: int | None
    verified_at: datetime | None

    class Config:
        from_attributes = True


class IndicatorValueCreate(BaseModel):
    """创建指标值请求"""
    indicator_code: str
    bank_code: str
    value_numeric: float | None = None
    value_text: str = ""
    report_year: int
    report_period: str = "FY"
    extract_page: int | None = None
    extract_context: str | None = None


class IndicatorValueUpdate(BaseModel):
    """更新指标值请求"""
    value_numeric: float | None = None
    value_text: str | None = None
    report_year: int | None = None
    report_period: str | None = None


class IndicatorValueVerify(BaseModel):
    """审核指标值请求"""
    verify_status: str  # APPROVED / REJECTED


class DashboardKpi(BaseModel):
    """首页 KPI 卡片"""
    bank_count: int = 0
    indicator_count: int = 0
    report_count: int = 0
    benchmark_count: int = 0
    accuracy_rate: float = 0.0


class DashboardTrendItem(BaseModel):
    """首页趋势数据点"""
    period: str
    value: float


class DashboardRankItem(BaseModel):
    """首页排行数据"""
    bank_name: str
    bank_code: str
    value: float
    rank: int


class DashboardOut(BaseModel):
    """首页仪表盘响应"""
    kpi: DashboardKpi
    nim_trend: list[DashboardTrendItem] = []
    npl_ranking: list[DashboardRankItem] = []
    recent_reports: list[dict] = []
