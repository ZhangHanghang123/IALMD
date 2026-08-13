"""工作流编排 API

提供工作流 CRUD、执行触发、执行历史查询、Agent 元数据等接口
路由顺序: 静态路径优先，动态路径 {workflow_id} 在后
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Any
import json

from ..database import get_db
from ..models import IalmdWorkflowDef, IalmdWorkflowExec, IalmdWorkflowNodeExec
from ..schemas.common import ResponseBase, PageResponse
from ..schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowExecRequest,
)
from ..dependencies import get_current_user
from ..services.workflow_engine import WorkflowEngine, get_default_workflows
from ..services.workflow_executor import execute_pipeline, get_pipeline_templates
from ..services.agents import AGENT_METADATA

router = APIRouter(prefix="/api/workflows", tags=["工作流编排"])


# ═══ 静态路由（必须放在 /{workflow_id} 之前）═══

@router.get("/agents", response_model=ResponseBase)
def list_agents():
    """获取所有 Agent 类型元数据（供前端组件栏展示）"""
    return ResponseBase(data=AGENT_METADATA)


@router.get("/templates", response_model=ResponseBase)
def get_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取预置工作流模板（全链路 + 同业对比 + 本体同步 + 定期刷新）"""
    templates = get_pipeline_templates()

    existing = db.query(IalmdWorkflowDef).filter(
        IalmdWorkflowDef.is_deleted == 0,
        IalmdWorkflowDef.workflow_code.in_([t["workflow_code"] for t in templates]),
    ).all()
    existing_codes = {w.workflow_code: w.id for w in existing}

    for t in templates:
        t["workflow_id"] = existing_codes.get(t["workflow_code"])
        t["exists"] = t["workflow_code"] in existing_codes

    return ResponseBase(data=templates)


@router.post("/templates/init", response_model=ResponseBase)
def init_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """初始化预置工作流模板到数据库"""
    templates = get_default_workflows()
    created = []

    for t in templates:
        existing = db.query(IalmdWorkflowDef).filter(
            IalmdWorkflowDef.workflow_code == t["workflow_code"],
            IalmdWorkflowDef.is_deleted == 0,
        ).first()
        if existing:
            continue

        wf = IalmdWorkflowDef(
            workflow_name=t["workflow_name"],
            workflow_code=t["workflow_code"],
            description=t["description"],
            node_json=t["node_json"],
            trigger_type="MANUAL",
            created_by=current_user.get("id"),
            updated_by=current_user.get("id"),
        )
        db.add(wf)
        created.append(t["workflow_name"])

    db.commit()
    return ResponseBase(data={"created": created, "count": len(created)})


