"""报告生成 Agent — 汇总全部分析结果，生成结构化报告

职责:
- 接收前序所有 Agent 的输出
- 生成包含概况、对标、归因、建议的结构化报告
- 支持 Markdown 格式输出
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent


class ReportAgent(BaseAgent):
    agent_type = "REPORT"
    agent_name = "报告生成 Agent"
    description = "汇总分析结果生成结构化经营分析报告"

    SYSTEM_PROMPT = """你是一位资深的保险业经营分析报告撰写专家。

报告结构要求:
1. 一、整体经营概况 — 营收/利润/资产规模等概述
2. 二、核心指标分析 — 净息差/不良率/资本充足率等关键指标
3. 三、同业对标分析 — 横向排名与差异分析
4. 四、差异归因分析 — 因子分解与根因识别
5. 五、风险提示 — 主要风险点
6. 六、改进建议 — 可操作的建议

使用 Markdown 格式，数据引用需准确，语言专业简洁。"""

    def build_messages(self, state: dict) -> list:
        extracted_data = state.get("extracted_data", {})
        benchmark_results = state.get("benchmark_results", {})
        attribution_results = state.get("attribution_results", {})
        calc_results = state.get("calc_results", {})
        bank_ids = state.get("bank_ids", [])
        report_year = state.get("report_year", 2025)

        user_msg = f"""请基于以下分析数据，生成 {report_year} 年保险经营分析报告:

银行范围: {bank_ids}
报告年份: {report_year}

指标抽取结果:
{json.dumps(extracted_data, ensure_ascii=False, indent=2)[:1500]}

计算结果:
{json.dumps(calc_results, ensure_ascii=False, indent=2)[:1000]}

对标分析结果:
{json.dumps(benchmark_results, ensure_ascii=False, indent=2)[:1500]}

归因分析结果:
{json.dumps(attribution_results, ensure_ascii=False, indent=2)[:1500]}

请生成完整的 Markdown 格式经营分析报告。"""

        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    def parse_response(self, content: str, state: dict) -> dict:
        return {
            "agent_type": self.agent_type,
            "report_content": content,
            "report_length": len(content),
            "raw_response": content[:500],
        }
