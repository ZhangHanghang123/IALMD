# -*- coding: utf-8 -*-
"""
初始化报告采集记录（ialmd_bank_report_link）

从已有的 report_record/report_file 生成"采集记录"页签数据，
并关联指标提取结果（extraction_status / extracted_count）。

用法：cd backend && python ../scripts/init_report_links.py
"""
import sys
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models import (
    IalmdReportRecord, IalmdReportFile, IalmdBankReportLink,
    IalmdIndicatorValue, IalmdBankInstitution,
)
from sqlalchemy import func

db = SessionLocal()


def main():
    print("=" * 60)
    print("初始化报告采集记录（bank_report_link）")
    print("=" * 60)

    # 机构映射：id -> bank_code
    inst_map = {}
    for b in db.query(IalmdBankInstitution).filter(IalmdBankInstitution.is_deleted == 0).all():
        inst_map[b.id] = b.bank_code

    # 读取所有报告记录
    records = db.query(IalmdReportRecord).filter(
        IalmdReportRecord.is_deleted == 0,
    ).order_by(IalmdReportRecord.id).all()
    print(f"报告记录: {len(records)} 条")

    added = 0
    skipped = 0
    done_count = 0

    for rec in records:
        bank_code = inst_map.get(rec.institution_id, "")
        if not bank_code:
            continue

        # 查重（机构+类型+年份+期间）
        exists = db.query(IalmdBankReportLink).filter(
            IalmdBankReportLink.institution_id == rec.institution_id,
            IalmdBankReportLink.report_type == rec.report_type,
            IalmdBankReportLink.report_year == rec.report_year,
            IalmdBankReportLink.report_period == rec.report_period,
            IalmdBankReportLink.is_deleted == 0,
        ).first()
        if exists:
            skipped += 1
            continue

        # 取该报告的第一个文件信息
        f = db.query(IalmdReportFile).filter(
            IalmdReportFile.report_id == rec.id,
            IalmdReportFile.is_deleted == 0,
        ).first()

        # 统计该机构+年份+期间的指标值数量
        extracted_count = db.query(func.count(IalmdIndicatorValue.id)).filter(
            IalmdIndicatorValue.bank_code == bank_code,
            IalmdIndicatorValue.report_year == rec.report_year,
            IalmdIndicatorValue.report_period == rec.report_period,
            IalmdIndicatorValue.is_deleted == 0,
        ).scalar() or 0

        extraction_status = "DONE" if extracted_count > 0 else "PENDING"
        if extracted_count > 0:
            done_count += 1

        db.add(IalmdBankReportLink(
            institution_id=rec.institution_id,
            bank_code=bank_code,
            report_type=rec.report_type,
            report_year=rec.report_year,
            report_period=rec.report_period,
            file_format=(f.file_type if f else ""),
            file_name=(f.file_name if f else rec.report_title),
            file_path=(f.storage_path if f else rec.source_url),
            file_size=(f.file_size if f else 0),
            file_hash=(f.file_hash if f else ""),
            exists_flag=1,
            extraction_status=extraction_status,
            extracted_count=extracted_count,
            last_extracted_at=datetime.now() if extracted_count > 0 else None,
            scan_time=datetime.now(),
        ))
        added += 1

    db.commit()

    total = db.query(func.count(IalmdBankReportLink.id)).filter(
        IalmdBankReportLink.is_deleted == 0,
    ).scalar()

    print(f"  新增采集记录: {added}")
    print(f"  跳过(已存在): {skipped}")
    print(f"  已提取指标: {done_count} 条记录")
    print(f"  采集记录总数: {total}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
