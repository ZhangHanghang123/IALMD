"""指标抽取 Agent — 从银行报告中提取结构化经营指标

职责:
- 接收报告年份、银行列表、目标指标
- 通过 LLM 从年报/半年报文本中抽取指标值
- 返回结构化指标数据 (指标名/值/单位/年份)
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent


class ExtractAgent(BaseAgent):
    agent_type = "EXTRACT"
    agent_name = "指标抽取 Agent"
    description = "从银行公开报告中提取经营指标数据"

    SYSTEM_PROMPT = """你是一位专业的保险业分析师，擅长从银行年报、半年报、季报中提取经营指标数据。

任务要求:
1. 从给定银行报告中提取以下类型的指标数据
2. 每个指标需包含: 指标名称、数值、单位、年份、数据来源
3. 如果某指标在报告中未披露，标注为 null
4. 置信度评估: 对每个抽取结果的准确度打分 (0-1)

输出格式: JSON，包含 indicators 数组，每个元素结构如下:
{
  "name": "指标名称",
  "code": "指标编码",
  "value": 数值,
  "unit": "单位",
  "year": 年份,
  "source": "数据来源页码",
  "confidence": 置信度
}"""

    def build_messages(self, state: dict) -> list:
        bank_ids = state.get("bank_ids", [])
        report_year = state.get("report_year", 2025)
        report_period = state.get("report_period", "FY")
        indicator_codes = state.get("indicator_codes", [])

        user_msg = f"""请从以下银行的 {report_year} 年 {report_period} 报告中提取经营指标:

目标银行ID: {bank_ids}
报告年份: {report_year}
报告周期: {report_period}
目标指标编码: {indicator_codes if indicator_codes else '全部可用指标'}

请返回 JSON 格式的指标抽取结果。"""

        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    def parse_response(self, content: str, state: dict) -> dict:
        parsed = self._safe_json_parse(content)
        return {
            "agent_type": self.agent_type,
            "indicators": parsed.get("indicators", []),
            "total_count": len(parsed.get("indicators", [])),
            "raw_response": content[:500],
        }
