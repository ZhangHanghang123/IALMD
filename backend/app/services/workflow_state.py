"""工作流状态定义 — LangGraph StateGraph 的共享状态

所有 Agent 节点共享此状态，每个节点读取上游数据并写入自己的产出
"""
from typing import TypedDict, Any
from langgraph.graph import MessagesState


class WorkflowState(MessagesState):
    """工作流执行状态（继承 MessagesState 自动管理消息历史）

    核心字段说明:
    - workflow_id: 工作流定义ID
    - exec_id: 当前执行记录ID
    - node_id: 当前节点ID
    - bank_ids: 目标银行ID列表
    - report_year: 报告年份
    - report_period: 报告周期 (FY/H1/Q1/Q3)
    - indicator_codes: 目标指标编码列表
    - extracted_data: 指标抽取结果（EXTRACT Agent 产出）
    - calc_results: 指标计算结果（CALC Agent 产出）
    - benchmark_results: 对标分析结果（BENCHMARK Agent 产出）
    - attribution_results: 归因分析结果（ATTRIBUTE Agent 产出）
    - report_content: 最终报告内容（REPORT Agent 产出）
    - node_outputs: 各节点输出汇总 {node_id: output}
    - errors: 执行错误列表
    """
    # 输入参数
    workflow_id: int
    exec_id: int
    node_id: str
    bank_ids: list[int]
    report_year: int
    report_period: str
    indicator_codes: list[str]

    # 各阶段产出
    extracted_data: dict[str, Any]
    calc_results: dict[str, Any]
    benchmark_results: dict[str, Any]
    attribution_results: dict[str, Any]
    report_content: str

    # 全局汇总
    node_outputs: dict[str, Any]
    errors: list[str]
