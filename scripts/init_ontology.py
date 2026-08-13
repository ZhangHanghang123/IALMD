# -*- coding: utf-8 -*-
"""
保险本体知识初始化脚本
参照 ALMD 的 ingest_ontology.py，适配保险 7 大类 + 20 指标

初始化内容：
  1. 关系类型枚举（relation_type）
  2. 概念树（ontology_class：Root + 7大类 + 20指标）
  3. 本体关系（ontology_relation：PARENT_CHILD + COMPUTED_FROM + SYNONYM）
  4. 异构映射（indicator_mapping：机构本地名 → 标准概念）
  5. 本体版本（ontology_version：V1.0.0）
  6. 本体标签（ontology_tag）

用法：cd backend && python ../scripts/init_ontology.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models import (
    IalmdOntologyClass, IalmdOntologyRelation, IalmdIndicatorMapping,
    IalmdOntologyVersion, IalmdOntologyRelationType, IalmdOntologyTag,
    IalmdBankInstitution, IalmdIndicatorDefine,
)
from sqlalchemy import func

db = SessionLocal()

# ==================== 7 大类定义 ====================
# (分类code, 中文名, 英文名, 描述)
CATEGORIES = [
    ("SCALE", "规模类", "Scale", "资产规模与保费规模指标"),
    ("PROFIT", "盈利类", "Profit", "盈利与投资收益率指标"),
    ("SOLVENCY", "偿付能力类", "Solvency", "偿二代偿付能力指标"),
    ("QUALITY", "业务质量类", "Quality", "成本、赔付、退保、继续率指标"),
    ("VALUE", "价值类", "Value", "精算价值指标（NBV/EV）"),
    ("CHANNEL", "渠道类", "Channel", "代理人渠道指标"),
    ("ESG", "ESG类", "ESG", "绿色保险与绿色投资指标"),
]

# ==================== 关系类型枚举 ====================
RELATION_TYPES = [
    ("PARENT_CHILD", "父子关系", "大类→指标的层级关系", "#3b82f6", "solid"),
    ("INSTANCE_OF", "实例归属", "机构实例→类型类", "#8b5cf6", "dashed"),
    ("COMPUTED_FROM", "计算依赖", "派生指标←基础指标", "#f59e0b", "dotted"),
    ("SYNONYM", "同义关系", "异名同义指标", "#10b981", "dashed"),
]

# ==================== 计算依赖关系 ====================
COMPUTE_PAIRS = [
    ("ROE", "NET_PROFIT", "净资产收益率 ← 净利润"),
    ("COMP_SOLVENCY", "ACTUAL_CAPITAL", "综合偿付能力充足率 ← 实际资本"),
    ("COMP_SOLVENCY", "MIN_CAPITAL", "综合偿付能力充足率 ← 最低资本"),
    ("CORE_SOLVENCY", "ACTUAL_CAPITAL", "核心偿付能力充足率 ← 实际资本"),
    ("CORE_SOLVENCY", "MIN_CAPITAL", "核心偿付能力充足率 ← 最低资本"),
    ("COR", "LOSS_RATIO", "综合成本率 ← 赔付率"),
]

# ==================== 同义关系 ====================
SYNONYM_PAIRS = [
    ("GPW", "GREEN_INSURANCE", "原保费收入 ↔ 绿色保险保费收入(子集)"),
]

# ==================== 异构映射别名 ====================
ALIAS_RULES = {
    "TOTAL_ASSETS": ["资产总计", "资产总额", "总资产"],
    "NET_ASSETS": ["净资产", "所有者权益", "归属于母公司股东的权益"],
    "GPW": ["原保险保费收入", "原保费收入", "保险业务收入"],
    "NET_PROFIT": ["净利润", "归属于母公司股东的净利润"],
    "ROE": ["净资产收益率", "加权平均净资产收益率", "ROE"],
    "TOTAL_INVEST_YIELD": ["总投资收益率", "综合投资收益率"],
    "NET_INVEST_YIELD": ["净投资收益率", "财务投资收益率"],
    "CORE_SOLVENCY": ["核心偿付能力充足率", "核心偿付能力"],
    "COMP_SOLVENCY": ["综合偿付能力充足率", "综合偿付能力"],
    "ACTUAL_CAPITAL": ["实际资本", "认可资产"],
    "MIN_CAPITAL": ["最低资本", "最低资本要求"],
    "COR": ["综合成本率", "综合成本"],
    "LOSS_RATIO": ["赔付率", "综合赔付率"],
    "SURRENDER_RATE": ["退保率", "退保金率"],
    "PERSISTENCY_13M": ["13个月继续率", "十三个月继续率", "13个月保费继续率"],
    "NBV": ["新业务价值", "NBV"],
    "EV": ["内含价值", "EV"],
    "AGENT_COUNT": ["代理人数量", "个险代理人", "营销员人数"],
    "GREEN_INSURANCE": ["绿色保险保费收入", "绿色保险"],
    "GREEN_INVEST": ["绿色投资规模", "绿色投资"],
}

# ==================== 本体标签 ====================
TAGS = [
    ("REGULATORY", "监管指标", "#f5222d", "监管要求的核心指标"),
    ("FINANCIAL", "财务指标", "#1677ff", "财务报表指标"),
    ("SOLVENCY_CORE", "偿付能力核心", "#fa8c16", "偿二代核心偿付能力指标"),
]


def create_relation_types():
    print("1. 创建关系类型枚举")
    count = 0
    for code, name, desc, color, style in RELATION_TYPES:
        if db.query(IalmdOntologyRelationType).filter(
            IalmdOntologyRelationType.type_code == code, IalmdOntologyRelationType.is_deleted == 0
        ).first():
            continue
        db.add(IalmdOntologyRelationType(
            type_code=code, type_name=name, type_desc=desc, color_hex=color, line_style=style,
        ))
        count += 1
    db.commit()
    print(f"  ✓ {count} 条关系类型")


def create_tags():
    print("2. 创建本体标签")
    count = 0
    for code, name, color, desc in TAGS:
        if db.query(IalmdOntologyTag).filter(IalmdOntologyTag.tag_code == code, IalmdOntologyTag.is_deleted == 0).first():
            continue
        db.add(IalmdOntologyTag(tag_code=code, tag_name=name, tag_color=color, description=desc))
        count += 1
    db.commit()
    print(f"  ✓ {count} 条标签")


def create_concept_tree():
    print("3. 创建概念树（Root + 7大类 + 20指标）")
    # 加载指标定义
    defs = db.query(IalmdIndicatorDefine).filter(IalmdIndicatorDefine.is_deleted == 0).all()
    indicator_map = {d.indicator_code: d for d in defs}

    id_map = {}  # class_code -> class_id

    # Root
    root = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.class_code == "INSURANCE_INDICATOR_ROOT", IalmdOntologyClass.is_deleted == 0
    ).first()
    if not root:
        root = IalmdOntologyClass(
            class_code="INSURANCE_INDICATOR_ROOT", class_name="保险经营指标本体",
            class_name_en="Insurance Indicator Root", class_level=0, parent_id=0,
            entity_type="CLASS", publish_status="PUBLISHED", sort_order=0,
        )
        db.add(root)
        db.flush()
    id_map["INSURANCE_INDICATOR_ROOT"] = root.id

    # 7 大类
    cat_count = 0
    for code, name, en, desc in CATEGORIES:
        cat = db.query(IalmdOntologyClass).filter(
            IalmdOntologyClass.class_code == f"CAT_{code}", IalmdOntologyClass.is_deleted == 0
        ).first()
        if not cat:
            cat = IalmdOntologyClass(
                class_code=f"CAT_{code}", class_name=name, class_name_en=en,
                parent_id=root.id, class_level=1, description=desc,
                entity_type="CLASS", publish_status="PUBLISHED", sort_order=cat_count,
            )
            db.add(cat)
            db.flush()
            cat_count += 1
        id_map[f"CAT_{code}"] = cat.id

    # 20 指标（关联指标定义）
    ind_count = 0
    for d in defs:
        code = d.indicator_code
        cat_id = id_map.get(f"CAT_{d.category_code}", root.id)
        cls = db.query(IalmdOntologyClass).filter(
            IalmdOntologyClass.class_code == code, IalmdOntologyClass.is_deleted == 0
        ).first()
        if not cls:
            cls = IalmdOntologyClass(
                class_code=code, class_name=d.indicator_name,
                class_name_en="", parent_id=cat_id, class_level=2,
                unit=d.unit or "", calc_formula=d.calc_formula or "",
                data_frequency="QUARTERLY", entity_type="CLASS",
                indicator_id=d.id, publish_status="PUBLISHED", sort_order=d.sort_order or 0,
            )
            db.add(cls)
            db.flush()
            ind_count += 1
        id_map[code] = cls.id

    db.commit()
    print(f"  ✓ 大类 {cat_count} 个，指标 {ind_count} 个")
    return id_map


def create_relations(id_map):
    print("4. 创建本体关系")
    count = 0

    # PARENT_CHILD（指标 → 大类）
    all_classes = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.is_deleted == 0, IalmdOntologyClass.parent_id > 0
    ).all()
    for cls in all_classes:
        exists = db.query(IalmdOntologyRelation).filter(
            IalmdOntologyRelation.source_class_id == cls.parent_id,
            IalmdOntologyRelation.target_class_id == cls.id,
            IalmdOntologyRelation.relation_type == "PARENT_CHILD",
            IalmdOntologyRelation.is_deleted == 0,
        ).first()
        if exists:
            continue
        db.add(IalmdOntologyRelation(
            source_class_id=cls.parent_id, target_class_id=cls.id,
            relation_type="PARENT_CHILD", description="", verify_status="APPROVED",
            confidence=1.0, is_instance=0,
        ))
        count += 1

    # COMPUTED_FROM
    for src, tgt, desc in COMPUTE_PAIRS:
        if src in id_map and tgt in id_map:
            db.add(IalmdOntologyRelation(
                source_class_id=id_map[src], target_class_id=id_map[tgt],
                relation_type="COMPUTED_FROM", description=desc,
                verify_status="APPROVED", confidence=1.0, is_instance=0,
            ))
            count += 1

    # SYNONYM
    for a, b, desc in SYNONYM_PAIRS:
        if a in id_map and b in id_map:
            db.add(IalmdOntologyRelation(
                source_class_id=id_map[a], target_class_id=id_map[b],
                relation_type="SYNONYM", description=desc,
                verify_status="APPROVED", confidence=0.9, is_instance=0,
            ))
            count += 1

    db.commit()
    print(f"  ✓ {count} 条关系")


def create_mappings(id_map):
    print("5. 创建异构映射（机构本地名 → 标准概念）")
    banks = db.query(IalmdBankInstitution).filter(IalmdBankInstitution.is_deleted == 0).all()
    count = 0
    for bank in banks:
        for base_code, aliases in ALIAS_RULES.items():
            if base_code not in id_map:
                continue
            for alias in aliases:
                exists = db.query(IalmdIndicatorMapping).filter(
                    IalmdIndicatorMapping.institution_id == bank.id,
                    IalmdIndicatorMapping.local_name == alias,
                    IalmdIndicatorMapping.is_deleted == 0,
                ).first()
                if exists:
                    continue
                db.add(IalmdIndicatorMapping(
                    institution_id=bank.id, local_name=alias,
                    ontology_class_id=id_map[base_code],
                    mapping_rule="EXACT" if alias == aliases[0] else "REGEX",
                    confidence=0.95, verify_status="APPROVED",
                    mapping_reason=f"保险机构常用格式: {alias} → {base_code}",
                ))
                count += 1
    db.commit()
    print(f"  ✓ {count} 条异构映射")


def publish_version():
    print("6. 发布本体版本 V1.0.0")
    classes = db.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.is_deleted == 0, IalmdOntologyClass.entity_type == "CLASS"
    ).all()
    relations = db.query(IalmdOntologyRelation).filter(IalmdOntologyRelation.is_deleted == 0).all()
    mappings = db.query(IalmdIndicatorMapping).filter(IalmdIndicatorMapping.is_deleted == 0).all()

    snapshot = {
        "classes": [{"id": c.id, "code": c.class_code, "name": c.class_name, "parent_id": c.parent_id} for c in classes],
        "relations": [{"source": r.source_class_id, "target": r.target_class_id, "type": r.relation_type} for r in relations],
        "mapping_count": len(mappings),  # 映射只存数量，避免 snapshot 超长
    }

    # 旧版本标记为非当前
    db.query(IalmdOntologyVersion).filter(IalmdOntologyVersion.is_current == 1).update({"is_current": 0})

    ver = IalmdOntologyVersion(
        version_code="V1.0.0",
        version_desc="保险经营指标本体初始化版本（7大类20指标）",
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        publish_status="PUBLISHED", is_current=1, published_at=datetime.now(),
        class_count=len(classes), relation_count=len(relations), mapping_count=len(mappings),
    )
    db.add(ver)
    db.commit()
    print(f"  ✓ 版本 V1.0.0（概念{len(classes)}、关系{len(relations)}、映射{len(mappings)}）")


def main():
    print("=" * 60)
    print("保险本体知识初始化")
    print("=" * 60)
    try:
        create_relation_types()
        create_tags()
        id_map = create_concept_tree()
        create_relations(id_map)
        create_mappings(id_map)
        publish_version()

        print("=" * 60)
        print("初始化完成！最终统计:")
        print(f"  概念: {db.query(func.count(IalmdOntologyClass.id)).filter(IalmdOntologyClass.is_deleted==0, IalmdOntologyClass.entity_type=='CLASS').scalar()}")
        print(f"  关系: {db.query(func.count(IalmdOntologyRelation.id)).filter(IalmdOntologyRelation.is_deleted==0).scalar()}")
        print(f"  映射: {db.query(func.count(IalmdIndicatorMapping.id)).filter(IalmdIndicatorMapping.is_deleted==0).scalar()}")
        print(f"  版本: {db.query(func.count(IalmdOntologyVersion.id)).scalar()}")
        print(f"  关系类型: {db.query(func.count(IalmdOntologyRelationType.id)).filter(IalmdOntologyRelationType.is_deleted==0).scalar()}")
        print(f"  标签: {db.query(func.count(IalmdOntologyTag.id)).filter(IalmdOntologyTag.is_deleted==0).scalar()}")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
