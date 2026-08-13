# -*- coding: utf-8 -*-
"""
保险报告采集数据初始化 + 指标提取脚本

功能：
  1. 扫描 data/保险经营报告下载/ 目录下的报告文件，录入报告采集管理数据
     （ialmd_report_record + ialmd_report_file）
  2. 从报告 PDF/HTML 中提取 20 个保险指标值（ialmd_indicator_value）

关联方式：优先使用机构代码 bank_code + 指标编码 indicator_code（代码关联）

用法：
  cd backend && python ../scripts/init_reports_and_extract.py
"""

import os
import re
import sys
import hashlib
from datetime import datetime, date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import SessionLocal
from app.models import (
    IalmdBankInstitution, IalmdReportRecord, IalmdReportFile,
    IalmdIndicatorDefine, IalmdIndicatorValue,
)
from sqlalchemy import func

REPORT_DIR = Path(settings.REPORTS_DIR)

# ==================== 报告类型映射（目录名 → 类型代码）====================
TYPE_MAP = {
    "年度报告": "ANNUAL",
    "半年度报告": "HALF",
    "季度报告": "QREPORT",
    "偿付能力报告": "SOLVENCY",
    "精算报告": "ACTUARIAL",
    "保费收入公告": "PREMIUM",
    "分红实现率公告": "DIVIDEND",
    "社会责任报告ESG": "ESG",
    "消费者权益保护工作报告": "CONSUMER",
}

# ==================== 保险指标匹配规则 ====================
# (指标编码, 匹配名称列表)
INDICATOR_PATTERNS = [
    ("CORE_SOLVENCY", ["核心偿付能力充足率", "核心偿付能力"]),
    ("COMP_SOLVENCY", ["综合偿付能力充足率", "综合偿付能力"]),
    ("ACTUAL_CAPITAL", ["实际资本"]),
    ("MIN_CAPITAL", ["最低资本"]),
    ("TOTAL_ASSETS", ["资产总计", "总资产", "资产总额"]),
    ("NET_ASSETS", ["净资产", "归属于母公司股东的权益", "所有者权益"]),
    ("GPW", ["原保险保费收入", "原保费收入", "保险业务收入"]),
    ("NET_PROFIT", ["净利润"]),
    ("ROE", ["净资产收益率", "加权平均净资产收益率"]),
    ("TOTAL_INVEST_YIELD", ["总投资收益率"]),
    ("NET_INVEST_YIELD", ["净投资收益率"]),
    ("COR", ["综合成本率"]),
    ("LOSS_RATIO", ["综合赔付率", "赔付率"]),
    ("SURRENDER_RATE", ["退保率"]),
    ("PERSISTENCY_13M", ["13个月继续率", "十三个月继续率", "13个月保费继续率", "十三个月保费继续率"]),
    ("NBV", ["新业务价值"]),
    ("EV", ["内含价值"]),
    ("AGENT_COUNT", ["代理人数量", "个险代理人", "营销员人数"]),
    ("GREEN_INSURANCE", ["绿色保险保费收入", "绿色保险"]),
    ("GREEN_INVEST", ["绿色投资规模", "绿色投资"]),
]


def safe_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def parse_filename_year(fn):
    """从文件名提取年份（支持 A股 2016年xxx.pdf 和 H股 2021_xxx.pdf 格式）"""
    m = re.search(r'(\d{4})', fn)
    return int(m.group(1)) if m else 0


def parse_period(fn):
    """判断报告期间"""
    if "半年" in fn or "中期" in fn or "H1" in fn.upper():
        return "H1"
    if "三季" in fn or "第三季" in fn or "Q3" in fn.upper():
        return "Q3"
    if "一季" in fn or "第一季" in fn or "Q1" in fn.upper():
        return "Q1"
    return "FY"


