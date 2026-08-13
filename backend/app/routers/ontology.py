"""本体管理 API 路由 — 类/实例/关系/映射/版本/银行报告"""
import os
import re
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from ..database import get_db
from ..models.ontology import (
    IalmdOntologyClass, IalmdOntologyRelation, IalmdIndicatorMapping,
    IalmdOntologyVersion, IalmdMappingCandidate, IalmdBankReportLink,
    IalmdOntologyRelationType, IalmdOntologyTag, SysOntologyAuditLog,
)
from ..models.bank import IalmdBankInstitution
from ..schemas.common import ResponseBase, PageResponse
from ..schemas.ontology import (
    OntologyClassCreate, OntologyClassUpdate, OntologyClassVO,
    OntologyRelationCreate, OntologyRelationVO,
    IndicatorMappingCreate, IndicatorMappingVO,
    BankReportLinkVO, MappingCandidateVO,
    OntologyVersionVO, RelationTypeVO, TagVO,
    AuditLogVO, BankOntologyVO,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/ontology", tags=["本体管理"])


# =============================================================
# 1. 本体概念 (Class + Instance)  CRUD
# =============================================================

@router.get("/classes", response_model=ResponseBase)
def list_classes(
    entity_type: Optional[str] = Query(None, description="CLASS/INSTANCE"),
    parent_id: Optional[int] = None,
    class_level: Optional[int] = None,
    publish_status: Optional[str] = None,
    bank_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取本体概念列表（支持类/实例筛选）"""
    q = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.status == 1,
        IalmdOntologyClass.is_deleted == 0,
    )
    if entity_type:
        q = q.filter(IalmdOntologyClass.entity_type == entity_type)
    if parent_id is not None:
        q = q.filter(IalmdOntologyClass.parent_id == parent_id)
    if class_level is not None:
        q = q.filter(IalmdOntologyClass.class_level == class_level)
    if publish_status:
        q = q.filter(IalmdOntologyClass.publish_status == publish_status)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            IalmdOntologyClass.class_name.like(like),
            IalmdOntologyClass.class_code.like(like),
            IalmdOntologyClass.class_name_en.like(like),
        ))
    items = q.order_by(IalmdOntologyClass.sort_order, IalmdOntologyClass.id).all()
    return ResponseBase(data=[OntologyClassVO.model_validate(i).model_dump() for i in items])


@router.get("/classes/tree", response_model=ResponseBase)
def get_class_tree(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取本体树（带层级结构）"""
    q = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.status == 1,
        IalmdOntologyClass.is_deleted == 0,
    )
    if entity_type:
        q = q.filter(IalmdOntologyClass.entity_type == entity_type)
    all_items = q.order_by(IalmdOntologyClass.sort_order).all()
    # 构建树
    nodes = {i.id: {
        "id": i.id, "class_code": i.class_code, "class_name": i.class_name,
        "class_name_en": i.class_name_en, "parent_id": i.parent_id,
        "class_level": i.class_level, "entity_type": i.entity_type,
        "bank_code": i.bank_code, "publish_status": i.publish_status,
        "children": [],
    } for i in all_items}
    tree = []
    for n in nodes.values():
        if n["parent_id"] and n["parent_id"] in nodes:
            nodes[n["parent_id"]]["children"].append(n)
        else:
            tree.append(n)
    return ResponseBase(data=tree)


@router.get("/classes/{class_id}", response_model=ResponseBase)
def get_class_detail(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取本体概念详情"""
    item = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.id == class_id,
        IalmdOntologyClass.is_deleted == 0,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="概念不存在")
    return ResponseBase(data=OntologyClassVO.model_validate(item).model_dump())


@router.post("/classes", response_model=ResponseBase)
def create_class(
    data: OntologyClassCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """新建本体概念/实例"""
    # 唯一性校验
    exists = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.class_code == data.class_code,
        IalmdOntologyClass.is_deleted == 0,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail=f"class_code '{data.class_code}' 已存在")

    item = IalmdOntologyClass(**data.model_dump())
    item.created_by = current_user.get("id")
    db.add(item)
    db.commit()
    db.refresh(item)

    # 写审计日志
    audit = SysOntologyAuditLog(
        entity_type="CLASS",
        entity_id=item.id,
        action="CREATE",
        after_json={"class_code": item.class_code, "class_name": item.class_name},
        operator_id=current_user.get("id"),
        operator_name=current_user.get("username", ""),
    )
    db.add(audit)
    db.commit()
    return ResponseBase(data=OntologyClassVO.model_validate(item).model_dump())


@router.put("/classes/{class_id}", response_model=ResponseBase)
def update_class(
    class_id: int,
    data: OntologyClassUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新本体概念"""
    item = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.id == class_id,
        IalmdOntologyClass.is_deleted == 0,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="概念不存在")

    before = {"class_code": item.class_code, "class_name": item.class_name}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.updated_by = current_user.get("id")
    db.commit()
    db.refresh(item)

    audit = SysOntologyAuditLog(
        entity_type="CLASS",
        entity_id=item.id,
        action="UPDATE",
        before_json=before,
        after_json={"class_code": item.class_code, "class_name": item.class_name},
        operator_id=current_user.get("id"),
        operator_name=current_user.get("username", ""),
    )
    db.add(audit)
    db.commit()
    return ResponseBase(data=OntologyClassVO.model_validate(item).model_dump())


@router.delete("/classes/{class_id}", response_model=ResponseBase)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """软删除本体概念（标记为 DEPRECATED）"""
    item = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.id == class_id,
        IalmdOntologyClass.is_deleted == 0,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="概念不存在")
    item.publish_status = "DEPRECATED"
    item.is_deleted = 1
    item.updated_by = current_user.get("id")
    db.commit()

    audit = SysOntologyAuditLog(
        entity_type="CLASS",
        entity_id=class_id,
        action="DELETE",
        before_json={"class_code": item.class_code},
        operator_id=current_user.get("id"),
        operator_name=current_user.get("username", ""),
    )
    db.add(audit)
    db.commit()
    return ResponseBase(message="概念已弃用")


