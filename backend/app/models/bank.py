"""保险机构 ORM 模型 — 完整版（含本体关联字段）"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdBankInstitution(Base):
    __tablename__ = "ialmd_bank_institution"
    __table_args__ = (
        UniqueConstraint("bank_name", name="uk_bank_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bank_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="保险机构全称")
    short_name: Mapped[str] = mapped_column(String(64), default="", comment="保险机构简称")
    bank_code: Mapped[str] = mapped_column(String(32), default="", comment="机构代码(如ICBC)")
    bank_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="机构类型")
    stock_code: Mapped[str] = mapped_column(String(16), default="", comment="股票代码")
    listing_market: Mapped[str] = mapped_column(String(16), default="", comment="上市地")
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="成立年份")
    headquarter: Mapped[str] = mapped_column(String(64), default="", comment="总部所在城市")
    region: Mapped[str] = mapped_column(String(32), default="", comment="区域")
    assets_scale_level: Mapped[str] = mapped_column(String(16), default="", comment="资产规模分级")
    ontology_class_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="关联本体概念ID")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="机构简介")
    total_assets: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True, comment="最新总资产(亿元)")
    website: Mapped[str] = mapped_column(String(256), default="", comment="官网URL")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)