"""LLM 配置管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.system import SysLlmConfig
from ..schemas.llm_config import (
    LlmConfigCreate,
    LlmConfigUpdate,
    LlmConfigEnable,
    LlmConfigResponse,
)
from ..schemas.common import ResponseBase, PageResponse

router = APIRouter(prefix="/api/llm-config", tags=["LLM配置"])


# ==================== 查询 ====================

@router.get("", response_model=PageResponse)
def list_configs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取 LLM 配置列表"""
    total = db.query(SysLlmConfig).filter(SysLlmConfig.status == 1).count()
    items = (
        db.query(SysLlmConfig)
        .filter(SysLlmConfig.status == 1)
        .order_by(SysLlmConfig.sort_order.asc(), SysLlmConfig.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[LlmConfigResponse.model_validate(item).model_dump() for item in items],
    )


@router.get("/{config_id}", response_model=ResponseBase)
def get_config(config_id: int, db: Session = Depends(get_db)):
    """获取单个 LLM 配置"""
    item = db.query(SysLlmConfig).filter(SysLlmConfig.id == config_id, SysLlmConfig.status == 1).first()
    if not item:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ResponseBase(data=LlmConfigResponse.model_validate(item).model_dump())


# ==================== 新增 ====================

@router.post("", response_model=ResponseBase)
def create_config(data: LlmConfigCreate, db: Session = Depends(get_db)):
    """新增 LLM 配置"""
    existing = db.query(SysLlmConfig).filter(
        SysLlmConfig.provider_code == data.provider_code,
        SysLlmConfig.status == 1,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"服务商编码 {data.provider_code} 已存在")

    # 如果设为默认，取消其他默认
    if data.is_default == 1:
        db.query(SysLlmConfig).filter(SysLlmConfig.is_default == 1).update({"is_default": 0})

    item = SysLlmConfig(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return ResponseBase(data=LlmConfigResponse.model_validate(item).model_dump(), message="新增成功")


# ==================== 编辑 ====================

@router.put("/{config_id}", response_model=ResponseBase)
def update_config(config_id: int, data: LlmConfigUpdate, db: Session = Depends(get_db)):
    """编辑 LLM 配置"""
    item = db.query(SysLlmConfig).filter(SysLlmConfig.id == config_id, SysLlmConfig.status == 1).first()
    if not item:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = data.model_dump(exclude_none=True)

    # 如果设默认，取消其他的
    if update_data.get("is_default") == 1:
        db.query(SysLlmConfig).filter(
            SysLlmConfig.is_default == 1,
            SysLlmConfig.id != config_id,
        ).update({"is_default": 0})

    for key, val in update_data.items():
        setattr(item, key, val)

    db.commit()
    db.refresh(item)
    return ResponseBase(data=LlmConfigResponse.model_validate(item).model_dump(), message="更新成功")


# ==================== 启/禁用 ====================

@router.patch("/{config_id}/toggle", response_model=ResponseBase)
def toggle_config(config_id: int, data: LlmConfigEnable, db: Session = Depends(get_db)):
    """启用/禁用 LLM 配置"""
    item = db.query(SysLlmConfig).filter(SysLlmConfig.id == config_id, SysLlmConfig.status == 1).first()
    if not item:
        raise HTTPException(status_code=404, detail="配置不存在")

    # mock 模式不允许禁用
    if item.provider_code == "mock" and data.is_enabled == 0:
        raise HTTPException(status_code=400, detail="模拟模式不允许禁用")

    item.is_enabled = data.is_enabled
    db.commit()
    db.refresh(item)

    # 配置变更后清除 LLM 缓存
    from ..services.llm_factory import clear_llm_cache
    clear_llm_cache()

    return ResponseBase(
        data=LlmConfigResponse.model_validate(item).model_dump(),
        message="启用成功" if data.is_enabled else "禁用成功",
    )


# ==================== 删除 ====================

@router.delete("/{config_id}", response_model=ResponseBase)
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除 LLM 配置（软删除）"""
    item = db.query(SysLlmConfig).filter(SysLlmConfig.id == config_id, SysLlmConfig.status == 1).first()
    if not item:
        raise HTTPException(status_code=404, detail="配置不存在")

    if item.provider_code == "mock":
        raise HTTPException(status_code=400, detail="模拟模式不允许删除")

    item.status = 0
    db.commit()
    return ResponseBase(message="删除成功")


# ==================== 测试连接 ====================

@router.post("/{config_id}/test", response_model=ResponseBase)
def test_connection(config_id: int, db: Session = Depends(get_db)):
    """测试 LLM 连接"""
    item = db.query(SysLlmConfig).filter(SysLlmConfig.id == config_id, SysLlmConfig.status == 1).first()
    if not item:
        raise HTTPException(status_code=404, detail="配置不存在")

    if item.provider_code == "mock":
        return ResponseBase(data={"success": True, "message": "模拟模式无需测试"}, message="模拟模式可用")

    if not item.api_key:
        raise HTTPException(status_code=400, detail="请先填写 API Key")

    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=item.model_name,
            api_key=item.api_key,
            base_url=item.base_url or None,
            temperature=0.1,
            max_tokens=10,
        )
        resp = llm.invoke("ping")
        return ResponseBase(
            data={"success": True, "response": str(resp.content)[:50]},
            message=f"连接成功 — {item.provider_name}",
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="langchain_openai 未安装")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")
