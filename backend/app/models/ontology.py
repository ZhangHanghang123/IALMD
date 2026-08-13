"""本体知识 ORM 模型 — 完整版（含类/实例/版本/标签/关系类型/审计/银行报告）"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, DateTime, Numeric, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


# ==========================================================
# 1. 本体概念表（类/实例统一管理）
# ==========================================================
class IalmdOntologyClass(Base):
    __tablename__ = "ialmd_ontology_class"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    class_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="本体类编码")
    class_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="本体类中文名")
    class_name_en: Mapped[str] = mapped_column(String(128), default="", comment="英文名")
    aliases_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="别名列表(JSON数组)")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, comment="父类ID")
    class_level: Mapped[int] = mapped_column(SmallInteger, default=1, comment="层级: 1=大类/2=指标/3=子指标")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(16), default="", comment="单位")
    decimal_places: Mapped[int] = mapped_column(SmallInteger, default=2, comment="小数位")
    calc_formula: Mapped[str] = mapped_column(String(512), default="", comment="计算公式")
    regulator_formula: Mapped[str] = mapped_column(String(512), default="", comment="监管口径公式")
    data_frequency: Mapped[str] = mapped_column(String(32), default="QUARTERLY", comment="数据频度")
    tags_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="标签列表")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    # 实例化（用于机构本体）
    entity_type: Mapped[str] = mapped_column(String(16), default="CLASS", comment="CLASS/INSTANCE")
    instance_of_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="所属类ID")
    bank_code: Mapped[str] = mapped_column(String(32), default="", comment="机构代码(机构实例用)")
    # 版本
    version_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="当前版本ID")
    publish_status: Mapped[str] = mapped_column(String(16), default="PUBLISHED", comment="DRAFT/PUBLISHED/DEPRECATED")
    ext_props_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="扩展属性")
    # 关联到指标定义
    indicator_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # 公共字段
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 2. 本体关系表（支持类间/实例间）
# ==========================================================
class IalmdOntologyRelation(Base):
    __tablename__ = "ialmd_ontology_relation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_class_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="源本体类ID")
    target_class_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="目标本体类ID")
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="PARENT_CHILD/SYNONYM/COMPUTED_FROM...")
    description: Mapped[str] = mapped_column(String(512), default="", comment="关系描述")
    created_version_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="创建版本ID")
    instance_source_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="实例源ID")
    instance_target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="实例目标ID")
    is_instance: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=类级, 1=实例级")
    weight: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, comment="权重")
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, comment="置信度")
    verify_status: Mapped[str] = mapped_column(String(16), default="PENDING", comment="PENDING/APPROVED/REJECTED")
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 3. 异构映射表
# ==========================================================
class IalmdIndicatorMapping(Base):
    __tablename__ = "ialmd_indicator_mapping"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="保险机构ID")
    local_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="本地指标名称")
    ontology_class_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="本体类ID")
    mapping_rule: Mapped[str] = mapped_column(String(32), default="EXACT", comment="EXACT/REGEX/LLM/MANUAL")
    effective_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="起效年度")
    expire_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="截止年度")
    source_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原文片段")
    llm_model: Mapped[str] = mapped_column(String(64), default="", comment="LLM模型")
    mapping_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="映射理由")
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, comment="置信度")
    verify_status: Mapped[str] = mapped_column(String(16), default="PENDING")
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 4. 本体版本快照表
# ==========================================================
class IalmdOntologyVersion(Base):
    __tablename__ = "ialmd_ontology_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    version_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, comment="版本号 V2.3.1")
    version_desc: Mapped[str] = mapped_column(String(512), default="")
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False, comment="全量本体快照JSON")
    diff_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    publish_status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    is_current: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否当前版本")
    published_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    class_count: Mapped[int] = mapped_column(Integer, default=0)
    relation_count: Mapped[int] = mapped_column(Integer, default=0)
    mapping_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 5. 映射候选表（LLM 推断缓冲）
# ==========================================================
class IalmdMappingCandidate(Base):
    __tablename__ = "ialmd_mapping_candidate"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    local_name: Mapped[str] = mapped_column(String(256), nullable=False)
    raw_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_file: Mapped[str] = mapped_column(String(512), default="")
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    candidate_class_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    alternative_class_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    llm_model: Mapped[str] = mapped_column(String(64), default="")
    llm_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(16), default="PENDING")
    reviewed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_remark: Mapped[str] = mapped_column(String(512), default="")
    final_mapping_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 6. 机构-报告关联表
# ==========================================================
class IalmdBankReportLink(Base):
    __tablename__ = "ialmd_bank_report_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bank_code: Mapped[str] = mapped_column(String(32), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False)
    report_period: Mapped[str] = mapped_column(String(16), default="FY")
    file_format: Mapped[str] = mapped_column(String(8), default="")
    file_name: Mapped[str] = mapped_column(String(256), default="")
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), default="")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    exists_flag: Mapped[int] = mapped_column(SmallInteger, default=1)
    extraction_status: Mapped[str] = mapped_column(String(16), default="PENDING")
    extracted_count: Mapped[int] = mapped_column(Integer, default=0)
    last_extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scan_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 7. 关系类型枚举表
# ==========================================================
class IalmdOntologyRelationType(Base):
    __tablename__ = "ialmd_ontology_relation_type"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    type_name: Mapped[str] = mapped_column(String(64), nullable=False)
    type_desc: Mapped[str] = mapped_column(String(256), default="")
    color_hex: Mapped[str] = mapped_column(String(8), default="#3b82f6")
    line_style: Mapped[str] = mapped_column(String(16), default="solid")
    source_types: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    target_types: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 8. 本体标签表
# ==========================================================
class IalmdOntologyTag(Base):
    __tablename__ = "ialmd_ontology_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tag_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    tag_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tag_color: Mapped[str] = mapped_column(String(8), default="#3b82f6")
    tag_category: Mapped[str] = mapped_column(String(32), default="CUSTOM")
    description: Mapped[str] = mapped_column(String(256), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==========================================================
# 9. 本体变更审计日志
# ==========================================================
class SysOntologyAuditLog(Base):
    __tablename__ = "sys_ontology_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    version_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    operator_name: Mapped[str] = mapped_column(String(64), default="")
    remark: Mapped[str] = mapped_column(String(512), default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)