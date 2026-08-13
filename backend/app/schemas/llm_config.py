"""LLM 配置 Schema"""
from datetime import datetime
from pydantic import BaseModel, Field
from .common import TimestampMixin


class LlmConfigBase(BaseModel):
    provider_name: str = Field(..., max_length=64, description="服务商名称")
    provider_code: str = Field(..., max_length=32, description="服务商编码")
    api_key: str = Field(default="", max_length=512, description="API密钥")
    base_url: str = Field(default="", max_length=256, description="API地址")
    model_name: str = Field(default="", max_length=128, description="模型名称")
    temperature: float = Field(default=0.10, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, le=131072, description="最大Token数")
    is_enabled: int = Field(default=0, ge=0, le=1, description="是否启用")
    is_default: int = Field(default=0, ge=0, le=1, description="是否默认")
    sort_order: int = Field(default=0, description="排序号")
    remark: str = Field(default="", max_length=256, description="备注")


class LlmConfigCreate(LlmConfigBase):
    pass


class LlmConfigUpdate(BaseModel):
    provider_name: str | None = Field(None, max_length=64)
    provider_code: str | None = Field(None, max_length=32)
    api_key: str | None = Field(None, max_length=512)
    base_url: str | None = Field(None, max_length=256)
    model_name: str | None = Field(None, max_length=128)
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1, le=131072)
    is_enabled: int | None = Field(None, ge=0, le=1)
    is_default: int | None = Field(None, ge=0, le=1)
    sort_order: int | None = Field(None)
    remark: str | None = Field(None, max_length=256)


class LlmConfigEnable(BaseModel):
    """启/禁用"""
    is_enabled: int = Field(..., ge=0, le=1, description="0=禁用,1=启用")


class LlmConfigResponse(TimestampMixin, LlmConfigBase):
    id: int
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
