"""差异归因 Agent — 指标变动的因子分解与根因分析

职责:
- 接收指标变动数据（同比/对标差异）
- 执行因子分解（如净息差 = 资产收益率 - 负债成本率）
- 量化各因子贡献度（BP 影响）
- 识别根因并给出建议
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent


class AttributeAgent(BaseAgent):
    agent_type = "ATTRIBUTE"
    agent_name = "差异归因 Agent"
    description = "指标变动因子分解与根因分析"

    SYSTEM_PROMPT = """你是一位保险业经营归因分析专家，擅长将指标变动分解为可量化的驱动因子。

归因分析方法:
1. 净息差分解: 资产规模变动 + 收益率变动 + 负债成本变动 + 结构变动
2. ROE分解 (杜邦): ROE = 净利率 × 资产周转率 × 权益乘数
3. 不良率变动: 新增不良 + 核销处置 + 贷款规模变动
4. 利润变动: 息差贡献 + 规模贡献 + 中收贡献 + 减值贡献

每个因子需量化影响方向和幅度(BP或百分比)。

输出格式: JSON:
{
  "target_indicator": "目标指标名称",
  "total_change": 总变动值,
  "total_change_bp": 总变动BP,
  "decomposition": [
    {
      "factor": "因子名称",
      "impact": 影响值,
      "impact_bp": 影响BP,
      "direction": "positive/negative",
      "explanation": "因子解释"
    }
  ],
  "root_cause": "根因分析",
  "recommendation": "改进建议"
}"""

    def build_messages(self, state: dict) -> list:
        benchmark_results = state.get("benchmark_results", {})
        extracted_data = state.get("extracted_data", {})
        indicator_codes = state.get("indicator_codes", [])

        user_msg = f"""对以下指标差异进行归因分析:

目标指标: {indicator_codes if indicator_codes else '净息差'}

对标分析结果:
{json.dumps(benchmark_results, ensure_ascii=False, indent=2)[:2000]}

原始指标数据:
{json.dumps(extracted_data, ensure_ascii=False, indent=2)[:1000]}

请执行因子分解归因分析，返回 JSON 结果。"""

        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    def parse_response(self, content: str, state: dict) -> dict:
        parsed = self._safe_json_parse(content)
        return {
            "agent_type": self.agent_type,
            "decomposition": parsed.get("decomposition", []),
            "root_cause": parsed.get("root_cause", ""),
            "recommendation": parsed.get("recommendation", ""),
            "total_change_bp": parsed.get("total_change_bp", 0),
            "raw_response": content[:500],
        }
