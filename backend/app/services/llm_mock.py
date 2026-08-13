"""模拟 LLM — 无 API Key 时的兜底实现，返回保险经营分析的预置响应"""
import json
import asyncio
import logging
from typing import Any, AsyncIterator, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

logger = logging.getLogger(__name__)


class MockChatModel(BaseChatModel):
    """模拟 LLM — 无 API Key 时的兜底实现，返回保险经营分析的预置响应"""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager=None,
        **kwargs,
    ) -> ChatResult:
        system_msg = ""
        user_msg = ""
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            if m.type == "system":
                system_msg = content
            elif m.type == "human":
                user_msg = content

        mock_content = self._build_mock_response(system_msg, user_msg)
        message = AIMessage(content=mock_content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager=None,
        **kwargs,
    ) -> AsyncIterator[AIMessage]:
        """异步流式输出 — mock 模式专用，避免 BaseChatModel 默认实现阻塞事件循环"""
        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        full_text = result.generations[0].message.content
        # 按 20 字符一块输出，模拟流式效果
        chunk_size = 20
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i + chunk_size]
            yield AIMessage(content=chunk)
            await asyncio.sleep(0.02)

    def _build_mock_response(self, system_msg: str, user_msg: str) -> str:
        s = system_msg

        # 1. EXTRACT Agent
        if ("抽取" in s or "提取" in s) and "指标" in s:
            return json.dumps({
                "status": "success",
                "indicators": [
                    {"name": "营业收入", "code": "REVENUE", "value": 8564.39, "unit": "亿元", "year": 2025, "confidence": 0.98},
                    {"name": "净利润", "code": "NET_PROFIT", "value": 3651.16, "unit": "亿元", "year": 2025, "confidence": 0.98},
                    {"name": "净息差", "code": "NIM", "value": 1.38, "unit": "%", "year": 2025, "confidence": 0.95},
                    {"name": "不良贷款率", "code": "NPL", "value": 1.32, "unit": "%", "year": 2025, "confidence": 0.96},
                    {"name": "资本充足率", "code": "CAR", "value": 19.10, "unit": "%", "year": 2025, "confidence": 0.97},
                    {"name": "拨备覆盖率", "code": "PCR", "value": 220.50, "unit": "%", "year": 2025, "confidence": 0.94},
                ],
                "total_count": 6,
            }, ensure_ascii=False)

        # 2. REPORT Agent (必须在 BENCHMARK 之前)
        if "报告撰写" in s or "报告生成" in s:
            return """## 保险经营分析报告

### 一、整体经营概况
2025年，六大行整体经营稳健，营业收入合计5.2万亿元，同比增长3.2%。净利润保持正增长，但增速放缓至2.1%。

### 二、核心指标分析
- **净息差**: 均值1.413%，较上年下降15BP，主要受LPR下行影响
- **不良贷款率**: 均值1.34%，较年初下降2BP，资产质量稳中向好
- **资本充足率**: 均值18.5%，远高于监管最低要求，资本缓冲充足
- **拨备覆盖率**: 均值215%，风险抵补能力较强

### 三、同业对标分析
邮储银行净息差1.65%领先同业，主要受益于零售业务优势；交通银行1.28%排名末位，对公业务占比偏高。

### 四、差异归因分析
净息差收窄17BP的分解:
- 生息资产收益率变动: -12BP（主因）
- 计息负债成本变动: -8BP
- 资产规模变动: +5BP
- 结构变动: -2BP

### 五、风险提示
1. LPR持续下行可能进一步压缩息差
2. 房地产领域不良暴露需持续关注
3. 理财净值化转型压力

### 六、改进建议
1. 优化资产负债结构，稳定净息差
2. 加强重点领域风险管控
3. 提升非息收入占比，增强盈利韧性"""

        # 3. BENCHMARK Agent
        if "对标分析" in s and "专家" in s:
            return json.dumps({
                "status": "success",
                "rankings": [
                    {"bank": "邮储银行", "value": 1.65, "rank": 1, "percentile": 100},
                    {"bank": "建设银行", "value": 1.42, "rank": 2, "percentile": 80},
                    {"bank": "中国银行", "value": 1.40, "rank": 3, "percentile": 60},
                    {"bank": "工商银行", "value": 1.38, "rank": 4, "percentile": 40},
                    {"bank": "农业银行", "value": 1.35, "rank": 5, "percentile": 20},
                    {"bank": "交通银行", "value": 1.28, "rank": 6, "percentile": 0},
                ],
                "statistics": {"mean": 1.413, "median": 1.39, "std_dev": 0.121, "max": 1.65, "min": 1.28},
                "leaders": ["邮储银行", "建设银行"],
                "laggards": ["交通银行", "农业银行"],
                "analysis": "邮储银行凭借零售业务优势净息差领先；交通银行受对公业务占比高影响净息差偏低",
            }, ensure_ascii=False)

        # 4. ATTRIBUTE Agent
        if "归因分析" in s and "专家" in s:
            return json.dumps({
                "status": "success",
                "target_indicator": "净息差",
                "total_change": -0.17,
                "total_change_bp": -17,
                "decomposition": [
                    {"factor": "生息资产规模变动", "impact": 0.05, "impact_bp": 5, "direction": "positive", "explanation": "资产规模扩张带来正向贡献"},
                    {"factor": "生息资产收益率变动", "impact": -0.12, "impact_bp": -12, "direction": "negative", "explanation": "LPR下行导致贷款收益率下降"},
                    {"factor": "计息负债成本变动", "impact": -0.08, "impact_bp": -8, "direction": "negative", "explanation": "存款成本刚性，降幅小于资产端"},
                    {"factor": "资产负债结构变动", "impact": -0.02, "impact_bp": -2, "direction": "negative", "explanation": "低收益资产占比提升"},
                ],
                "root_cause": "LPR下行导致贷款收益率下降12BP，而存款成本仅下降3BP，息差收窄主要来自资产端收益率下行",
                "recommendation": "1. 优化信贷结构，提升高收益资产占比；2. 加强负债成本管控，压降高成本存款；3. 提升非息收入占比",
            }, ensure_ascii=False)

        # 5. CALC Agent
        if "财务分析" in s or ("计算" in s and "衍生" in s):
            return json.dumps({
                "status": "success",
                "calc_results": [
                    {"name": "ROE", "code": "ROE", "value": 11.52, "formula": "净利润/净资产×100%", "inputs": ["净利润", "净资产"], "year": 2025},
                    {"name": "ROA", "code": "ROA", "value": 0.92, "formula": "净利润/总资产×100%", "inputs": ["净利润", "总资产"], "year": 2025},
                    {"name": "成本收入比", "code": "CIR", "value": 28.5, "formula": "管理费/营业收入×100%", "inputs": ["管理费", "营业收入"], "year": 2025},
                    {"name": "拨备覆盖率", "code": "PCR", "value": 220.5, "formula": "减值准备/不良贷款×100%", "inputs": ["减值准备", "不良贷款"], "year": 2025},
                ],
            }, ensure_ascii=False)

        # Default
        return json.dumps({
            "status": "success",
            "message": "模拟分析完成",
            "data": {"processed": True, "items": 5},
        }, ensure_ascii=False)

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        """兼容 bind_tools 调用"""
        return self