def scan_reports(db, bank_map):
    """扫描报告文件，录入报告采集管理数据"""
    print("=" * 60)
    print("步骤1: 扫描报告文件，初始化报告采集管理数据")
    print("=" * 60)

    scanned = added_record = added_file = skipped = 0

    for bank_dir in sorted(REPORT_DIR.iterdir()):
        if not bank_dir.is_dir():
            continue
        bank_name = bank_dir.name
        if bank_name not in bank_map:
            continue
        inst_id, bank_code = bank_map[bank_name]

        for type_dir in sorted(bank_dir.iterdir()):
            if not type_dir.is_dir():
                continue
            report_type = TYPE_MAP.get(type_dir.name)
            if not report_type:
                continue

            for fn in sorted(type_dir.iterdir()):
                if not fn.is_file():
                    continue
                if fn.suffix.lower() not in (".pdf", ".html"):
                    continue

                scanned += 1
                filepath = fn  # Path
                full_path = str(filepath)
                year = parse_filename_year(fn.name)
                period = parse_period(fn.name)
                if year == 0:
                    continue

                # 查找/创建报告记录（按 机构+类型+年份+期间 去重）
                record = db.query(IalmdReportRecord).filter(
                    IalmdReportRecord.institution_id == inst_id,
                    IalmdReportRecord.report_type == report_type,
                    IalmdReportRecord.report_year == year,
                    IalmdReportRecord.report_period == period,
                    IalmdReportRecord.is_deleted == 0,
                ).first()

                if not record:
                    record = IalmdReportRecord(
                        institution_id=inst_id,
                        report_type=report_type,
                        report_year=year,
                        report_period=period,
                        report_title=fn.stem,
                        collect_status="PARSED",  # 已采集（文件已下载）
                        collected_at=datetime.now(),
                        source_url=full_path,
                        status=1,
                    )
                    db.add(record)
                    db.flush()
                    added_record += 1

                # 检查文件是否已录入
                exists_file = db.query(IalmdReportFile).filter(
                    IalmdReportFile.report_id == record.id,
                    IalmdReportFile.file_name == fn.name,
                    IalmdReportFile.is_deleted == 0,
                ).first()
                if exists_file:
                    skipped += 1
                    continue

                # 计算文件哈希
                try:
                    size = fn.stat().st_size
                    h = hashlib.sha256()
                    with open(full_path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            h.update(chunk)
                    file_hash = h.hexdigest()
                except Exception:
                    size = 0
                    file_hash = ""

                db.add(IalmdReportFile(
                    report_id=record.id,
                    file_name=fn.name,
                    file_type=fn.suffix.lstrip(".").upper(),
                    file_size=size,
                    file_hash=file_hash,
                    storage_path=full_path,
                    status=1,
                ))
                added_file += 1

    db.commit()
    print(f"  扫描文件: {scanned}")
    print(f"  新增报告记录: {added_record}")
    print(f"  新增报告文件: {added_file}")
    print(f"  跳过(已存在): {skipped}")
    return scanned


def extract_text(filepath):
    """提取 PDF/HTML 文本"""
    ext = filepath.suffix.lower()
    try:
        if ext == ".pdf":
            import pypdf
            text = ""
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
                max_pages = min(len(reader.pages), 60)
                for i in range(max_pages):
                    try:
                        t = reader.pages[i].extract_text()
                        if t:
                            text += t + "\n"
                    except Exception:
                        pass
            return text
        elif ext == ".html":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"&nbsp;", " ", text)
            text = re.sub(r"\s+", " ", text)
            return text
    except Exception:
        pass
    return ""


def match_indicators(text):
    """从文本匹配 20 个保险指标"""
    result = {}
    for code, names in INDICATOR_PATTERNS:
        for name in names:
            escaped = re.escape(name)
            # 匹配：指标名 + 冒号/等号 + 数值（可能带%或单位）
            patterns = [
                rf"{escaped}[：:＝=\s]*([\d,]+\.?\d*)\s*[%％]?",
                rf"{escaped}[^0-9]{{0,10}}([\d,]+\.?\d*)\s*[%％]?",
            ]
            found = False
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    val = m.group(1).replace(",", "")
                    try:
                        fval = float(val)
                        # 合理性检查
                        if 0.0001 <= fval <= 100000000000:
                            result[code] = fval
                            found = True
                    except ValueError:
                        pass
                    break
            if found:
                break
    return result


