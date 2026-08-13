"""字典管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from ..database import get_db
from ..models.system import SysDictType, SysDictData
from ..schemas.dict import (
    DictTypeCreate, DictTypeUpdate, DictTypeResponse, DictTypeWithData,
    DictDataCreate, DictDataUpdate, DictDataResponse,
)
from ..schemas.common import ResponseBase, PageResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/dict", tags=["字典管理"])


# ==================== 字典类型 ====================

@router.get("/types", response_model=PageResponse)
def list_dict_types(
    dict_code: Optional[str] = None,
    dict_name: Optional[str] = None,
    status: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取字典类型列表"""
    query = db.query(SysDictType).filter(SysDictType.is_deleted == 0)
    
    if dict_code:
        query = query.filter(SysDictType.dict_code.like(f"%{dict_code}%"))
    if dict_name:
        query = query.filter(SysDictType.dict_name.like(f"%{dict_name}%"))
    if status is not None:
        query = query.filter(SysDictType.status == status)
    
    total = query.count()
    items = query.order_by(SysDictType.sort_order.asc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PageResponse(
        data=[DictTypeResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/types/{type_id}", response_model=ResponseBase)
def get_dict_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取字典类型详情"""
    dict_type = db.query(SysDictType).filter(
        SysDictType.id == type_id,
        SysDictType.is_deleted == 0,
    ).first()
    
    if not dict_type:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    
    return ResponseBase(data=DictTypeResponse.model_validate(dict_type))


@router.get("/types/{type_id}/with-data", response_model=ResponseBase)
def get_dict_type_with_data(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取字典类型(含数据列表)"""
    dict_type = db.query(SysDictType).filter(
        SysDictType.id == type_id,
        SysDictType.is_deleted == 0,
    ).first()
    
    if not dict_type:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    
    datas = db.query(SysDictData).filter(
        SysDictData.dict_type_id == type_id,
        SysDictData.is_deleted == 0,
    ).order_by(SysDictData.sort_order.asc()).all()
    
    result = DictTypeWithData.model_validate(dict_type)
    result.datas = [DictDataResponse.model_validate(d) for d in datas]
    
    return ResponseBase(data=result)


@router.post("/types", response_model=ResponseBase)
def create_dict_type(
    data: DictTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建字典类型"""
    # 检查编码唯一性
    exists = db.query(SysDictType).filter(
        SysDictType.dict_code == data.dict_code,
        SysDictType.is_deleted == 0,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="字典编码已存在")
    
    dict_type = SysDictType(
        dict_name=data.dict_name,
        dict_code=data.dict_code,
        description=data.description,
        sort_order=data.sort_order,
        created_by=current_user.get("id"),
    )
    db.add(dict_type)
    db.commit()
    db.refresh(dict_type)
    
    return ResponseBase(data=DictTypeResponse.model_validate(dict_type))


@router.put("/types/{type_id}", response_model=ResponseBase)
def update_dict_type(
    type_id: int,
    data: DictTypeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新字典类型"""
    dict_type = db.query(SysDictType).filter(
        SysDictType.id == type_id,
        SysDictType.is_deleted == 0,
    ).first()
    
    if not dict_type:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    
    if data.dict_name is not None:
        dict_type.dict_name = data.dict_name
    if data.description is not None:
        dict_type.description = data.description
    if data.sort_order is not None:
        dict_type.sort_order = data.sort_order
    if data.status is not None:
        dict_type.status = data.status
    
    dict_type.updated_by = current_user.get("id")
    db.commit()
    
    return ResponseBase(data=DictTypeResponse.model_validate(dict_type))


@router.delete("/types/{type_id}", response_model=ResponseBase)
def delete_dict_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除字典类型"""
    dict_type = db.query(SysDictType).filter(
        SysDictType.id == type_id,
        SysDictType.is_deleted == 0,
    ).first()
    
    if not dict_type:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    
    dict_type.is_deleted = 1
    db.commit()
    
    return ResponseBase(message="删除成功")


# ==================== 字典数据 ====================

@router.get("/data", response_model=PageResponse)
def list_dict_data(
    dict_type_id: Optional[int] = None,
    dict_code: Optional[str] = None,
    dict_label: Optional[str] = None,
    status: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取字典数据列表"""
    query = db.query(SysDictData).filter(SysDictData.is_deleted == 0)
    
    if dict_type_id:
        query = query.filter(SysDictData.dict_type_id == dict_type_id)
    if dict_label:
        query = query.filter(SysDictData.dict_label.like(f"%{dict_label}%"))
    if status is not None:
        query = query.filter(SysDictData.status == status)
    
    # 如果提供了字典编码，需要先查类型ID
    if dict_code:
        dict_type = db.query(SysDictType).filter(
            SysDictType.dict_code == dict_code,
            SysDictType.is_deleted == 0,
        ).first()
        if dict_type:
            query = query.filter(SysDictData.dict_type_id == dict_type.id)
        else:
            return PageResponse(data=[], total=0, page=page, page_size=page_size)
    
    total = query.count()
    items = query.order_by(SysDictData.sort_order.asc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 填充字典类型信息
    result = []
    for item in items:
        resp = DictDataResponse.model_validate(item)
        dict_type = db.query(SysDictType).filter(SysDictType.id == item.dict_type_id).first()
        if dict_type:
            resp.dict_type_id = dict_type.id
        result.append(resp)
    
    return PageResponse(data=result, total=total, page=page, page_size=page_size)


@router.get("/data/{data_id}", response_model=ResponseBase)
def get_dict_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取字典数据详情"""
    dict_data = db.query(SysDictData).filter(
        SysDictData.id == data_id,
        SysDictData.is_deleted == 0,
    ).first()
    
    if not dict_data:
        raise HTTPException(status_code=404, detail="字典数据不存在")
    
    return ResponseBase(data=DictDataResponse.model_validate(dict_data))


@router.post("/data", response_model=ResponseBase)
def create_dict_data(
    data: DictDataCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建字典数据"""
    # 检查类型存在
    dict_type = db.query(SysDictType).filter(
        SysDictType.id == data.dict_type_id,
        SysDictType.is_deleted == 0,
    ).first()
    if not dict_type:
        raise HTTPException(status_code=400, detail="字典类型不存在")
    
    # 检查键名唯一性
    exists = db.query(SysDictData).filter(
        SysDictData.dict_type_id == data.dict_type_id,
        SysDictData.dict_key == data.dict_key,
        SysDictData.is_deleted == 0,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="字典键名已存在")
    
    dict_data = SysDictData(
        dict_type_id=data.dict_type_id,
        dict_label=data.dict_label,
        dict_value=data.dict_value,
        dict_key=data.dict_key,
        sort_order=data.sort_order,
        created_by=current_user.get("id"),
    )
    db.add(dict_data)
    db.commit()
    db.refresh(dict_data)
    
    return ResponseBase(data=DictDataResponse.model_validate(dict_data))


@router.put("/data/{data_id}", response_model=ResponseBase)
def update_dict_data(
    data_id: int,
    data: DictDataUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新字典数据"""
    dict_data = db.query(SysDictData).filter(
        SysDictData.id == data_id,
        SysDictData.is_deleted == 0,
    ).first()
    
    if not dict_data:
        raise HTTPException(status_code=404, detail="字典数据不存在")
    
    if data.dict_label is not None:
        dict_data.dict_label = data.dict_label
    if data.dict_value is not None:
        dict_data.dict_value = data.dict_value
    if data.dict_key is not None:
        dict_data.dict_key = data.dict_key
    if data.sort_order is not None:
        dict_data.sort_order = data.sort_order
    if data.status is not None:
        dict_data.status = data.status
    
    dict_data.updated_by = current_user.get("id")
    db.commit()
    
    return ResponseBase(data=DictDataResponse.model_validate(dict_data))


@router.delete("/data/{data_id}", response_model=ResponseBase)
def delete_dict_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除字典数据"""
    dict_data = db.query(SysDictData).filter(
        SysDictData.id == data_id,
        SysDictData.is_deleted == 0,
    ).first()
    
    if not dict_data:
        raise HTTPException(status_code=404, detail="字典数据不存在")
    
    dict_data.is_deleted = 1
    db.commit()
    
    return ResponseBase(message="删除成功")


# ==================== 字典查询(前端使用) ====================

@router.get("/codes/{dict_code}", response_model=ResponseBase)
def get_dict_by_code(
    dict_code: str,
    db: Session = Depends(get_db),
):
    """根据字典编码获取字典数据列表(前端下拉框用)"""
    dict_type = db.query(SysDictType).filter(
        SysDictType.dict_code == dict_code,
        SysDictType.status == 1,
        SysDictType.is_deleted == 0,
    ).first()
    
    if not dict_type:
        return ResponseBase(data=[])
    
    datas = db.query(SysDictData).filter(
        SysDictData.dict_type_id == dict_type.id,
        SysDictData.status == 1,
        SysDictData.is_deleted == 0,
    ).order_by(SysDictData.sort_order.asc()).all()
    
    return ResponseBase(data=[
        {
            "label": d.dict_label,
            "value": d.dict_value,
            "key": d.dict_key,
        }
        for d in datas
    ])
