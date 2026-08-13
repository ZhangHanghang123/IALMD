"""指标计算 Agent — 基于原始指标计算衍生指标

职责:
- 接收抽取的原始指标数据
- 计算衍生指标（如 ROE=净利润/净资产）
- 执行同比/环比变化计算
- 返回计算结果集
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent


class CalcAgent(BaseAgent):
    agent_type = "CALC"
    agent_name = "指标计算 Agent"
    description = "基于原始指标计算衍生指标和变化率"

    SYSTEM_PROMPT = """你是一位保险业财务分析专家，擅长计算保险经营衍生指标。

计算规则:
1. ROE = 净利润 / 净资产 × 100%
2. ROA = 净利润 / 总资产 × 100%
3. 成本收入比 = 业务及管理费 / 营业收入 × 100%
4. 拨备覆盖率 = 贷款减值准备 / 不良贷款 × 100%
5. 同比增长率 = (本期值 - 上期值) / 上期值 × 100%
6. 净息差 = 利息净收入 / 生息资产平均余额 × 100%

输出格式: JSON，包含 calc_results 数组:
{
  "name": "衍生指标名称",
  "code": "指标编码",
  "value": 计算值,
  "formula": "计算公式",
  "inputs": ["输入指标1", "输入指标2"],
  "year": 年份
}"""

    def build_messages(self, state: dict) -> list:
        extracted_data = state.get("extracted_data", {})

        user_msg = f"""基于以下已抽取的原始指标，计算衍生指标:

原始指标数据:
{json.dumps(extracted_data, ensure_ascii=False, indent=2)}

请计算所有可计算的衍生指标，并返回 JSON 结果。"""

        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    def parse_response(self, content: str, state: dict) -> dict:
        parsed = self._safe_json_parse(content)
        return {
            "agent_type": self.agent_type,
            "calc_results": parsed.get("calc_results", []),
            "total_count": len(parsed.get("calc_results", [])),
            "raw_response": content[:500],
        }
