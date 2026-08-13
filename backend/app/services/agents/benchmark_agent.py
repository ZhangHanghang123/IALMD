"""对标分析 Agent — 跨银行指标排名与对比

职责:
- 接收多银行的同一指标值
- 计算排名、均值、标准差、分位数
- 识别领先/落后银行
- 返回对标结果
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from .base import BaseAgent


class BenchmarkAgent(BaseAgent):
    agent_type = "BENCHMARK"
    agent_name = "对标分析 Agent"
    description = "跨银行指标排名与对比分析"

    SYSTEM_PROMPT = """你是一位保险业同业对标分析专家。

分析要求:
1. 对各银行同一指标进行排名
2. 计算行业均值、中位数、标准差
3. 识别领先者（前25%）和落后者（后25%）
4. 分析指标差异的可能原因
5. 提供分位数分布（P25/P50/P75）

输出格式: JSON:
{
  "rankings": [{"bank": "银行名", "value": 值, "rank": 排名, "percentile": 分位数}],
  "statistics": {"mean": 均值, "median": 中位数, "std_dev": 标准差, "max": 最大值, "min": 最小值},
  "leaders": ["领先银行列表"],
  "laggards": ["落后银行列表"],
  "analysis": "差异原因分析"
}"""

    def build_messages(self, state: dict) -> list:
        extracted_data = state.get("extracted_data", {})
        calc_results = state.get("calc_results", {})
        bank_ids = state.get("bank_ids", [])
        indicator_codes = state.get("indicator_codes", [])

        user_msg = f"""对以下银行进行同业对标分析:

银行ID列表: {bank_ids}
目标指标: {indicator_codes if indicator_codes else '全部指标'}

已抽取指标数据:
{json.dumps(extracted_data, ensure_ascii=False, indent=2)[:2000]}

计算结果:
{json.dumps(calc_results, ensure_ascii=False, indent=2)[:2000]}

请返回对标分析结果 JSON。"""

        return [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]

    def parse_response(self, content: str, state: dict) -> dict:
        parsed = self._safe_json_parse(content)
        return {
            "agent_type": self.agent_type,
            "rankings": parsed.get("rankings", []),
            "statistics": parsed.get("statistics", {}),
            "leaders": parsed.get("leaders", []),
            "laggards": parsed.get("laggards", []),
            "analysis": parsed.get("analysis", ""),
            "raw_response": content[:500],
        }
