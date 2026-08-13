"""报告采集服务 V2 — 高效版：年份过滤 + 已处理跳过 + 直接入库"""
import os, re, json, time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from app.config import settings

DOWNLOAD_ROOT = Path(settings.REPORTS_DIR)

# 指标定义（对标指标定义表 ialmd_indicator_define）
INDICATOR_CATEGORIES = {
    "经营成果": [
        ("利息净收入", "PROFIT_NII"),
        ("手续费及佣金净收入", "PROFIT_NCI"),
        ("营业收入", "PROFIT_REVENUE"),
        ("业务及管理费", "PROFIT_OPE"),
        ("资产减值损失", "PROFIT_LLP"),
        ("营业利润", "PROFIT_OP_INC"),
        ("税前利润", "PROFIT_PBT"),
        ("净利润", "PROFIT_NET_INC"),
        ("信用减值损失", "PROFIT_LLP"),
    ],
    "资产负债": [
        ("资产总额", "ASSET_LIAB_TOTAL_ASSET"),
        ("客户贷款及垫款总额", "ASSET_LIAB_LOAN"),
        ("公司类贷款", "ASSET_LIAB_CORP_LOAN"),
        ("个人贷款", "ASSET_LIAB_PER_LOAN"),
        ("票据贴现", "ASSET_LIAB_BILL_DISC"),
        ("贷款减值准备", "ASSET_LIAB_LLR"),
        ("投资", "ASSET_LIAB_INVEST"),
        ("负债总额", "ASSET_LIAB_TOTAL_LIAB"),
        ("客户存款", "ASSET_LIAB_DEPOSIT"),
        ("归属于母公司股东的权益", "ASSET_LIAB_EQUITY"),
    ],
    "资本净额": [
        ("核心一级资本净额", "CAPITAL_CET1"),
        ("一级资本净额", "CAPITAL_TIER1"),
        ("总资本净额", "CAPITAL_TIER2"),
        ("风险加权资产", "CAPITAL_RWA"),
    ],
    "每股指标": [
        ("每股净资产", "PER_SHARE_BPS"),
        ("基本每股收益", "PER_SHARE_EPS"),
        ("稀释每股收益", "PER_SHARE_EPS_DIL"),
    ],
    "盈利能力": [
        ("平均总资产回报率", "PROFITABILITY_ROAA"),
        ("加权平均净资产收益率", "PROFITABILITY_ROE"),
        ("净利息差", "PROFITABILITY_NIM"),
        ("净利息收益率", "PROFITABILITY_NIR"),
        ("风险加权资产收益率", "PROFITABILITY_RORWA"),
        ("手续费及佣金净收入比营业收入", "PROFITABILITY_NCI_REV"),
        ("成本收入比", "PROFITABILITY_CIR"),
    ],
    "资产质量": [
        ("不良贷款率", "ASSET_QUALITY_NPL"),
        ("拨备覆盖率", "ASSET_QUALITY_PCR"),
        ("贷款拨备率", "ASSET_QUALITY_LLP_LOAN"),
    ],
    "资本充足率": [
        ("核心一级资本充足率", "CAPITAL_ADEQUACY_CET1_RATIO"),
        ("一级资本充足率", "CAPITAL_ADEQUACY_TIER1_RATIO"),
        ("资本充足率", "CAPITAL_ADEQUACY_CAR"),
        ("总权益对总资产比率", "CAPITAL_ADEQUACY_EQUITY_RATIO"),
        ("风险加权资产占总资产比率", "CAPITAL_ADEQUACY_RWA_RATIO"),
    ],
}

def extract_indicators_from_bank(bank_id, years=None, db_session=None):
    """高效版：从银行报告中提取指标值"""
    if db_session is None:
        return {"error": "数据库连接不可用"}

    from app.models.bank import IalmdBankInstitution
    from app.models.ontology import IalmdIndicatorMapping
    from sqlalchemy import func

    bank = db_session.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id, IalmdBankInstitution.is_deleted == 0,
    ).first()
    if not bank:
        return {"error": "机构不存在"}

    bank_dir = DOWNLOAD_ROOT / bank.bank_name
    if not bank_dir.exists():
        return {"error": f"报告目录不存在: {bank_dir}"}

    # 批量加载指标定义（一次查询）
    indicator_map = _load_indicator_defs(db_session)

    result = {"bank": bank.bank_name, "extracted": 0, "files_processed": 0, "skipped": 0, "errors": 0}

    # 按年份过滤
    year_set = set(years) if years else None

    for rtype_dir in sorted(bank_dir.iterdir()):
        if not rtype_dir.is_dir():
            continue

        for fpath in sorted(rtype_dir.iterdir()):
            if not fpath.is_file():
                continue

            # 提取文件名中的年份
            year_m = re.search(r"(\d{4})", fpath.name)
            year = int(year_m.group(1)) if year_m else 0
            if year == 0:
                continue
            if year_set and year not in year_set:
                continue

            # 检查是否已处理
            if _is_already_extracted(db_session, bank.id, year):
                result["skipped"] += 1
                continue

            result["files_processed"] += 1

            # 提取
            if fpath.suffix.lower() == ".pdf":
                indicators = _extract_from_pdf_text(fpath)
            elif fpath.suffix.lower() == ".html":
                indicators = _extract_from_html_text(fpath)
            else:
                continue

            if not indicators:
                continue

            # 入库
            stored = _store_indicators_fast(db_session, bank.id, year, indicators, indicator_map, str(fpath))
            result["extracted"] += stored
            if stored == 0:
                result["errors"] += 1

    db_session.commit()
    return result