@router.get("/executions/{exec_id}/nodes", response_model=ResponseBase)
def get_node_executions(
    exec_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取某次执行的节点级执行详情"""
    nodes = db.query(IalmdWorkflowNodeExec).filter(
        IalmdWorkflowNodeExec.exec_id == exec_id,
        IalmdWorkflowNodeExec.is_deleted == 0,
    ).order_by(IalmdWorkflowNodeExec.created_at.asc()).all()

    return ResponseBase(data=[
        {
            "id": n.id,
            "exec_id": n.exec_id,
            "node_id": n.node_id,
            "node_type": n.node_type,
            "agent_type": n.agent_type,
            "exec_status": n.exec_status,
            "input_json": n.input_json,
            "output_json": n.output_json,
            "error_msg": n.error_msg,
            "started_at": str(n.started_at) if n.started_at else None,
            "finished_at": str(n.finished_at) if n.finished_at else None,
        }
        for n in nodes
    ])


# ═══ 工作流列表 & 创建 ═══

@router.get("", response_model=PageResponse)
def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取工作流定义列表"""
    query = db.query(IalmdWorkflowDef).filter(
        IalmdWorkflowDef.is_deleted == 0,
    )
    if keyword:
        query = query.filter(IalmdWorkflowDef.workflow_name.contains(keyword))

    total = query.count()
    items = query.order_by(IalmdWorkflowDef.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for w in items:
        node_json = w.node_json
        if isinstance(node_json, str):
            node_json = json.loads(node_json)
        result.append({
            "id": w.id,
            "workflow_name": w.workflow_name,
            "workflow_code": w.workflow_code,
            "description": w.description,
            "node_json": node_json,
            "node_count": len(node_json.get("nodes", [])) if isinstance(node_json, dict) else 0,
            "trigger_type": w.trigger_type,
            "cron_expr": w.cron_expr,
            "status": w.status,
            "created_at": str(w.created_at) if w.created_at else None,
            "updated_at": str(w.updated_at) if w.updated_at else None,
        })

    return PageResponse(data=result, total=total, page=page, page_size=page_size)


@router.post("", response_model=ResponseBase)
def create_workflow(
    body: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建工作流"""
    node_json = body.node_json.model_dump() if hasattr(body.node_json, "model_dump") else body.node_json

    wf = IalmdWorkflowDef(
        workflow_name=body.workflow_name,
        workflow_code=body.workflow_code,
        description=body.description,
        node_json=node_json,
        trigger_type=body.trigger_type,
        cron_expr=body.cron_expr,
        created_by=current_user.get("id"),
        updated_by=current_user.get("id"),
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    return ResponseBase(data={"id": wf.id, "message": "工作流创建成功"})


# ═══ 动态路由 {workflow_id} ═══

@router.get("/{workflow_id}", response_model=ResponseBase)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取工作流详情"""
    w = db.query(IalmdWorkflowDef).filter(
        IalmdWorkflowDef.id == workflow_id,
        IalmdWorkflowDef.is_deleted == 0,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="工作流不存在")

    node_json = w.node_json
    if isinstance(node_json, str):
        node_json = json.loads(node_json)

    return ResponseBase(data={
        "id": w.id,
        "workflow_name": w.workflow_name,
        "workflow_code": w.workflow_code,
        "description": w.description,
        "node_json": node_json,
        "trigger_type": w.trigger_type,
        "cron_expr": w.cron_expr,
        "status": w.status,
        "created_at": str(w.created_at) if w.created_at else None,
        "updated_at": str(w.updated_at) if w.updated_at else None,
    })


@router.put("/{workflow_id}", response_model=ResponseBase)
def update_workflow(
    workflow_id: int,
    body: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新工作流"""
    w = db.query(IalmdWorkflowDef).filter(
        IalmdWorkflowDef.id == workflow_id,
        IalmdWorkflowDef.is_deleted == 0,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="工作流不存在")

    if body.workflow_name is not None:
        w.workflow_name = body.workflow_name
    if body.description is not None:
        w.description = body.description
    if body.node_json is not None:
        w.node_json = body.node_json.model_dump() if hasattr(body.node_json, "model_dump") else body.node_json
    if body.trigger_type is not None:
        w.trigger_type = body.trigger_type
    if body.cron_expr is not None:
        w.cron_expr = body.cron_expr
    if body.status is not None:
        w.status = body.status

    w.updated_by = current_user.get("id")
    db.commit()

    return ResponseBase(data={"id": w.id, "message": "工作流更新成功"})


@router.delete("/{workflow_id}", response_model=ResponseBase)
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除工作流（软删除）"""
    w = db.query(IalmdWorkflowDef).filter(
        IalmdWorkflowDef.id == workflow_id,
        IalmdWorkflowDef.is_deleted == 0,
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="工作流不存在")

    w.is_deleted = 1
    w.updated_by = current_user.get("id")
    db.commit()

    return ResponseBase(data={"id": w.id, "message": "工作流已删除"})


@router.post("/{workflow_id}/execute", response_model=ResponseBase)
def execute_workflow(
    workflow_id: int,
    body: WorkflowExecRequest | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """执行工作流 — 串联 指标提取→本体映射→同业对比→报告生成"""
    input_params = body.model_dump() if body else {}
    result = execute_pipeline(
        db, workflow_id=workflow_id,
        input_params=input_params,
        user_id=current_user.get("id", 1),
    )
    return ResponseBase(data=result)


@router.get("/{workflow_id}/executions", response_model=PageResponse)
def list_executions(
    workflow_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取工作流执行历史"""
    query = db.query(IalmdWorkflowExec).filter(
        IalmdWorkflowExec.workflow_id == workflow_id,
        IalmdWorkflowExec.is_deleted == 0,
    )
    total = query.count()
    items = query.order_by(IalmdWorkflowExec.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return PageResponse(
        data=[
            {
                "id": e.id,
                "workflow_id": e.workflow_id,
                "exec_status": e.exec_status,
                "input_json": e.input_json,
                "output_json": e.output_json,
                "error_msg": e.error_msg,
                "started_at": str(e.started_at) if e.started_at else None,
                "finished_at": str(e.finished_at) if e.finished_at else None,
                "triggered_by": e.triggered_by,
                "created_at": str(e.created_at) if e.created_at else None,
            }
            for e in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
