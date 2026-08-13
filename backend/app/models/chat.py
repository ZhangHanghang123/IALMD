"""智能对话 ORM 模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class IalmdChatSession(Base):
    __tablename__ = "ialmd_chat_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户ID")
    session_title: Mapped[str] = mapped_column(String(256), default="新对话", comment="会话标题")
    session_type: Mapped[str] = mapped_column(String(32), default="ANALYSIS", comment="会话类型")
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="对话上下文JSON")
    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息数量")
    is_archived: Mapped[int] = mapped_column(Integer, default=0, comment="是否归档")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class IalmdChatMessage(Base):
    __tablename__ = "ialmd_chat_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="会话ID")
    role: Mapped[str] = mapped_column(String(16), nullable=False, comment="角色: USER/ASSISTANT/SYSTEM")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    message_type: Mapped[str] = mapped_column(String(32), default="TEXT", comment="消息类型")
    chart_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="ECharts图表配置JSON")
    table_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="表格数据JSON")
    trace_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="溯源数据JSON")
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, comment="消耗Token数")
    model_name: Mapped[str] = mapped_column(String(64), default="", comment="模型名称")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
