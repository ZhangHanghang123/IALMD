"""字典管理 Pydantic Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .common import TimestampMixin


# ==================== 字典类型 ====================

class DictTypeBase(BaseModel):
    """字典类型基础"""
    dict_name: str = Field(..., description="字典名称")
    dict_code: str = Field(..., description="字典编码")
    description: Optional[str] = ""
    sort_order: int = 0


class DictTypeCreate(DictTypeBase):
    """字典类型创建"""
    pass


class DictTypeUpdate(BaseModel):
    """字典类型更新"""
    dict_name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None


class DictTypeResponse(TimestampMixin, DictTypeBase):
    """字典类型响应"""
    id: int
    status: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== 字典数据 ====================

class DictDataBase(BaseModel):
    """字典数据基础"""
    dict_label: str = Field(..., description="字典标签")
    dict_value: str = Field(..., description="字典键值")
    dict_key: str = Field(..., description="字典键名")
    sort_order: int = 0


class DictDataCreate(DictDataBase):
    """字典数据创建"""
    dict_type_id: int


class DictDataUpdate(BaseModel):
    """字典数据更新"""
    dict_label: Optional[str] = None
    dict_value: Optional[str] = None
    dict_key: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[int] = None


class DictDataResponse(TimestampMixin, DictDataBase):
    """字典数据响应"""
    id: int
    dict_type_id: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 字典详情(包含数据列表) ====================

class DictTypeWithData(DictTypeResponse):
    """字典类型(含数据列表)"""
    datas: list[DictDataResponse] = []

    class Config:
        from_attributes = True
