"""报告采集 ORM 模型"""
from datetime import datetime, date
from sqlalchemy import BigInteger, String, Integer, DateTime, Date, Text, Numeric
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdReportRecord(Base):
    __tablename__ = "ialmd_report_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="保险机构ID")
    report_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="报告类型")
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, comment="报告年度")
    report_period: Mapped[str] = mapped_column(String(16), default="FY", comment="报告期间")
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="发布日期")
    report_title: Mapped[str] = mapped_column(String(512), default="", comment="报告标题")
    collect_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="采集状态")
    page_count: Mapped[int] = mapped_column(Integer, default=0, comment="报告页数")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, comment="重试次数")
    source_url: Mapped[str] = mapped_column(String(1024), default="", comment="源文件URL")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="采集完成时间")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdReportFile(Base):
    __tablename__ = "ialmd_report_file"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="报告记录ID")
    file_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文件名")
    file_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="文件类型")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, comment="文件大小")
    file_hash: Mapped[str] = mapped_column(String(64), default="", comment="文件SHA256")
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="存储路径")
    download_url: Mapped[str] = mapped_column(String(1024), default="", comment="下载URL")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdCollectTask(Base):
    __tablename__ = "ialmd_collect_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="任务类型")
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="目标ID")
    celery_task_id: Mapped[str] = mapped_column(String(128), default="", comment="Celery任务ID")
    exec_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="执行状态")
    progress: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, comment="进度百分比")
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="执行结果JSON")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
