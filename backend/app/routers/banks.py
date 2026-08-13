"""保险机构 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from ..database import get_db
from ..models import IalmdBankInstitution
from ..schemas.common import ResponseBase, PageResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/banks", tags=["保险机构"])


# ==================== Schemas ====================

class BankCreate(BaseModel):
    """机构创建"""
    bank_name: str = Field(..., description="保险机构全称")
    short_name: Optional[str] = ""
    bank_code: Optional[str] = ""
    bank_type: str = Field(..., description="机构类型")
    stock_code: Optional[str] = ""
    listing_market: Optional[str] = ""
    total_assets: Optional[float] = None
    website: Optional[str] = ""


class BankUpdate(BaseModel):
    """机构更新"""
    bank_name: Optional[str] = None
    short_name: Optional[str] = None
    bank_code: Optional[str] = None
    bank_type: Optional[str] = None
    stock_code: Optional[str] = None
    listing_market: Optional[str] = None
    total_assets: Optional[float] = None
    website: Optional[str] = None
    status: Optional[int] = None


class BankOut(BaseModel):
    """机构输出"""
    id: int
    bank_name: str
    short_name: str
    bank_code: str
    bank_type: str
    stock_code: str
    listing_market: str
    total_assets: Optional[float]
    website: str
    status: int

    class Config:
        from_attributes = True


# ==================== API ====================

@router.get("", response_model=PageResponse)
def list_banks(
    bank_type: str | None = Query(None, description="机构类型筛选"),
    keyword: str | None = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    # 移除认证要求，允许公开访问机构列表
):
    """获取机构列表"""
    query = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.is_deleted == 0,
    )
    if bank_type:
        query = query.filter(IalmdBankInstitution.bank_type == bank_type)
    if keyword:
        query = query.filter(
            IalmdBankInstitution.bank_name.contains(keyword) |
            IalmdBankInstitution.short_name.contains(keyword)
        )

    total = query.count()
    items = query.order_by(IalmdBankInstitution.bank_type, IalmdBankInstitution.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return PageResponse(
        data=[BankOut.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/types", response_model=ResponseBase)
def get_bank_types(db: Session = Depends(get_db)):
    """获取机构类型列表(用于下拉框)"""
    from ..services.dict_service import get_dict_by_code
    # 使用字典服务获取机构类型
    bank_types = get_dict_by_code("bank_type")
    return ResponseBase(data=[
        {"label": v["dict_label"], "value": v["dict_value"]}
        for k, v in bank_types.items()
    ])


@router.get("/types/stat", response_model=ResponseBase)
def get_bank_types_stat(db: Session = Depends(get_db)):
    """获取机构类型统计"""
    from sqlalchemy import func
    from ..services.dict_service import get_dict_by_code
    
    types = db.query(
        IalmdBankInstitution.bank_type,
        func.count(IalmdBankInstitution.id),
    ).filter(
        IalmdBankInstitution.status == 1,
        IalmdBankInstitution.is_deleted == 0,
    ).group_by(IalmdBankInstitution.bank_type).all()
    
    # 使用字典获取中文名称
    bank_type_dict = get_dict_by_code("bank_type")
    
    return ResponseBase(data=[
        {
            "type_code": t[0], 
            "type_name": bank_type_dict.get(t[0], {}).get("dict_label", t[0]), 
            "count": t[1]
        }
        for t in types
    ])


@router.get("/{bank_id}", response_model=ResponseBase)
def get_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取机构详情"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    return ResponseBase(data=BankOut.model_validate(bank).model_dump())


@router.post("", response_model=ResponseBase)
def create_bank(
    data: BankCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建机构"""
    bank = IalmdBankInstitution(
        bank_name=data.bank_name,
        short_name=data.short_name,
        bank_code=data.bank_code,
        bank_type=data.bank_type,
        stock_code=data.stock_code,
        listing_market=data.listing_market,
        total_assets=data.total_assets,
        website=data.website,
        created_by=current_user.get("id"),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    
    return ResponseBase(data=BankOut.model_validate(bank).model_dump())


@router.put("/{bank_id}", response_model=ResponseBase)
def update_bank(
    bank_id: int,
    data: BankUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新机构"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    if data.bank_name is not None:
        bank.bank_name = data.bank_name
    if data.short_name is not None:
        bank.short_name = data.short_name
    if data.bank_code is not None:
        bank.bank_code = data.bank_code
    if data.bank_type is not None:
        bank.bank_type = data.bank_type
    if data.stock_code is not None:
        bank.stock_code = data.stock_code
    if data.listing_market is not None:
        bank.listing_market = data.listing_market
    if data.total_assets is not None:
        bank.total_assets = data.total_assets
    if data.website is not None:
        bank.website = data.website
    if data.status is not None:
        bank.status = data.status
    
    bank.updated_by = current_user.get("id")
    db.commit()
    db.refresh(bank)
    
    return ResponseBase(data=BankOut.model_validate(bank).model_dump())


@router.delete("/{bank_id}", response_model=ResponseBase)
def delete_bank(
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除机构(软删除)"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    bank.is_deleted = 1
    db.commit()
    
    return ResponseBase(message="删除成功")


@router.patch("/{bank_id}/status", response_model=ResponseBase)
def toggle_bank_status(
    bank_id: int,
    status: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """切换机构状态"""
    bank = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.id == bank_id,
        IalmdBankInstitution.is_deleted == 0,
    ).first()
    
    if not bank:
        raise HTTPException(status_code=404, detail="机构不存在")
    
    bank.status = status
    bank.updated_by = current_user.get("id")
    db.commit()
    
    return ResponseBase(message="状态更新成功")
