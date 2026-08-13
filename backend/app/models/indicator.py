"""经营指标 ORM 模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdIndicatorDefine(Base):
    __tablename__ = "ialmd_indicator_define"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="指标编码")
    indicator_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="指标名称")
    indicator_alias: Mapped[str] = mapped_column(String(256), default="", comment="别名")
    category_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="分类编码")
    unit: Mapped[str] = mapped_column(String(16), default="", comment="单位")
    decimal_places: Mapped[int] = mapped_column(Integer, default=2, comment="小数位数")
    calc_formula: Mapped[str] = mapped_column(String(512), default="", comment="计算公式")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdIndicatorValue(Base):
    __tablename__ = "ialmd_indicator_value"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 关联字段（使用编码关联，便于扩展）
    indicator_code: Mapped[str] = mapped_column(String(64), default="", comment="指标编码")
    bank_code: Mapped[str] = mapped_column(String(32), default="", comment="机构代码")
    # 保留ID关联（兼容旧数据）
    indicator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="指标定义ID(兼容)")
    institution_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="保险机构ID(兼容)")
    report_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="来源报告ID")
    value_numeric: Mapped[float | None] = mapped_column(Numeric(24, 6), nullable=True, comment="指标数值")
    value_text: Mapped[str] = mapped_column(String(128), default="", comment="指标文本值")
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, comment="数据年份")
    report_period: Mapped[str] = mapped_column(String(16), default="FY", comment="数据期间")
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, comment="抽取置信度")
    extract_page: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="来源页码")
    extract_context: Mapped[str | None] = mapped_column(Text, nullable=True, comment="抽取上下文")
    verify_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="审核状态")
    verified_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="审核人ID")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="审核时间")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
