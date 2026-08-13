"""通用 Pydantic Schema"""
from pydantic import BaseModel, field_validator
from typing import Any
from datetime import datetime


class ResponseBase(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Any = None


class PageResponse(BaseModel):
    """分页响应"""
    code: int = 0
    message: str = "success"
    data: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class PageRequest(BaseModel):
    """分页请求"""
    page: int = 1
    page_size: int = 20
    keyword: str | None = None


class TimestampMixin(BaseModel):
    """混入：自动修复 MySQL 零日期 '0000-00-00 00:00:00' → datetime(2000,1,1)

    用法:
        class MySchema(TimestampMixin):
            created_at: datetime
            updated_at: Optional[datetime]
    """
    @field_validator('created_at', 'updated_at', 'verified_at', 'published_at',
                     'last_login_at', check_fields=False)
    @classmethod
    def coerce_zero_date(cls, v):
        if isinstance(v, str) and v.startswith('0000-00-00'):
            return datetime(2000, 1, 1)
        return v
