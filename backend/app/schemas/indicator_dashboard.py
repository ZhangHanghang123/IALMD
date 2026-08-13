"""
指标仪表盘 API  schemas
Bank Business Intelligence Analysis Platform
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class IndicatorDashboardRequest(BaseModel):
    """指标仪表盘请求"""
    year: Optional[int] = Field(None, description="年份筛选，默认为当前年份")
    bank_type: Optional[str] = Field(None, description="机构类型筛选: 国有大型商业银行/股份制商业银行/城市商业银行/农村商业银行/政策性银行")
    category_code: Optional[str] = Field(None, description="指标分类编码")
    indicator_code: Optional[str] = Field(None, description="指标编码")


class IndicatorCategorySummary(BaseModel):
    """指标分类汇总"""
    category_code: str = Field(..., description="指标分类编码")
    category_name: str = Field(..., description="指标分类名称")
    indicator_count: int = Field(0, description="指标数量")
    avg_value: Optional[float] = Field(None, description="行业平均值")
    max_value: Optional[float] = Field(None, description="行业最大值")
    min_value: Optional[float] = Field(None, description="行业最小值")
    median_value: Optional[float] = Field(None, description="行业中位数")
    bank_count: int = Field(0, description="参与统计的银行数量")


class IndicatorTrendData(BaseModel):
    """指标趋势数据"""
    year: int = Field(..., description="年份")
    avg_value: Optional[float] = Field(None, description="行业平均值")
    max_value: Optional[float] = Field(None, description="行业最大值")
    min_value: Optional[float] = Field(None, description="行业最小值")
    median_value: Optional[float] = Field(None, description="行业中位数")
    bank_count: int = Field(0, description="参与统计的银行数量")


class IndicatorRankingItem(BaseModel):
    """指标排名项"""
    bank_id: int = Field(..., description="银行ID")
    bank_name: str = Field(..., description="机构名称")
    bank_type: str = Field(..., description="机构类型")
    value: Optional[float] = Field(None, description="指标值")
    rank: int = Field(0, description="排名")
    change: Optional[int] = Field(None, description="排名变化（较上期）")


class IndicatorComparisonData(BaseModel):
    """指标对比数据"""
    indicator_code: str = Field(..., description="指标编码")
    indicator_name: str = Field(..., description="指标名称")
    unit: str = Field(..., description="单位")
    category_code: str = Field(..., description="分类编码")
    data: List[IndicatorRankingItem] = Field(default_factory=list, description="对比数据列表")


class IndicatorDistributionData(BaseModel):
    """指标分布数据（用于直方图）"""
    range_start: float = Field(..., description="区间起始值")
    range_end: float = Field(..., description="区间结束值")
    range_label: str = Field(..., description="区间标签")
    bank_count: int = Field(0, description="该区间的银行数量")
    percentage: float = Field(0.0, description="占比%")


class IndicatorDashboardKpi(BaseModel):
    """指标仪表盘KPI卡片"""
    total_indicators: int = Field(0, description="指标总数")
    total_banks: int = Field(0, description="银行数量")
    category_count: int = Field(0, description="分类数量")
    data_completeness: float = Field(0.0, description="数据完整度%")


class IndicatorDashboardOut(BaseModel):
    """指标仪表盘响应"""
    kpi: IndicatorDashboardKpi = Field(..., description="KPI概览")
    category_summaries: List[IndicatorCategorySummary] = Field(default_factory=list, description="各分类汇总")
    indicator_trends: List[IndicatorTrendData] = Field(default_factory=list, description="指标趋势")
    top_performers: List[IndicatorRankingItem] = Field(default_factory=list, description="标杆银行")
    bottom_performers: List[IndicatorRankingItem] = Field(default_factory=list, description="待提升银行")
    distribution: List[IndicatorDistributionData] = Field(default_factory=list, description="分布情况")
    last_updated: datetime = Field(default_factory=datetime.now, description="数据更新时间")


class IndicatorTrendRequest(BaseModel):
    """指标趋势请求"""
    indicator_code: str = Field(..., description="指标编码")
    bank_type: Optional[str] = Field(None, description="机构类型筛选")
    years: Optional[int] = Field(5, description="展示年数，默认5年")


class IndicatorRankingRequest(BaseModel):
    """指标排名请求"""
    indicator_code: str = Field(..., description="指标编码")
    year: Optional[int] = Field(None, description="年份")
    bank_type: Optional[str] = Field(None, description="机构类型筛选")
    top_n: Optional[int] = Field(20, description="显示前N名，默认20")


class IndicatorComparisonRequest(BaseModel):
    """多指标对比请求"""
    indicator_codes: List[str] = Field(..., description="指标编码列表")
    year: Optional[int] = Field(None, description="年份")
    bank_type: Optional[str] = Field(None, description="机构类型筛选")
    bank_ids: Optional[List[int]] = Field(None, description="指定机构ID列表")


class IndicatorDistributionRequest(BaseModel):
    """指标分布请求"""
    indicator_code: str = Field(..., description="指标编码")
    year: Optional[int] = Field(None, description="年份")
    bank_type: Optional[str] = Field(None, description="机构类型筛选")
    bucket_count: Optional[int] = Field(5, description="分组数量，默认5")


class BankIndicatorSnapshot(BaseModel):
    """银行指标快照（用于详情页）"""
    bank_id: int = Field(..., description="银行ID")
    bank_name: str = Field(..., description="机构名称")
    indicator_code: str = Field(..., description="指标编码")
    indicator_name: str = Field(..., description="指标名称")
    value: Optional[float] = Field(None, description="指标值")
    year: int = Field(..., description="年份")
    report_type: str = Field(..., description="报告类型")
    avg_value: Optional[float] = Field(None, description="行业平均值")
    median_value: Optional[float] = Field(None, description="行业中位数")
    rank: Optional[int] = Field(None, description="行业排名")
    percentile: Optional[float] = Field(None, description="百分位")


class IndicatorDetailOut(BaseModel):
    """指标详情响应"""
    indicator_code: str = Field(..., description="指标编码")
    indicator_name: str = Field(..., description="指标名称")
    category_code: str = Field(..., description="分类编码")
    category_name: str = Field(..., description="分类名称")
    unit: str = Field(..., description="单位")
    calc_formula: Optional[str] = Field(None, description="计算公式")
    description: Optional[str] = Field(None, description="指标说明")
    trend_data: List[IndicatorTrendData] = Field(default_factory=list, description="历史趋势")
    ranking_data: List[IndicatorRankingItem] = Field(default_factory=list, description="排名数据")
    distribution_data: List[IndicatorDistributionData] = Field(default_factory=list, description="分布数据")
    bank_snapshots: List[BankIndicatorSnapshot] = Field(default_factory=list, description="银行快照")
