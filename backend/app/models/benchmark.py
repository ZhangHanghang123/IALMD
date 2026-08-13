"""同业对标 ORM 模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdBenchmarkCompare(Base):
    __tablename__ = "ialmd_benchmark_compare"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="指标定义ID")
    compare_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="对比类型")
    institution_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="对比机构ID列表JSON")
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False, comment="对比结果JSON")
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, comment="数据年份")
    report_period: Mapped[str] = mapped_column(String(16), default="FY", comment="数据期间")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
