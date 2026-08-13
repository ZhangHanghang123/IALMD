"""工作流 ORM 模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdWorkflowDef(Base):
    __tablename__ = "ialmd_workflow_def"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="工作流名称")
    workflow_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="工作流编码")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="说明")
    node_json: Mapped[dict] = mapped_column(JSON, nullable=False, comment="节点DAG图定义JSON")
    trigger_type: Mapped[str] = mapped_column(String(16), default="MANUAL", comment="触发方式")
    cron_expr: Mapped[str] = mapped_column(String(64), default="", comment="Cron表达式")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdWorkflowExec(Base):
    __tablename__ = "ialmd_workflow_exec"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="工作流定义ID")
    exec_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="执行状态")
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="输入参数JSON")
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="输出结果JSON")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    triggered_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="触发人ID")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdWorkflowNodeExec(Base):
    __tablename__ = "ialmd_workflow_node_exec"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exec_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="工作流执行ID")
    node_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="节点ID")
    node_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="节点类型")
    agent_type: Mapped[str] = mapped_column(String(32), default="", comment="Agent类型")
    exec_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="执行状态")
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="输入数据JSON")
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="输出数据JSON")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
