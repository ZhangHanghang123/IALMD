"""工作流 Pydantic Schemas"""
from pydantic import BaseModel
from typing import Any


class NodeDef(BaseModel):
    """节点定义"""
    id: str
    type: str  # EXTRACT | CALC | BENCHMARK | ATTRIBUTE | REPORT
    label: str = ""
    config: dict[str, Any] = {}


class EdgeDef(BaseModel):
    """边定义"""
    source: str
    target: str
    condition: str | None = None


class WorkflowDAG(BaseModel):
    """工作流 DAG 图"""
    nodes: list[NodeDef] = []
    edges: list[EdgeDef] = []


class WorkflowCreate(BaseModel):
    """创建工作流"""
    workflow_name: str
    workflow_code: str
    description: str | None = None
    node_json: WorkflowDAG
    trigger_type: str = "MANUAL"
    cron_expr: str = ""


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    workflow_name: str | None = None
    description: str | None = None
    node_json: WorkflowDAG | None = None
    trigger_type: str | None = None
    cron_expr: str | None = None
    status: int | None = None


class WorkflowExecRequest(BaseModel):
    """执行工作流请求"""
    bank_ids: list[int] = [1, 2, 3, 4, 5, 6]
    report_year: int = 2025
    report_period: str = "FY"
    indicator_codes: list[str] = []


class WorkflowOut(BaseModel):
    """工作流输出"""
    id: int
    workflow_name: str
    workflow_code: str
    description: str | None = None
    node_json: Any = None
    trigger_type: str = "MANUAL"
    cron_expr: str = ""
    status: int = 1
    created_at: str | None = None
    updated_at: str | None = None


class WorkflowExecOut(BaseModel):
    """工作流执行记录输出"""
    id: int
    workflow_id: int
    exec_status: str
    input_json: Any = None
    output_json: Any = None
    error_msg: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    triggered_by: int | None = None


class NodeExecOut(BaseModel):
    """节点执行记录输出"""
    id: int
    exec_id: int
    node_id: str
    node_type: str
    agent_type: str
    exec_status: str
    input_json: Any = None
    output_json: Any = None
    error_msg: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
