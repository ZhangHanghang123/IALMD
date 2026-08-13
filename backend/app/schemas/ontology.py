"""本体管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ============== 本体概念 (Class / Instance) ==============

class OntologyClassBase(BaseModel):
    class_code: str = Field(..., max_length=64)
    class_name: str = Field(..., max_length=128)
    class_name_en: str = ""
    aliases_json: Optional[List[str]] = None
    parent_id: int = 0
    class_level: int = 1
    description: Optional[str] = None
    unit: str = ""
    decimal_places: int = 2
    calc_formula: str = ""
    regulator_formula: str = ""
    data_frequency: str = "QUARTERLY"
    tags_json: Optional[List[str]] = None
    sort_order: int = 0
    entity_type: str = "CLASS"  # CLASS / INSTANCE
    instance_of_id: Optional[int] = None
    bank_code: str = ""
    publish_status: str = "PUBLISHED"
    ext_props_json: Optional[dict] = None
    indicator_id: Optional[int] = None


class OntologyClassCreate(OntologyClassBase):
    pass


class OntologyClassUpdate(BaseModel):
    class_name: Optional[str] = None
    class_name_en: Optional[str] = None
    aliases_json: Optional[List[str]] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    calc_formula: Optional[str] = None
    regulator_formula: Optional[str] = None
    tags_json: Optional[List[str]] = None
    sort_order: Optional[int] = None
    publish_status: Optional[str] = None
    ext_props_json: Optional[dict] = None


class OntologyClassVO(BaseModel):
    id: int
    class_code: str
    class_name: str
    class_name_en: str
    aliases_json: Optional[List[str]] = None
    parent_id: int
    class_level: int
    description: Optional[str] = None
    unit: str
    decimal_places: int
    calc_formula: str
    regulator_formula: str
    data_frequency: str
    tags_json: Optional[List[str]] = None
    sort_order: int
    entity_type: str
    instance_of_id: Optional[int] = None
    bank_code: str
    publish_status: str
    ext_props_json: Optional[dict] = None
    indicator_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 本体关系 ==============

class OntologyRelationCreate(BaseModel):
    source_class_id: int
    target_class_id: int
    relation_type: str
    description: str = ""
    weight: float = 1.0
    confidence: float = 1.0
    is_instance: int = 0
    instance_source_id: Optional[int] = None
    instance_target_id: Optional[int] = None


class OntologyRelationVO(BaseModel):
    id: int
    source_class_id: int
    target_class_id: int
    relation_type: str
    description: str
    weight: float
    confidence: float
    verify_status: str
    is_instance: int
    instance_source_id: Optional[int] = None
    instance_target_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 异构映射 ==============

class IndicatorMappingCreate(BaseModel):
    institution_id: int
    local_name: str
    ontology_class_id: int
    mapping_rule: str = "EXACT"
    effective_year: Optional[int] = None
    expire_year: Optional[int] = None
    source_context: Optional[str] = None
    llm_model: str = ""
    mapping_reason: Optional[str] = None
    confidence: float = 1.0


class IndicatorMappingVO(BaseModel):
    id: int
    institution_id: int
    local_name: str
    ontology_class_id: int
    mapping_rule: str
    effective_year: Optional[int] = None
    expire_year: Optional[int] = None
    source_context: Optional[str] = None
    llm_model: str
    confidence: float
    verify_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 银行报告 ==============

class BankReportLinkVO(BaseModel):
    id: int
    institution_id: int
    bank_code: str
    report_type: str
    report_year: int
    report_period: str
    file_format: str
    file_name: str
    file_path: str
    file_size: int
    page_count: int
    extraction_status: str
    extracted_count: int
    last_extracted_at: Optional[datetime] = None
    scan_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 映射候选 (LLM 推断缓冲) ==============

class MappingCandidateVO(BaseModel):
    id: int
    institution_id: int
    local_name: str
    raw_context: Optional[str] = None
    source_file: str
    source_page: Optional[int] = None
    candidate_class_id: Optional[int] = None
    confidence: float
    llm_model: str
    llm_reasoning: Optional[str] = None
    review_status: str
    review_remark: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 版本快照 ==============

class OntologyVersionVO(BaseModel):
    id: int
    version_code: str
    version_desc: str
    publish_status: str
    is_current: int
    class_count: int
    relation_count: int
    mapping_count: int
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 关系类型 / 标签 ==============

class RelationTypeVO(BaseModel):
    id: int
    type_code: str
    type_name: str
    type_desc: str
    color_hex: str
    line_style: str
    sort_order: int

    class Config:
        from_attributes = True


class TagVO(BaseModel):
    id: int
    tag_code: str
    tag_name: str
    tag_color: str
    tag_category: str
    description: str
    sort_order: int

    class Config:
        from_attributes = True


# ============== 审计日志 ==============

class AuditLogVO(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    before_json: Optional[dict] = None
    after_json: Optional[dict] = None
    version_id: Optional[int] = None
    operator_name: str
    remark: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== 银行本体 ==============

class BankOntologyVO(BaseModel):
    """银行本体实例视图"""
    id: int  # institution_id (bank's own primary key)
    bank_code: str = ""
    bank_name: str = ""
    short_name: str = ""
    bank_type: str = ""
    stock_code: str = ""
    listing_market: str = ""
    founded_year: Optional[int] = None
    headquarter: str = ""
    region: str = ""
    assets_scale_level: str = ""
    ontology_class_id: Optional[int] = None
    description: Optional[str] = None
    total_assets: Optional[float] = None
    # 关联统计
    indicator_count: int = 0
    report_count: int = 0
    mapping_count: int = 0

    class Config:
        from_attributes = True