def extract_indicators(db, bank_map):
    """从报告文件提取指标值"""
    print("=" * 60)
    print("步骤2: 从报告提取保险指标值")
    print("=" * 60)

    # 加载指标定义（编码 → 名称）
    defs = db.query(IalmdIndicatorDefine).filter(IalmdIndicatorDefine.is_deleted == 0).all()
    indicator_names = {d.indicator_code: d.indicator_name for d in defs}

    total_extracted = 0
    files_processed = 0

    # 遍历所有报告文件（优先 PDF）
    report_files = db.query(IalmdReportFile).filter(
        IalmdReportFile.is_deleted == 0,
        IalmdReportFile.file_type == "PDF",
    ).all()

    for rf in report_files:
        # 获取机构代码
        record = db.query(IalmdReportRecord).filter(
            IalmdReportRecord.id == rf.report_id,
            IalmdReportRecord.is_deleted == 0,
        ).first()
        if not record:
            continue

        # 反查机构 bank_code
        inst = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.id == record.institution_id,
        ).first()
        if not inst:
            continue
        bank_code = inst.bank_code

        filepath = Path(rf.storage_path)
        if not filepath.exists():
            continue

        files_processed += 1
        text = extract_text(filepath)
        if not text:
            continue

        indicators = match_indicators(text)
        if not indicators:
            continue

        for code, value in indicators.items():
            # 检查是否已存在（按 编码+机构代码+年份+期间 去重）
            exists = db.query(IalmdIndicatorValue).filter(
                IalmdIndicatorValue.indicator_code == code,
                IalmdIndicatorValue.bank_code == bank_code,
                IalmdIndicatorValue.report_year == record.report_year,
                IalmdIndicatorValue.report_period == record.report_period,
                IalmdIndicatorValue.is_deleted == 0,
            ).first()
            if exists:
                continue

            db.add(IalmdIndicatorValue(
                indicator_code=code,
                bank_code=bank_code,
                indicator_id=defs and next((d.id for d in defs if d.indicator_code == code), None),
                institution_id=inst.id,
                report_id=record.id,
                value_numeric=value,
                value_text=str(value),
                report_year=record.report_year,
                report_period=record.report_period,
                confidence=0.7,
                extract_context=rf.file_name[:200],
                verify_status="PENDING",
                status=1,
            ))
            total_extracted += 1

    db.commit()
    print(f"  处理文件: {files_processed}")
    print(f"  提取指标值: {total_extracted}")
    return total_extracted


def main():
    if not REPORT_DIR.exists():
        print(f"报告目录不存在: {REPORT_DIR}")
        sys.exit(1)

    db = SessionLocal()
    try:
        # 机构映射：bank_name → (id, bank_code)
        bank_map = {}
        for b in db.query(IalmdBankInstitution).filter(IalmdBankInstitution.is_deleted == 0).all():
            bank_map[b.bank_name] = (b.id, b.bank_code)
        print(f"机构映射: {len(bank_map)} 家")

        # 步骤1: 扫描报告 + 录入
        scan_reports(db, bank_map)

        # 步骤2: 指标提取
        extract_indicators(db, bank_map)

        # 汇总
        print("=" * 60)
        print("完成！最终统计:")
        print(f"  报告记录: {db.query(func.count(IalmdReportRecord.id)).filter(IalmdReportRecord.is_deleted == 0).scalar()}")
        print(f"  报告文件: {db.query(func.count(IalmdReportFile.id)).filter(IalmdReportFile.is_deleted == 0).scalar()}")
        print(f"  指标值: {db.query(func.count(IalmdIndicatorValue.id)).filter(IalmdIndicatorValue.is_deleted == 0).scalar()}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
