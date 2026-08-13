"""系统管理 ORM 模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class SysUser(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="登录名")
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False, comment="密码哈希")
    real_name: Mapped[str] = mapped_column(String(64), default="", comment="真实姓名")
    email: Mapped[str] = mapped_column(String(128), default="", comment="邮箱")
    phone: Mapped[str] = mapped_column(String(20), default="", comment="手机号")
    institution_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="所属保险机构ID")
    avatar_url: Mapped[str] = mapped_column(String(256), default="", comment="头像URL")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后登录时间")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态: 0=禁用,1=正常")
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, comment="逻辑删除")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建人ID")
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新人ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    roles: Mapped[list["SysRole"]] = relationship(
        secondary="sys_user_role",
        primaryjoin="SysUser.id == SysUserRole.user_id",
        secondaryjoin="SysRole.id == SysUserRole.role_id",
        back_populates="users",
        lazy="selectin",
        viewonly=True,
    )


class SysRole(Base):
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色编码")
    description: Mapped[str] = mapped_column(String(256), default="", comment="角色描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态")
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, comment="逻辑删除")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    users: Mapped[list["SysUser"]] = relationship(
        secondary="sys_user_role",
        primaryjoin="SysRole.id == SysUserRole.role_id",
        secondaryjoin="SysUser.id == SysUserRole.user_id",
        back_populates="roles",
        lazy="selectin",
        viewonly=True,
    )


class SysUserRole(Base):
    __tablename__ = "sys_user_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uk_user_role"),
    )


class SysPermission(Base):
    __tablename__ = "sys_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(String(128), nullable=False, comment="权限编码")
    permission_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="权限名称")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父权限ID")
    permission_type: Mapped[str] = mapped_column(String(16), default="MENU", comment="权限类型")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_permission.id"), nullable=False, comment="权限ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uk_role_permission"),
    )


class SysLlmConfig(Base):
    """LLM 配置表 — 管理各 AI 服务商的 API Key 和参数"""
    __tablename__ = "sys_llm_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="服务商名称")
    provider_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="服务商编码: deepseek/qwen/openai/mock")
    api_key: Mapped[str] = mapped_column(String(512), default="", comment="API密钥")
    base_url: Mapped[str] = mapped_column(String(256), default="", comment="API地址")
    model_name: Mapped[str] = mapped_column(String(128), default="", comment="模型名称")
    temperature: Mapped[float] = mapped_column(default=0.10, comment="温度参数")
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, comment="最大Token数")
    is_enabled: Mapped[int] = mapped_column(Integer, default=0, comment="是否启用: 0=禁用,1=启用")
    is_default: Mapped[int] = mapped_column(Integer, default=0, comment="是否默认: 0=否,1=是")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    remark: Mapped[str] = mapped_column(String(256), default="", comment="备注")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class SysAuditLog(Base):
    __tablename__ = "sys_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="操作人ID")
    username: Mapped[str] = mapped_column(String(64), default="", comment="操作人登录名")
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作类型")
    target_type: Mapped[str] = mapped_column(String(32), default="", comment="目标类型")
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="目标ID")
    target_name: Mapped[str] = mapped_column(String(256), default="", comment="目标名称")
    detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="操作详情JSON")
    ip_address: Mapped[str] = mapped_column(String(45), default="", comment="客户端IP")
    user_agent: Mapped[str] = mapped_column(String(512), default="", comment="User-Agent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ==================== 系统字典 ====================

class SysDictType(Base):
    """字典类型表"""
    __tablename__ = "sys_dict_type"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典名称")
    dict_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="字典编码(唯一)")
    description: Mapped[str] = mapped_column(String(256), default="", comment="字典描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态: 0=禁用,1=正常")
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, comment="逻辑删除")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字典数据
    datas: Mapped[list["SysDictData"]] = relationship(
        back_populates="dict_type",
        lazy="selectin",
    )


class SysDictData(Base):
    """字典数据表"""
    __tablename__ = "sys_dict_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_type_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_dict_type.id"), nullable=False, comment="字典类型ID")
    dict_label: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典标签(显示值)")
    dict_value: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典键值(存储值)")
    dict_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典键名(CODE)")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态: 0=禁用,1=正常")
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, comment="逻辑删除")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字典类型
    dict_type: Mapped["SysDictType"] = relationship(back_populates="datas")

    __table_args__ = (
        UniqueConstraint("dict_type_id", "dict_key", name="uk_dict_type_key"),
    )
