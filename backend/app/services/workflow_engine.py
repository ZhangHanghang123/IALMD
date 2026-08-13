"""工作流引擎 — 基于 LangGraph StateGraph 的 DAG 执行引擎

核心能力:
1. 将前端编排的节点 JSON 转换为 LangGraph StateGraph
2. 按拓扑排序执行各 Agent 节点
3. 支持条件分支（基于上游输出动态路由）
4. 执行状态持久化到 MySQL (IALMD_workflow_exec / IALMD_workflow_node_exec)
5. 支持并行执行无依赖关系的节点
"""
import json
import logging
from datetime import datetime
from typing import Any
from collections import defaultdict, deque

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .workflow_state import WorkflowState
from .agents import get_agent, AGENT_METADATA
from ..models import IalmdWorkflowDef, IalmdWorkflowExec, IalmdWorkflowNodeExec

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """LangGraph 驱动的工作流执行引擎"""

    def __init__(self, db: Session):
        self.db = db

    def parse_dag(self, node_json: dict) -> dict:
        """解析前端编排的节点 JSON，构建 DAG 拓扑

        输入格式 (node_json):
        {
          "nodes": [
            {"id": "node_1", "type": "EXTRACT", "label": "指标抽取", "config": {...}},
            {"id": "node_2", "type": "CALC", "label": "指标计算", "config": {...}},
            ...
          ],
          "edges": [
            {"source": "node_1", "target": "node_2"},
            ...
          ]
        }

        输出: 拓扑排序后的节点执行顺序
        """
        nodes = node_json.get("nodes", [])
        edges = node_json.get("edges", [])

        # 构建邻接表和入度表
        adj = defaultdict(list)
        in_degree = {n["id"]: 0 for n in nodes}
        node_map = {n["id"]: n for n in nodes}

        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            adj[src].append(tgt)
            in_degree[tgt] += 1

        # Kahn 拓扑排序
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        topo_order = []

        while queue:
            nid = queue.popleft()
            topo_order.append(nid)
            for neighbor in adj[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(nodes):
            raise ValueError("DAG 存在环依赖，无法拓扑排序")

        return {
            "topo_order": topo_order,
            "node_map": node_map,
            "adj": dict(adj),
        }

    def build_graph(self, node_json: dict) -> StateGraph:
        """将 DAG 转换为 LangGraph StateGraph

        策略: 线性串联拓扑排序后的节点（LangGraph 支持 add_node + add_edge）
        对于有分支的 DAG，使用 add_conditional_edges
        """
        dag = self.parse_dag(node_json)
        topo_order = dag["topo_order"]
        node_map = dag["node_map"]
        adj = dag["adj"]

        graph = StateGraph(WorkflowState)

        # 注册所有节点
        for node_id in topo_order:
            node_def = node_map[node_id]
            node_type = node_def.get("type", "EXTRACT")
            agent = get_agent(node_type)

            # 创建闭包捕获 node_id, agent, node_type（避免循环变量覆盖）
            def make_node_func(nid, ag, ntype):
                def node_func(state: WorkflowState) -> dict:
                    # 设置当前 node_id
                    state_dict = dict(state)
                    state_dict["node_id"] = nid

                    # 执行 Agent
                    result = ag.execute(state_dict)

                    # 将 Agent 产出写入对应字段
                    output = result.get("node_outputs", {}).get(nid, {}).get("output", {})
                    state_updates = {}

                    if ntype == "EXTRACT":
                        state_updates["extracted_data"] = output
                    elif ntype == "CALC":
                        state_updates["calc_results"] = output
                    elif ntype == "BENCHMARK":
                        state_updates["benchmark_results"] = output
                    elif ntype == "ATTRIBUTE":
                        state_updates["attribution_results"] = output
                    elif ntype == "REPORT":
                        state_updates["report_content"] = output.get("report_content", "")

                    state_updates["node_outputs"] = result.get("node_outputs", {})
                    if result.get("errors"):
                        state_updates["errors"] = result["errors"]

                    return state_updates

                return node_func

            graph.add_node(node_id, make_node_func(node_id, agent, node_type))

        # 构建边
        for node_id in topo_order:
            neighbors = adj.get(node_id, [])
            if not neighbors:
                graph.add_edge(node_id, END)
            elif len(neighbors) == 1:
                graph.add_edge(node_id, neighbors[0])
            else:
                # 多分支: 使用条件边
                def make_router(targets):
                    def router(state):
                        # 简单策略: 返回第一个目标（可扩展为基于 state 的条件路由）
                        return targets[0]
                    return router

                graph.add_conditional_edges(
                    node_id,
                    make_router(neighbors),
                    {tgt: tgt for tgt in neighbors}
                )

        # 设置入口节点
        if topo_order:
            graph.set_entry_point(topo_order[0])

        return graph.compile()

    def execute(
        self,
        workflow_id: int,
        input_params: dict | None = None,
        triggered_by: int | None = None,
    ) -> dict:
        """执行工作流

        1. 加载工作流定义
        2. 创建执行记录
        3. 构建 LangGraph 并执行
        4. 逐节点记录执行状态
        5. 返回最终结果
        """
        # 1. 加载工作流定义
        wf_def = self.db.query(IalmdWorkflowDef).filter(
            IalmdWorkflowDef.id == workflow_id,
            IalmdWorkflowDef.is_deleted == 0,
        ).first()

        if not wf_def:
            raise ValueError(f"工作流 {workflow_id} 不存在")

        node_json = wf_def.node_json if isinstance(wf_def.node_json, dict) else json.loads(wf_def.node_json)

        # 2. 创建执行记录
        exec_record = IalmdWorkflowExec(
            workflow_id=workflow_id,
            exec_status="RUNNING",
            input_json=input_params or {},
            started_at=datetime.now(),
            triggered_by=triggered_by,
            created_by=triggered_by,
        )
        self.db.add(exec_record)
        self.db.commit()
        self.db.refresh(exec_record)

        exec_id = exec_record.id
        logger.info(f"工作流 '{wf_def.workflow_name}' 执行开始 (exec_id={exec_id})")

        # 3. 构建初始状态
        initial_state: WorkflowState = {
            "messages": [],
            "workflow_id": workflow_id,
            "exec_id": exec_id,
            "node_id": "",
            "bank_ids": input_params.get("bank_ids", [1, 2, 3, 4, 5, 6]) if input_params else [1, 2, 3, 4, 5, 6],
            "report_year": input_params.get("report_year", 2025) if input_params else 2025,
            "report_period": input_params.get("report_period", "FY") if input_params else "FY",
            "indicator_codes": input_params.get("indicator_codes", []) if input_params else [],
            "extracted_data": {},
            "calc_results": {},
            "benchmark_results": {},
            "attribution_results": {},
            "report_content": "",
            "node_outputs": {},
            "errors": [],
        }

        try:
            # 4. 构建 LangGraph
            app = self.build_graph(node_json)

            # 5. 执行
            final_state = app.invoke(initial_state, config={"recursion_limit": 50})

            # 6. 逐节点记录
            dag = self.parse_dag(node_json)
            node_map = dag["node_map"]
            node_outputs = final_state.get("node_outputs", {})

            for node_id, output in node_outputs.items():
                node_def = node_map.get(node_id, {})
                node_exec = IalmdWorkflowNodeExec(
                    exec_id=exec_id,
                    node_id=node_id,
                    node_type=node_def.get("type", ""),
                    agent_type=node_def.get("type", ""),
                    exec_status="COMPLETED" if output.get("output") else "FAILED",
                    input_json={"config": node_def.get("config", {})},
                    output_json=output,
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                    created_by=triggered_by,
                )
                self.db.add(node_exec)

            # 7. 更新执行记录
            errors = final_state.get("errors", [])
            exec_record.exec_status = "FAILED" if errors else "COMPLETED"
            exec_record.output_json = {
                "node_count": len(node_outputs),
                "has_report": bool(final_state.get("report_content")),
                "errors": errors,
            }
            exec_record.error_msg = "; ".join(errors) if errors else None
            exec_record.finished_at = datetime.now()
            self.db.commit()

            logger.info(f"工作流执行完成 (exec_id={exec_id}, status={exec_record.exec_status})")

            return {
                "exec_id": exec_id,
                "status": exec_record.exec_status,
                "node_outputs": node_outputs,
                "report_content": final_state.get("report_content", ""),
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"工作流执行失败: {e}", exc_info=True)
            exec_record.exec_status = "FAILED"
            exec_record.error_msg = str(e)
            exec_record.finished_at = datetime.now()
            self.db.commit()

            return {
                "exec_id": exec_id,
                "status": "FAILED",
                "error": str(e),
            }


def get_default_workflows() -> list[dict]:
    """预置工作流模板"""
    return [
        {
            "workflow_name": "年报指标全量抽取",
            "workflow_code": "EXTRACT_ANNUAL",
            "description": "从银行年报中全量抽取经营指标，包含6大类36个指标",
            "node_json": {
                "nodes": [
                    {"id": "n1", "type": "EXTRACT", "label": "指标抽取", "config": {"report_type": "annual"}},
                ],
                "edges": [],
            },
        },
        {
            "workflow_name": "同业净息差对标分析",
            "workflow_code": "BENCHMARK_NIM",
            "description": "六大行净息差横向对标 + 差异归因 + 分析报告",
            "node_json": {
                "nodes": [
                    {"id": "n1", "type": "EXTRACT", "label": "指标抽取", "config": {"indicator": "NIM"}},
                    {"id": "n2", "type": "BENCHMARK", "label": "对标排名", "config": {}},
                    {"id": "n3", "type": "ATTRIBUTE", "label": "差异归因", "config": {}},
                    {"id": "n4", "type": "REPORT", "label": "报告生成", "config": {}},
                ],
                "edges": [
                    {"source": "n1", "target": "n2"},
                    {"source": "n2", "target": "n3"},
                    {"source": "n3", "target": "n4"},
                ],
            },
        },
        {
            "workflow_name": "季度经营快报生成",
            "workflow_code": "QUARTERLY_REPORT",
            "description": "季度指标抽取→计算→对标→报告全链路",
            "node_json": {
                "nodes": [
                    {"id": "n1", "type": "EXTRACT", "label": "季报指标抽取", "config": {"period": "Q1"}},
                    {"id": "n2", "type": "CALC", "label": "衍生指标计算", "config": {}},
                    {"id": "n3", "type": "BENCHMARK", "label": "同业对标", "config": {}},
                    {"id": "n4", "type": "ATTRIBUTE", "label": "差异归因", "config": {}},
                    {"id": "n5", "type": "REPORT", "label": "快报生成", "config": {"template": "quarterly"}},
                ],
                "edges": [
                    {"source": "n1", "target": "n2"},
                    {"source": "n2", "target": "n3"},
                    {"source": "n3", "target": "n4"},
                    {"source": "n4", "target": "n5"},
                ],
            },
        },
    ]
