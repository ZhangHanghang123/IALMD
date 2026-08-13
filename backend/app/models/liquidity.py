"""
流动性压力测试及风险缓释 — ORM 模型
表:
  - ialmd_g21_gap: G21流动性期限缺口数据
  - ialmd_hqla_asset: HQLA优质流动性资产
  - ialmd_stress_version: 压力测试版本（中枢）
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Integer, Text, DateTime, DECIMAL, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class IalmdG21Gap(Base):
    """G21流动性期限缺口数据"""
    __tablename__ = "ialmd_g21_gap"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_period: Mapped[str] = mapped_column(String(20), nullable=False, comment="报告期")
    item_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="科目编码")
    item_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="科目名称")
    category: Mapped[str] = mapped_column(String(32), nullable=False, comment="分类: ASSET/LIABILITY/OFF_BALANCE")
    overnight_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="隔夜金额")
    day7_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="7天金额")
    day14_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="14天金额")
    month1_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="1个月金额")
    month3_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="3个月金额")
    month6_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="6个月金额")
    year1_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="1年金额")
    year5_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="5年以上金额")
    unlimited_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="无期限金额")
    total_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="合计金额")

    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class IalmdHqlaAsset(Base):
    """HQLA优质流动性资产"""
    __tablename__ = "ialmd_hqla_asset"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_period: Mapped[str] = mapped_column(String(20), nullable=False, comment="报告期")
    asset_level: Mapped[str] = mapped_column(String(16), nullable=False, comment="LEVEL1/LEVEL2A/LEVEL2B")
    asset_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="资产名称")
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="资产类型")
    face_value: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="面值")
    market_value: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="市场价值")
    haircut_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 4), default=0, comment="扣减率")
    discounted_value: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="折后价值")
    hqla_value: Mapped[Optional[float]] = mapped_column(DECIMAL(24, 4), default=0, comment="计入HQLA金额")

    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class IalmdStressVersion(Base):
    """压力测试版本（中枢）"""
    __tablename__ = "ialmd_stress_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    version_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="版本编号")
    version_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="版本名称")
    version_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="版本描述")
    version_status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", comment="DRAFT/PUBLISHED/ARCHIVED")
    g21_period: Mapped[str] = mapped_column(String(20), nullable=False, comment="G21报告期引用")
    hqla_period: Mapped[str] = mapped_column(String(20), nullable=False, comment="HQLA快照期引用")
    scenario_type: Mapped[str] = mapped_column(String(32), nullable=False, default="MULTI", comment="保留字段，固定MULTI")
    test_window: Mapped[int] = mapped_column(Integer, default=30, comment="测试窗口(天)")
    scenario_params_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="情景参数JSON")
    benchmark_results_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="基准结果JSON")
    stress_results_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="压力测试结果JSON")
    cash_flow_gaps_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="现金流缺口JSON")
    mitigation_measures_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="缓释措施JSON")
    mitigation_results_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="缓释后结果JSON")

    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