def _load_indicator_defs(db_session):
    """批量加载指标定义 → 名称到ID的映射"""
    from app.models.indicator import IalmdIndicatorDefine
    from app.models.ontology import IalmdOntologyClass

    id_map = {}

    # 从指标定义表加载
    defs = db_session.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.is_deleted == 0,
        IalmdIndicatorDefine.status == 1,
    ).all()
    for d in defs:
        if d.indicator_name and d.indicator_code:
            id_map[d.indicator_name] = d.id
            # 还加上本体code作为key
            id_map[d.indicator_code] = d.id

    # 从本体概念表加载（概念名→指标ID）
    concepts = db_session.query(IalmdOntologyClass).filter(
        IalmdOntologyClass.is_deleted == 0,
        IalmdOntologyClass.entity_type == "CLASS",
        IalmdOntologyClass.indicator_id.isnot(None),
    ).all()
    for c in concepts:
        if c.class_name and c.indicator_id:
            id_map[c.class_name] = c.indicator_id
        if c.class_name_en and c.indicator_id:
            id_map[c.class_name_en] = c.indicator_id

    return id_map


def _is_already_extracted(db_session, bank_id, year):
    """检查该银行+年份是否已有提取数据"""
    from app.models.indicator import IalmdIndicatorValue
    from sqlalchemy import func

    count = db_session.query(func.count(IalmdIndicatorValue.id)).filter(
        IalmdIndicatorValue.institution_id == bank_id,
        IalmdIndicatorValue.report_year == year,
        IalmdIndicatorValue.is_deleted == 0,
        IalmdIndicatorValue.confidence >= 0.8,
    ).scalar() or 0
    return count >= 30


def _extract_from_pdf_text(filepath):
    """从PDF文本中提取指标值"""
    import pypdf
    indicators = {}
    try:
        full_text = ""
        with open(filepath, "rb") as f:
            reader = pypdf.PdfReader(f)
            max_pages = min(len(reader.pages), 15)
            for i in range(max_pages):
                try:
                    txt = reader.pages[i].extract_text()
                    if txt:
                        full_text += txt + "\n"
                except Exception:
                    pass

        return _match_indicators(full_text)
    except Exception:
        return indicators


def _extract_from_html_text(filepath):
    """从HTML文本中提取指标值"""
    indicators = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"\s+", " ", text)

        return _match_indicators(text)
    except Exception:
        return indicators


def _match_indicators(text):
    """从文本中匹配所有指标"""
    result = {}
    for cat, indicators in INDICATOR_CATEGORIES.items():
        for name, code in indicators:
            escaped = re.escape(name)
            patterns = [
                rf"{escaped}[：:：\s]*([\d,]+\.?\d*)\s*[%％]?",
                rf"{escaped}[：:：\s]*\n?\s*([\d,]+\.?\d*)\s*[%％]?",
            ]
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    val = m.group(1).replace(",", "")
                    try:
                        fval = float(val)
                        # 合理性检查：避免匹配到年份等
                        if fval < 0.001 or fval > 100000000:
                            continue
                        result[name] = fval
                    except ValueError:
                        pass
                    break
    return result


def _store_indicators_fast(db_session, bank_id, year, indicators, indicator_map, source):
    """快速入库指标值（批量检查已存在）"""
    from app.models.indicator import IalmdIndicatorValue

    stored = 0
    for name, value in indicators.items():
        # 查找指标ID（名称匹配）
        indicator_id = indicator_map.get(name)
        if not indicator_id:
            # 尝试代码匹配
            for cat_indicators in INDICATOR_CATEGORIES.values():
                for iname, icode in cat_indicators:
                    if iname == name:
                        indicator_id = indicator_map.get(icode)
                        break
                if indicator_id:
                    break
        if not indicator_id:
            continue

        # 检查是否已存在
        exists = db_session.query(IalmdIndicatorValue.id).filter(
            IalmdIndicatorValue.indicator_id == indicator_id,
            IalmdIndicatorValue.institution_id == bank_id,
            IalmdIndicatorValue.report_year == year,
            IalmdIndicatorValue.report_period == "FY",
            IalmdIndicatorValue.is_deleted == 0,
        ).first()
        if exists:
            continue

        # 存入
        val = IalmdIndicatorValue(
            indicator_id=indicator_id,
            institution_id=bank_id,
            report_id=0,
            value_numeric=value,
            value_text=str(value),
            report_year=year,
            report_period="FY",
            confidence=0.85,
            extract_context=source[:200] if source else "",
            verify_status="PENDING",
        )
        db_session.add(val)
        stored += 1

    return stored


def batch_extract_all(db_session, bank_type=None):
    """批量提取所有银行的指标"""
    from app.models.bank import IalmdBankInstitution
    from sqlalchemy import func

    q = db_session.query(IalmdBankInstitution).filter(IalmdBankInstitution.is_deleted == 0)
    if bank_type:
        q = q.filter(IalmdBankInstitution.bank_type == bank_type)
    banks = q.all()

    summary = {"total_banks": len(banks), "total_extracted": 0, "errors": []}
    for i, bank in enumerate(banks):
        try:
            print(f"[{i+1}/{len(banks)}] Extracting {bank.bank_name} ({bank.bank_code})...")
            r = extract_indicators_from_bank(bank.id, db_session=db_session)
            summary["total_extracted"] += r.get("extracted", 0)
            print(f"  -> {r.get('extracted', 0)} indicator values")
        except Exception as e:
            summary["errors"].append({"bank": bank.bank_name, "error": str(e)[:200]})
            print(f"  -> ERROR: {e}")

    db_session.commit()
    return summary