# =============================================================
# 2. 本体关系
# =============================================================

@router.get("/relations", response_model=ResponseBase)
def list_relations(
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    relation_type: Optional[str] = None,
    is_instance: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取关系列表"""
    q = db.query(IalmdOntologyRelation).filter(
        IalmdOntologyRelation.status == 1,
        IalmdOntologyRelation.is_deleted == 0,
    )
    if source_id:
        q = q.filter(or_(
            IalmdOntologyRelation.source_class_id == source_id,
            IalmdOntologyRelation.instance_source_id == source_id,
        ))
    if target_id:
        q = q.filter(or_(
            IalmdOntologyRelation.target_class_id == target_id,
            IalmdOntologyRelation.instance_target_id == target_id,
        ))
    if relation_type:
        q = q.filter(IalmdOntologyRelation.relation_type == relation_type)
    if is_instance is not None:
        q = q.filter(IalmdOntologyRelation.is_instance == is_instance)
    items = q.order_by(IalmdOntologyRelation.id.desc()).limit(500).all()
    return ResponseBase(data=[OntologyRelationVO.model_validate(i).model_dump() for i in items])


@router.post("/relations", response_model=ResponseBase)
def create_relation(
    data: OntologyRelationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建关系"""
    item = IalmdOntologyRelation(**data.model_dump())
    item.created_by = current_user.get("id")
    db.add(item)
    db.commit()
    db.refresh(item)
    return ResponseBase(data=OntologyRelationVO.model_validate(item).model_dump())


@router.delete("/relations/{relation_id}", response_model=ResponseBase)
def delete_relation(
    relation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除关系"""
    item = db.query(IalmdOntologyRelation).filter(IalmdOntologyRelation.id == relation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="关系不存在")
    item.is_deleted = 1
    item.status = 0
    db.commit()
    return ResponseBase(message="关系已删除")


# =============================================================
# 3. 异构映射
# =============================================================

@router.get("/mappings", response_model=PageResponse)
def list_mappings(
    page: int = 1,
    page_size: int = 20,
    institution_id: Optional[int] = None,
    mapping_rule: Optional[str] = None,
    verify_status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取异构映射列表（分页）"""
    q = db.query(IalmdIndicatorMapping).filter(
        IalmdIndicatorMapping.status == 1,
        IalmdIndicatorMapping.is_deleted == 0,
    )
    if institution_id:
        q = q.filter(IalmdIndicatorMapping.institution_id == institution_id)
    if mapping_rule:
        q = q.filter(IalmdIndicatorMapping.mapping_rule == mapping_rule)
    if verify_status:
        q = q.filter(IalmdIndicatorMapping.verify_status == verify_status)
    if keyword:
        q = q.filter(IalmdIndicatorMapping.local_name.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(IalmdIndicatorMapping.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[IndicatorMappingVO.model_validate(i).model_dump() for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/mappings", response_model=ResponseBase)
def create_mapping(
    data: IndicatorMappingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建异构映射"""
    item = IalmdIndicatorMapping(**data.model_dump())
    item.created_by = current_user.get("id")
    db.add(item)
    db.commit()
    db.refresh(item)
    return ResponseBase(data=IndicatorMappingVO.model_validate(item).model_dump())


@router.post("/mappings/{mapping_id}/approve", response_model=ResponseBase)
def approve_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """审核通过映射"""
    item = db.query(IalmdIndicatorMapping).filter(IalmdIndicatorMapping.id == mapping_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="映射不存在")
    item.verify_status = "APPROVED"
    item.verified_by = current_user.get("id")
    item.verified_at = datetime.now()
    db.commit()
    return ResponseBase(message="已审核通过")


@router.post("/mappings/{mapping_id}/reject", response_model=ResponseBase)
def reject_mapping(
    mapping_id: int,
    remark: str = "",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """驳回映射"""
    item = db.query(IalmdIndicatorMapping).filter(IalmdIndicatorMapping.id == mapping_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="映射不存在")
    item.verify_status = "REJECTED"
    item.verified_by = current_user.get("id")
    item.verified_at = datetime.now()
    db.commit()
    return ResponseBase(message="已驳回")


# =============================================================
# 4. 映射候选 (LLM 推断)
# =============================================================

@router.get("/mapping-candidates", response_model=PageResponse)
def list_candidates(
    page: int = 1,
    page_size: int = 20,
    institution_id: Optional[int] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取映射候选列表（LLM 推断缓冲）"""
    q = db.query(IalmdMappingCandidate).filter(
        IalmdMappingCandidate.status == 1,
        IalmdMappingCandidate.is_deleted == 0,
    )
    if institution_id:
        q = q.filter(IalmdMappingCandidate.institution_id == institution_id)
    if review_status:
        q = q.filter(IalmdMappingCandidate.review_status == review_status)
    total = q.count()
    items = q.order_by(IalmdMappingCandidate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[MappingCandidateVO.model_validate(i).model_dump() for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/mapping-candidates/{candidate_id}/approve", response_model=ResponseBase)
def approve_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """审核通过候选，自动写入正式映射表"""
    cand = db.query(IalmdMappingCandidate).filter(IalmdMappingCandidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="候选不存在")
    if not cand.candidate_class_id:
        raise HTTPException(status_code=400, detail="候选无推荐类")

    # 写入正式映射表
    new_mapping = IalmdIndicatorMapping(
        institution_id=cand.institution_id,
        local_name=cand.local_name,
        ontology_class_id=cand.candidate_class_id,
        mapping_rule=cand.llm_model and "LLM" or "MANUAL",
        confidence=cand.confidence,
        source_context=cand.raw_context,
        llm_model=cand.llm_model,
        mapping_reason=cand.llm_reasoning,
        verify_status="APPROVED",
        verified_by=current_user.get("id"),
        verified_at=datetime.now(),
        created_by=current_user.get("id"),
    )
    db.add(new_mapping)
    db.flush()

    # 更新候选状态
    cand.review_status = "APPROVED"
    cand.reviewed_by = current_user.get("id")
    cand.reviewed_at = datetime.now()
    cand.final_mapping_id = new_mapping.id
    db.commit()
    return ResponseBase(data={"mapping_id": new_mapping.id}, message="已通过并入库")


# =============================================================
# 5. 银行本体（实例）
# =============================================================

@router.get("/banks", response_model=ResponseBase)
def list_banks(
    bank_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取银行本体实例列表（含关联统计）"""
    q = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.status == 1,
        IalmdBankInstitution.is_deleted == 0,
    )
    if bank_type:
        q = q.filter(IalmdBankInstitution.bank_type == bank_type)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            IalmdBankInstitution.bank_name.like(like),
            IalmdBankInstitution.short_name.like(like),
            IalmdBankInstitution.bank_code.like(like),
        ))
    items = q.order_by(IalmdBankInstitution.id).all()
    result = []
    for b in items:
        # 关联统计
        indicator_count = db.query(func.count(IalmdIndicatorMapping.id)).filter(
            IalmdIndicatorMapping.institution_id == b.id,
            IalmdIndicatorMapping.is_deleted == 0,
        ).scalar() or 0
        report_count = db.query(func.count(IalmdBankReportLink.id)).filter(
            IalmdBankReportLink.institution_id == b.id,
            IalmdBankReportLink.is_deleted == 0,
        ).scalar() or 0
        vo = BankOntologyVO.model_validate(b).model_dump()
        vo["indicator_count"] = indicator_count
        vo["report_count"] = report_count
        vo["mapping_count"] = indicator_count
        result.append(vo)
    return ResponseBase(data=result)


@router.get("/banks/{bank_id}", response_model=ResponseBase)
def get_bank_detail(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取银行本体详情"""
    b = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    if not b:
        raise HTTPException(status_code=404, detail="机构不存在")

    # 关联的指标映射
    mappings = db.query(IalmdIndicatorMapping, IalmdOntologyClass).join(
        IalmdOntologyClass, IalmdIndicatorMapping.ontology_class_id == IalmdOntologyClass.id,
    ).filter(
        IalmdIndicatorMapping.institution_id == bank_id,
        IalmdIndicatorMapping.is_deleted == 0,
        IalmdOntologyClass.is_deleted == 0,
    ).limit(200).all()

    # 关联的报告
    reports = db.query(IalmdBankReportLink).filter(
        IalmdBankReportLink.institution_id == bank_id,
        IalmdBankReportLink.is_deleted == 0,
    ).order_by(IalmdBankReportLink.report_type, desc(IalmdBankReportLink.report_year)).all()

    # 关联的关系（以银行为源或目标）
    relations = db.query(IalmdOntologyRelation).filter(
        IalmdOntologyRelation.is_deleted == 0,
        or_(
            IalmdOntologyRelation.instance_source_id == bank_id,
            IalmdOntologyRelation.instance_target_id == bank_id,
        )
    ).all()

    vo = BankOntologyVO.model_validate(b).model_dump()
    vo["mappings"] = [{
        "id": m[0].id,
        "local_name": m[0].local_name,
        "ontology_class_id": m[0].ontology_class_id,
        "ontology_class_name": m[1].class_name,
        "ontology_class_code": m[1].class_code,
        "mapping_rule": m[0].mapping_rule,
        "confidence": float(m[0].confidence),
        "verify_status": m[0].verify_status,
    } for m in mappings]
    vo["reports"] = [BankReportLinkVO.model_validate(r).model_dump() for r in reports]
    vo["report_summary"] = {}
    for r in reports:
        rt = r.report_type
        if rt not in vo["report_summary"]:
            vo["report_summary"][rt] = {"count": 0, "years": [], "latest": ""}
        vo["report_summary"][rt]["count"] += 1
        vo["report_summary"][rt]["years"].append(r.report_year)
    for rt in vo["report_summary"]:
        vo["report_summary"][rt]["years"].sort(reverse=True)
        latest = max(vo["report_summary"][rt]["years"])
        vo["report_summary"][rt]["latest"] = f"{latest}年"
    vo["relations"] = [OntologyRelationVO.model_validate(r).model_dump() for r in relations]
    return ResponseBase(data=vo)


# =============================================================
# 6. 银行报告
# =============================================================

@router.get("/bank-reports", response_model=PageResponse)
def list_bank_reports(
    page: int = 1,
    page_size: int = 20,
    institution_id: Optional[int] = None,
    bank_code: Optional[str] = None,
    report_type: Optional[str] = None,
    report_year: Optional[int] = None,
    extraction_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取银行报告列表"""
    q = db.query(IalmdBankReportLink).filter(
        IalmdBankReportLink.status == 1,
        IalmdBankReportLink.is_deleted == 0,
    )
    if institution_id:
        q = q.filter(IalmdBankReportLink.institution_id == institution_id)
    if bank_code:
        q = q.filter(IalmdBankReportLink.bank_code == bank_code)
    if report_type:
        q = q.filter(IalmdBankReportLink.report_type == report_type)
    if report_year:
        q = q.filter(IalmdBankReportLink.report_year == report_year)
    if extraction_status:
        q = q.filter(IalmdBankReportLink.extraction_status == extraction_status)
    total = q.count()
    items = q.order_by(desc(IalmdBankReportLink.report_year), IalmdBankReportLink.bank_code).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[BankReportLinkVO.model_validate(i).model_dump() for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/bank-reports/scan", response_model=ResponseBase)
def scan_bank_reports(
    base_dir: str = Query("保险经营报告下载", description="报告根目录"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """扫描报告文件夹，建立银行-报告关联索引"""
    if not os.path.exists(base_dir):
        raise HTTPException(status_code=404, detail=f"目录不存在: {base_dir}")

    # 机构代码映射
    bank_code_map = {
        "中国工商银行": "ICBC", "中国建设银行": "CCB", "中国农业银行": "ABC",
        "中国银行": "BOC", "交通银行": "BCOM", "中国邮政储蓄银行": "PSBC",
        "招商银行": "CMB", "上海浦东发展银行": "SPDB", "中国民生银行": "CMBC",
        "中国光大银行": "CGB", "华夏银行": "HXB", "中信银行": "CITIC",
        "兴业银行": "CIB", "平安银行": "PAB", "浙商银行": "BJTB",
        "上海银行": "SHPD", "渤海银行": "BOS", "北京银行": "BJCN",
        "宁波银行": "BJBANK", "南京银行": "NJCB", "江苏银行": "BJBK",
        "杭州银行": "HZBANK", "成都银行": "CDBANK", "长沙银行": "CSBANK",
        "重庆银行": "CQBANK", "郑州银行": "ZZBANK", "青岛银行": "QDBANK",
        "齐鲁银行": "QLBANK", "西安银行": "XABANK", "兰州银行": "LZBANK",
        "贵阳银行": "GYBANK", "厦门银行": "XMBANK", "苏州银行": "SUZHOUBANK",
        "无锡银行": "WUXIBANK", "常熟农村商业银行": "CSRCB",
        "张家港农村商业银行": "ZJRCB", "无锡农村商业银行": "WJRCB",
        "浙江绍兴瑞丰农村商业银行": "ZJRFB", "紫金农村商业银行": "ZJRH",
        "苏州农村商业银行": "SZRCB", "重庆农村商业银行": "CQRCB",
        "青岛农村商业银行": "QDCRCB", "江阴农村商业银行": "ZJGCR",
        "国家开发银行": "CDB", "中国进出口银行": "EXIM", "中国农业发展银行": "ADBC",
    }

    # 报告类型映射
    type_map = {
        "年度报告": "ANNUAL",
        "半年度报告": "HALF",
        "季度报告": "QREPORT",
        "业绩快报": "EXPRESS",
        "资本充足率信息披露报告": "CAPITAL",
        "流动性风险信息披露报告": "LIQUIDITY",
        "社会责任报告ESG": "ESG",
        "普惠金融服务报告": "INCLUSIVE",
        "消费者权益保护工作报告": "CONSUMER",
        "绿色金融专项报告": "GREEN",
    }

    # 机构类型映射
    type_for_bank = {
        "ICBC": "BIG_STATE", "CCB": "BIG_STATE", "ABC": "BIG_STATE",
        "BOC": "BIG_STATE", "BCOM": "BIG_STATE", "PSBC": "BIG_STATE",
        "CMB": "JOINT_STOCK", "SPDB": "JOINT_STOCK", "CMBC": "JOINT_STOCK",
        "CGB": "JOINT_STOCK", "HXB": "JOINT_STOCK", "CITIC": "JOINT_STOCK",
        "CIB": "JOINT_STOCK", "PAB": "JOINT_STOCK", "BJTB": "JOINT_STOCK",
        "SHPD": "CITY", "BOS": "CITY", "BJCN": "CITY", "BJBANK": "CITY",
        "NJCB": "CITY", "BJBK": "CITY", "HZBANK": "CITY", "CDBANK": "CITY",
        "CSBANK": "CITY", "CQBANK": "CITY", "ZZBANK": "CITY", "QDBANK": "CITY",
        "QLBANK": "CITY", "XABANK": "CITY", "LZBANK": "CITY", "GYBANK": "CITY",
        "XMBANK": "CITY", "SUZHOUBANK": "CITY", "WUXIBANK": "CITY",
        "CSRCB": "RURAL", "ZJRCB": "RURAL", "WJRCB": "RURAL", "ZJRFB": "RURAL",
        "ZJRH": "RURAL", "SZRCB": "RURAL", "CQRCB": "RURAL",
        "QDCRCB": "RURAL", "ZJGCR": "RURAL",
        "CDB": "POLICY", "EXIM": "POLICY", "ADBC": "POLICY",
    }

    scanned = 0
    new_added = 0
    # 文件名解析正则: 2013年年度报告.pdf / 2025年第三季度报告.pdf
    pattern = re.compile(r"(\d{4})年(.+?)\.(html|pdf)$", re.IGNORECASE)

    for bank_dir in os.listdir(base_dir):
        bank_path = os.path.join(base_dir, bank_dir)
        if not os.path.isdir(bank_path):
            continue
        code = bank_code_map.get(bank_dir, "")
        if not code:
            continue

        # 找机构
        inst = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.bank_code == code,
            IalmdBankInstitution.is_deleted == 0,
        ).first()
        if not inst:
            continue
        institution_id = inst.id

        for type_dir in os.listdir(bank_path):
            type_path = os.path.join(bank_path, type_dir)
            if not os.path.isdir(type_path):
                continue
            rtype = type_map.get(type_dir)
            if not rtype:
                continue

            for f in os.listdir(type_path):
                m = pattern.match(f)
                if not m:
                    continue
                year = int(m.group(1))
                fmt = m.group(3).upper()
                full_path = os.path.join(type_path, f)
                # 计算文件大小
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0
                # 计算 hash（仅小文件，>10MB 跳过）
                file_hash = ""
                if size < 10 * 1024 * 1024:
                    try:
                        with open(full_path, "rb") as fh:
                            file_hash = hashlib.md5(fh.read()).hexdigest()[:16]
                    except Exception:
                        pass

                # 是否已存在
                exists_link = db.query(IalmdBankReportLink).filter(
                    IalmdBankReportLink.bank_code == code,
                    IalmdBankReportLink.report_type == rtype,
                    IalmdBankReportLink.report_year == year,
                    IalmdBankReportLink.file_format == fmt,
                ).first()
                if exists_link:
                    scanned += 1
                    continue
                link = IalmdBankReportLink(
                    institution_id=institution_id,
                    bank_code=code,
                    report_type=rtype,
                    report_year=year,
                    report_period="FY" if rtype == "ANNUAL" else (
                        "H1" if rtype == "HALF" else (
                            "Q3" if "三季" in f else (
                                "Q2" if "半年" in f else "Q1" if rtype == "QREPORT" else "FY"
                            )
                        )
                    ),
                    file_format=fmt,
                    file_name=f,
                    file_path=full_path,
                    file_size=size,
                    file_hash=file_hash,
                    exists_flag=1,
                    extraction_status="PENDING",
                )
                db.add(link)
                new_added += 1
                scanned += 1

    db.commit()
    return ResponseBase(data={"scanned": scanned, "new_added": new_added})


# =============================================================
# 7. 关系类型枚举 / 标签
# =============================================================

@router.get("/relation-types", response_model=ResponseBase)
def list_relation_types(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取所有关系类型"""
    items = db.query(IalmdOntologyRelationType).filter(
        IalmdOntologyRelationType.status == 1,
        IalmdOntologyRelationType.is_deleted == 0,
    ).order_by(IalmdOntologyRelationType.sort_order).all()
    return ResponseBase(data=[RelationTypeVO.model_validate(i).model_dump() for i in items])


@router.get("/tags", response_model=ResponseBase)
def list_tags(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取所有本体标签"""
    items = db.query(IalmdOntologyTag).filter(
        IalmdOntologyTag.status == 1,
        IalmdOntologyTag.is_deleted == 0,
    ).order_by(IalmdOntologyTag.sort_order).all()
    return ResponseBase(data=[TagVO.model_validate(i).model_dump() for i in items])


# =============================================================
# 8. 版本管理
# =============================================================

@router.get("/versions", response_model=ResponseBase)
def list_versions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取版本列表"""
    items = db.query(IalmdOntologyVersion).order_by(desc(IalmdOntologyVersion.id)).all()
    return ResponseBase(data=[OntologyVersionVO.model_validate(i).model_dump() for i in items])


@router.post("/versions/publish", response_model=ResponseBase)
def publish_version(
    version_code: str = Query(...),
    version_desc: str = Query(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """发布新版本（生成快照）"""
    # 取消其他版本的当前标记
    db.query(IalmdOntologyVersion).filter(IalmdOntologyVersion.is_current == 1).update({"is_current": 0})

    # 统计
    class_count = db.query(func.count(IalmdOntologyClass.id)).filter(
        IalmdOntologyClass.is_deleted == 0,
        IalmdOntologyClass.entity_type == "CLASS",
    ).scalar() or 0
    rel_count = db.query(func.count(IalmdOntologyRelation.id)).filter(
        IalmdOntologyRelation.is_deleted == 0,
    ).scalar() or 0
    map_count = db.query(func.count(IalmdIndicatorMapping.id)).filter(
        IalmdIndicatorMapping.is_deleted == 0,
    ).scalar() or 0

    # 全量快照
    import json
    classes = db.query(IalmdOntologyClass).filter(IalmdOntologyClass.is_deleted == 0).all()
    relations = db.query(IalmdOntologyRelation).filter(IalmdOntologyRelation.is_deleted == 0).all()
    mappings = db.query(IalmdIndicatorMapping).filter(IalmdIndicatorMapping.is_deleted == 0).all()
    snapshot = {
        "classes": [
            {c: getattr(x, c) for c in [
                "id", "class_code", "class_name", "class_name_en", "parent_id",
                "class_level", "entity_type", "instance_of_id", "bank_code",
                "publish_status", "sort_order"
            ]} for x in classes
        ],
        "relations": [
            {c: getattr(x, c) for c in [
                "id", "source_class_id", "target_class_id", "relation_type",
                "is_instance", "instance_source_id", "instance_target_id",
                "weight", "confidence"
            ]} for x in relations
        ],
        "mappings": [
            {c: getattr(x, c) for c in [
                "id", "institution_id", "local_name", "ontology_class_id",
                "mapping_rule", "confidence", "verify_status"
            ]} for x in mappings
        ],
    }

    ver = IalmdOntologyVersion(
        version_code=version_code,
        version_desc=version_desc,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False, default=str),
        publish_status="PUBLISHED",
        is_current=1,
        published_by=current_user.get("id"),
        published_at=datetime.now(),
        class_count=class_count,
        relation_count=rel_count,
        mapping_count=map_count,
        created_by=current_user.get("id"),
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)
    return ResponseBase(data=OntologyVersionVO.model_validate(ver).model_dump(), message="版本已发布")


# =============================================================
# 9. 审计日志
# =============================================================

@router.get("/audit-logs", response_model=PageResponse)
def list_audit_logs(
    page: int = 1,
    page_size: int = 30,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取审计日志"""
    q = db.query(SysOntologyAuditLog)
    if entity_type:
        q = q.filter(SysOntologyAuditLog.entity_type == entity_type)
    if action:
        q = q.filter(SysOntologyAuditLog.action == action)
    total = q.count()
    items = q.order_by(desc(SysOntologyAuditLog.id)).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[AuditLogVO.model_validate(i).model_dump() for i in items],
        total=total, page=page, page_size=page_size,
    )


# =============================================================
# 10. 统计概览
# =============================================================

@router.get("/stats", response_model=ResponseBase)
def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """本体管理统计概览"""
    class_count = db.query(func.count(IalmdOntologyClass.id)).filter(
        IalmdOntologyClass.is_deleted == 0,
        IalmdOntologyClass.entity_type == "CLASS",
    ).scalar() or 0
    instance_count = db.query(func.count(IalmdOntologyClass.id)).filter(
        IalmdOntologyClass.is_deleted == 0,
        IalmdOntologyClass.entity_type == "INSTANCE",
    ).scalar() or 0
    rel_count = db.query(func.count(IalmdOntologyRelation.id)).filter(
        IalmdOntologyRelation.is_deleted == 0,
    ).scalar() or 0
    inst_rel_count = db.query(func.count(IalmdOntologyRelation.id)).filter(
        IalmdOntologyRelation.is_deleted == 0,
        IalmdOntologyRelation.is_instance == 1,
    ).scalar() or 0
    mapping_total = db.query(func.count(IalmdIndicatorMapping.id)).filter(
        IalmdIndicatorMapping.is_deleted == 0,
    ).scalar() or 0
    mapping_pending = db.query(func.count(IalmdIndicatorMapping.id)).filter(
        IalmdIndicatorMapping.is_deleted == 0,
        IalmdIndicatorMapping.verify_status == "PENDING",
    ).scalar() or 0
    candidate_pending = db.query(func.count(IalmdMappingCandidate.id)).filter(
        IalmdMappingCandidate.is_deleted == 0,
        IalmdMappingCandidate.review_status == "PENDING",
    ).scalar() or 0
    bank_count = db.query(func.count(IalmdBankInstitution.id)).filter(
        IalmdBankInstitution.is_deleted == 0,
    ).scalar() or 0
    report_count = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.is_deleted == 0,
    ).scalar() or 0
    version_count = db.query(func.count(IalmdOntologyVersion.id)).scalar() or 0

    return ResponseBase(data={
        "class_count": class_count,
        "instance_count": instance_count,
        "relation_count": rel_count,
        "instance_relation_count": inst_rel_count,
        "mapping_total": mapping_total,
        "mapping_pending": mapping_pending,
        "candidate_pending": candidate_pending,
        "bank_count": bank_count,
        "report_count": report_count,
        "version_count": version_count,
    })


# =============================================================
# 11. 银行文件管理 — 列出/下载保险经营报告文件夹下的文件
# =============================================================

from app.config import settings

REPORT_BASE_DIR = settings.REPORTS_DIR


@router.get("/banks/{bank_id}/files", response_model=ResponseBase)
def list_bank_files(
    bank_id: int,
    subpath: str = Query("", description="子路径(空=列出报告类型目录, 类型名=列出该类型下文件)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """列出银行报告文件 — 支持两层浏览：类型目录 + 类型内文件"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")

    bank_dir = os.path.join(REPORT_BASE_DIR, bank.bank_name)
    if not os.path.exists(bank_dir):
        # 尝试用简称
        bank_dir = os.path.join(REPORT_BASE_DIR, bank.short_name) if bank.short_name else ""
        if not bank_dir or not os.path.exists(bank_dir):
            return ResponseBase(data={"bank_name": bank.bank_name, "path": "", "items": [], "exists": False})

    if subpath:
        # 列出某个报告类型下的文件
        type_dir = os.path.join(bank_dir, subpath)
        if not os.path.exists(type_dir) or not os.path.isdir(type_dir):
            return ResponseBase(data={"bank_name": bank.bank_name, "path": subpath, "items": [], "exists": False})
        items = []
        for fn in sorted(os.listdir(type_dir)):
            fp = os.path.join(type_dir, fn)
            if os.path.isfile(fp):
                try:
                    sz = os.path.getsize(fp)
                except OSError:
                    sz = 0
                items.append({
                    "name": fn,
                    "size": sz,
                    "size_fmt": f"{sz / 1024 / 1024:.2f} MB" if sz > 1024 * 1024 else f"{sz / 1024:.1f} KB",
                    "ext": os.path.splitext(fn)[1].lower(),
                    "rel_path": f"{subpath}/{fn}".replace("\\", "/"),
                })
        return ResponseBase(data={
            "bank_name": bank.bank_name,
            "bank_code": bank.bank_code,
            "path": subpath,
            "items": items,
            "total": len(items),
            "exists": True,
        })
    else:
        # 列出报告类型目录
        items = []
        for dn in sorted(os.listdir(bank_dir)):
            dp = os.path.join(bank_dir, dn)
            if os.path.isdir(dp):
                file_count = sum(1 for _ in os.listdir(dp) if os.path.isfile(os.path.join(dp, _)))
                items.append({
                    "name": dn,
                    "type": "directory",
                    "file_count": file_count,
                })
        return ResponseBase(data={
            "bank_name": bank.bank_name,
            "bank_code": bank.bank_code,
            "path": "",
            "items": items,
            "total": len(items),
            "exists": True,
        })


@router.get("/banks/{bank_id}/files/download")
def download_bank_file(
    bank_id: int,
    rel_path: str = Query(..., description="文件相对路径（不含机构名称），如 '年度报告/2024年年度报告.pdf'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """下载银行报告文件"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")

    bank_dir = os.path.join(REPORT_BASE_DIR, bank.bank_name)
    if not os.path.exists(bank_dir):
        bank_dir = os.path.join(REPORT_BASE_DIR, bank.short_name) if bank.short_name else ""
        if not bank_dir or not os.path.exists(bank_dir):
            raise HTTPException(status_code=404, detail=f"报告目录不存在: {bank.bank_name}")

    # 安全检查：防止路径穿越
    full_path = os.path.normpath(os.path.join(bank_dir, rel_path))
    if not full_path.startswith(os.path.normpath(bank_dir)):
        raise HTTPException(status_code=403, detail="非法路径")

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {rel_path}")

    return FileResponse(
        full_path,
        filename=os.path.basename(full_path),
        media_type="application/octet-stream",
    )