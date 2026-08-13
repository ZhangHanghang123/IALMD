"""Agent 节点基类 — 所有 Agent 的公共逻辑

每个 Agent 是 LangGraph 的一个 node function:
- 输入: WorkflowState
- 输出: 更新后的 state dict
- 使用 LangChain 的 prompt + LLM 链进行推理
"""
import json
import logging
from datetime import datetime
from typing import Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from ..llm_factory import get_llm

logger = logging.getLogger(__name__)


class BaseAgent:
    """Agent 基类"""

    agent_type: str = "BASE"
    agent_name: str = "基础 Agent"
    description: str = ""

    def __init__(self):
        self.llm = get_llm()

    def build_messages(self, state: dict) -> list:
        """构建 LLM 消息列表 — 子类实现"""
        raise NotImplementedError

    def parse_response(self, content: str, state: dict) -> dict:
        """解析 LLM 返回内容 — 子类实现"""
        raise NotImplementedError

    def execute(self, state: dict) -> dict:
        """执行 Agent 逻辑 — LangGraph node 入口

        1. 构建 prompt
        2. 调用 LLM
        3. 解析响应
        4. 返回状态更新
        """
        node_id = state.get("node_id", "unknown")
        logger.info(f"[{self.agent_type}] 节点 {node_id} 开始执行")

        try:
            messages = self.build_messages(state)
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            parsed = self.parse_response(content, state)

            # 记录到 node_outputs
            node_outputs = state.get("node_outputs", {})
            node_outputs[node_id] = {
                "agent_type": self.agent_type,
                "agent_name": self.agent_name,
                "output": parsed,
                "executed_at": datetime.now().isoformat(),
            }

            logger.info(f"[{self.agent_type}] 节点 {node_id} 执行完成")
            return {"node_outputs": node_outputs}

        except Exception as e:
            logger.error(f"[{self.agent_type}] 节点 {node_id} 执行失败: {e}")
            errors = state.get("errors", [])
            errors.append(f"{self.agent_type}/{node_id}: {str(e)}")
            return {"errors": errors}

    def _safe_json_parse(self, content: str) -> dict:
        """安全解析 JSON，支持 LLM 返回非纯 JSON 的情况"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            return json.loads(content[start:end].strip())

        # 尝试提取第一个 { ... } 块
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            return json.loads(content[start:end + 1])

        return {"raw_content": content, "parse_error": True}
