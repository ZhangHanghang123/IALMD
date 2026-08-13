"""报告采集 Agent — 从巨潮资讯网采集保险公司经营报告

职责:
- 从数据库读取保险机构（A股上市险企）
- 采集近 10 年的经营报告（年报/半年报/季报/偿付能力/精算/保费公告等）
- 参照银行版目录结构存储：data/保险经营报告下载/{机构名称}/{报告类型}/
- 为后续指标提取提供报告文件

与 BaseAgent 不同：本 Agent 是自动化下载任务，不依赖 LLM。
"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 引入 tools 下载脚本（IALMD/tools/download_insurance_reports.py）
_TOOLS_DIR = Path(__file__).resolve().parents[4] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from download_insurance_reports import (  # noqa: E402
    load_progress, save_progress, process_company,
    BASE_DIR, LOG_FILE, log_message, ensure_dir,
)
from app.database import SessionLocal  # noqa: E402
from app.models import IalmdBankInstitution  # noqa: E402


class CollectAgent:
    """报告采集 Agent"""

    agent_type = "COLLECT"
    agent_name = "报告采集 Agent"
    description = "从巨潮资讯网采集保险公司10年经营报告，参照银行目录结构存储"

    def __init__(self):
        # 报告采集不需要 LLM
        pass

    def execute(self, state: dict | None = None) -> dict:
        """执行报告采集 — 从数据库读取 A 股上市险企并下载报告

        state 可选参数:
          - institution_codes: 指定机构代码列表（bank_code），缺省下载全部 A 股上市险企
          - dry_run: True 时只列出目标机构不实际下载
        """
        state = state or {}
        institution_codes = state.get("institution_codes")
        dry_run = state.get("dry_run", False)

        ensure_dir(BASE_DIR)
        log_message("=" * 60, LOG_FILE)
        log_message("报告采集 Agent 启动", LOG_FILE)
        log_message(f"输出目录: {BASE_DIR}", LOG_FILE)
        log_message("=" * 60, LOG_FILE)

        progress = load_progress()
        db = SessionLocal()
        summary = {"total": 0, "downloaded": 0, "skipped": 0, "failed": 0, "errors": []}

        try:
            query = db.query(IalmdBankInstitution).filter(
                IalmdBankInstitution.is_deleted == 0,
                IalmdBankInstitution.status == 1,
            )
            if institution_codes:
                query = query.filter(IalmdBankInstitution.bank_code.in_(institution_codes))

            companies = query.order_by(IalmdBankInstitution.id).all()
            a_share = [c for c in companies
                       if (c.listing_market or "") in ("A", "A+H") and c.stock_code]

            log_message(f"目标机构: {len(companies)} 家，其中 A 股上市险企 {len(a_share)} 家", LOG_FILE)
            summary["total"] = len(a_share)

            for company in a_share:
                if dry_run:
                    log_message(f"  [DRY-RUN] {company.bank_name} ({company.bank_code} / {company.stock_code})", LOG_FILE)
                    continue
                try:
                    before = len(progress["downloaded"])
                    process_company(company, progress)
                    after = len(progress["downloaded"])
                    summary["downloaded"] += max(0, after - before)
                except Exception as e:
                    summary["errors"].append({"company": company.bank_name, "error": str(e)[:200]})
                    logger.error(f"[COLLECT] 采集 {company.bank_name} 失败: {e}")

            save_progress(progress)
            summary["skipped"] = len(progress.get("skipped", []))
            summary["failed"] = len(progress.get("failed", []))

            log_message(f"报告采集完成：目标{summary['total']}家，成功{summary['downloaded']}，失败{summary['failed']}", LOG_FILE)
            return {
                "agent_type": self.agent_type,
                "agent_name": self.agent_name,
                "summary": summary,
                "output_dir": str(BASE_DIR),
            }

        finally:
            db.close()
