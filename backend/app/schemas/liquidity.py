"""
流动性压力测试 — Pydantic Schema 定义
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ==================== G21 缺口数据 ====================

class G21GapBase(BaseModel):
    report_period: str = Field(..., description="报告期")
    item_code: str = Field(..., max_length=64, description="科目编码")
    item_name: str = Field(..., max_length=128, description="科目名称")
    category: str = Field(default="ASSET", description="ASSET/LIABILITY/OFF_BALANCE")
    overnight_amount: float = Field(default=0, description="隔夜")
    day7_amount: float = Field(default=0, description="7天")
    day14_amount: float = Field(default=0, description="14天")
    month1_amount: float = Field(default=0, description="1个月")
    month3_amount: float = Field(default=0, description="3个月")
    month6_amount: float = Field(default=0, description="6个月")
    year1_amount: float = Field(default=0, description="1年")
    year5_amount: float = Field(default=0, description="5年以上")
    unlimited_amount: float = Field(default=0, description="无期限")
    total_amount: float = Field(default=0, description="合计")


class G21GapCreate(G21GapBase):
    pass


class G21ImportItem(BaseModel):
    """导入用，不含report_period（由外层传入）"""
    item_code: str = Field(..., max_length=64)
    item_name: str = Field(..., max_length=128)
    category: str = Field(default="ASSET")
    overnight_amount: float = 0; day7_amount: float = 0; day14_amount: float = 0
    month1_amount: float = 0; month3_amount: float = 0; month6_amount: float = 0
    year1_amount: float = 0; year5_amount: float = 0; unlimited_amount: float = 0
    total_amount: float = 0


class G21GapUpdate(BaseModel):
    item_name: Optional[str] = None
    overnight_amount: Optional[float] = None
    day7_amount: Optional[float] = None
    day14_amount: Optional[float] = None
    month1_amount: Optional[float] = None
    month3_amount: Optional[float] = None
    month6_amount: Optional[float] = None
    year1_amount: Optional[float] = None
    year5_amount: Optional[float] = None
    unlimited_amount: Optional[float] = None
    total_amount: Optional[float] = None


class G21GapVO(G21GapBase):
    id: int
    status: int = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== HQLA 资产 ====================

class HqlaAssetBase(BaseModel):
    report_period: str = Field(..., description="报告期")
    asset_level: str = Field(..., description="LEVEL1/LEVEL2A/LEVEL2B")
    asset_name: str = Field(..., max_length=256, description="资产名称")
    asset_type: str = Field(..., max_length=64, description="资产类型")
    face_value: float = Field(default=0, description="面值")
    market_value: float = Field(default=0, description="市场价值")
    haircut_rate: float = Field(default=0, description="扣减率")
    discounted_value: float = Field(default=0, description="折后价值")
    hqla_value: float = Field(default=0, description="计入HQLA金额")


class HqlaAssetCreate(HqlaAssetBase):
    pass


class HqlaImportItem(BaseModel):
    """导入用，不含report_period（由外层传入）"""
    asset_level: str = Field(..., description="LEVEL1/LEVEL2A/LEVEL2B")
    asset_name: str = Field(..., max_length=256)
    asset_type: str = Field(..., max_length=64)
    face_value: float = 0; market_value: float = 0; haircut_rate: float = 0
    discounted_value: float = 0; hqla_value: float = 0


class HqlaAssetUpdate(BaseModel):
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    face_value: Optional[float] = None
    market_value: Optional[float] = None
    haircut_rate: Optional[float] = None
    discounted_value: Optional[float] = None
    hqla_value: Optional[float] = None


class HqlaAssetVO(HqlaAssetBase):
    id: int
    status: int = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 压力测试版本 ====================

SCENARIO_DEFAULTS = {
    "BASE": {"deposit_runoff_retail": 0, "deposit_runoff_corp": 0, "wholesale_rollover_rate": 1.0, "credit_drawdown_rate": 0.05, "bond_haircut": 0, "interbank_spread_bp": 0},
    "MILD": {"deposit_runoff_retail": 0.08, "deposit_runoff_corp": 0.15, "wholesale_rollover_rate": 0.80, "credit_drawdown_rate": 0.15, "bond_haircut": 0.05, "interbank_spread_bp": 50},
    "MODERATE": {"deposit_runoff_retail": 0.15, "deposit_runoff_corp": 0.25, "wholesale_rollover_rate": 0.50, "credit_drawdown_rate": 0.30, "bond_haircut": 0.15, "interbank_spread_bp": 100},
    "SEVERE": {"deposit_runoff_retail": 0.25, "deposit_runoff_corp": 0.40, "wholesale_rollover_rate": 0.0, "credit_drawdown_rate": 0.50, "bond_haircut": 0.30, "interbank_spread_bp": 200},
}

class StressVersionBase(BaseModel):
    version_code: str = Field(..., max_length=32, description="版本编号")
    version_name: str = Field(..., max_length=256, description="版本名称")
    version_desc: Optional[str] = Field(None, description="版本描述")
    version_status: str = Field(default="DRAFT", description="DRAFT/PUBLISHED/ARCHIVED")
    g21_period: str = Field(..., description="G21报告期引用")
    hqla_period: str = Field(..., description="HQLA快照期引用")
    test_window: int = Field(default=30, description="测试窗口")


class StressVersionCreate(StressVersionBase):
    scenario_params_json: Optional[dict] = Field(default_factory=lambda: dict(SCENARIO_DEFAULTS))


class ScenarioParamsUpdate(BaseModel):
    """更新单个情景的参数"""
    scenario_type: str = Field(..., description="BASE/MILD/MODERATE/SEVERE")
    params: dict = Field(..., description="情景参数")


class StressVersionUpdate(BaseModel):
    version_name: Optional[str] = None
    version_desc: Optional[str] = None
    version_status: Optional[str] = None
    test_window: Optional[int] = None
    scenario_params_json: Optional[dict] = None
    stress_results_json: Optional[dict] = None
    cash_flow_gaps_json: Optional[dict] = None
    mitigation_measures_json: Optional[dict] = None
    mitigation_results_json: Optional[dict] = None


class StressVersionVO(StressVersionBase):
    id: int
    scenario_params_json: Optional[dict] = None
    stress_results_json: Optional[dict] = None
    cash_flow_gaps_json: Optional[dict] = None
    mitigation_measures_json: Optional[dict] = None
    mitigation_results_json: Optional[dict] = None
    status: int = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 版本对比 ====================

class VersionCompareRequest(BaseModel):
    version_ids: list[int] = Field(..., description="对比的版本ID列表（2-4个）")


# ==================== Excel 导入 ====================

class G21ImportRequest(BaseModel):
    report_period: str = Field(..., description="报告期")
    items: list[G21ImportItem] = Field(..., description="导入的G21数据列表")


class HqlaImportRequest(BaseModel):
    report_period: str = Field(..., description="报告期")
    items: list[HqlaImportItem] = Field(..., description="导入的HQLA资产列表")
