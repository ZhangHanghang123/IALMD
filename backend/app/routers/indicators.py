"""经营指标 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import get_db
from ..models import IalmdIndicatorDefine, IalmdIndicatorValue, IalmdBankInstitution
from ..schemas.common import ResponseBase, PageResponse
from ..schemas.bank import (
    IndicatorDefineOut, IndicatorValueOut, IndicatorValueCreate,
    IndicatorValueUpdate, IndicatorValueVerify
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/indicators", tags=["经营指标"])


@router.get("", response_model=PageResponse)
def list_indicators(
    category_code: str | None = Query(None, description="分类编码"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取指标定义列表"""
    query = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
    )
    if category_code:
        query = query.filter(IalmdIndicatorDefine.category_code == category_code)

    total = query.count()
    items = query.order_by(IalmdIndicatorDefine.sort_order, IalmdIndicatorDefine.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return PageResponse(
        data=[IndicatorDefineOut.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/values", response_model=ResponseBase)
def get_indicator_values(
    indicator_code: str = Query(..., description="指标编码"),
    report_year: int = Query(2025, description="数据年份"),
    institution_ids: str | None = Query(None, description="银行ID列表(逗号分隔)"),
    db: Session = Depends(get_db),
):
    """获取指标值（用于对比分析）"""
    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {indicator_code} 不存在")

    query = db.query(
        IalmdIndicatorValue, IalmdBankInstitution.short_name, IalmdBankInstitution.bank_code
    ).join(
        IalmdBankInstitution,
        IalmdIndicatorValue.institution_id == IalmdBankInstitution.id,
    ).filter(
        IalmdIndicatorValue.indicator_id == indicator.id,
        IalmdIndicatorValue.report_year == report_year,
        IalmdIndicatorValue.report_period == "FY",
        IalmdIndicatorValue.verify_status == "APPROVED",
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    )

    if institution_ids:
        ids = [int(x) for x in institution_ids.split(",") if x.strip()]
        if ids:
            query = query.filter(IalmdIndicatorValue.institution_id.in_(ids))

    rows = query.order_by(IalmdIndicatorValue.value_numeric.desc()).all()

    return ResponseBase(data=[
        {
            "institution_id": row[0].institution_id,
            "bank_name": row[1],
            "bank_code": row[2],
            "value": float(row[0].value_numeric) if row[0].value_numeric else None,
            "year": row[0].report_year,
            "indicator_name": indicator.indicator_name,
            "unit": indicator.unit,
        }
        for row in rows
    ])


@router.get("/categories", response_model=ResponseBase)
def get_indicator_categories(db: Session = Depends(get_db)):
    """获取指标分类树"""
    from sqlalchemy import func
    categories = db.query(
        IalmdIndicatorDefine.category_code,
        func.count(IalmdIndicatorDefine.id),
    ).filter(
        IalmdIndicatorDefine.status == 1,
        IalmdIndicatorDefine.is_deleted == 0,
    ).group_by(IalmdIndicatorDefine.category_code).all()

    category_names = {
        "SCALE": "规模指标",
        "PROFIT": "盈利指标",
        "SOLVENCY": "偿付能力指标",
        "QUALITY": "业务质量指标",
        "VALUE": "价值指标",
        "CHANNEL": "渠道指标",
        "ESG": "ESG指标",
    }

    result = []
    for cat_code, cnt in categories:
        indicators = db.query(IalmdIndicatorDefine).filter(
            IalmdIndicatorDefine.category_code == cat_code,
            IalmdIndicatorDefine.status == 1,
            IalmdIndicatorDefine.is_deleted == 0,
        ).order_by(IalmdIndicatorDefine.sort_order).all()
        result.append({
            "category_code": cat_code,
            "category_name": category_names.get(cat_code, cat_code),
            "count": cnt,
            "indicators": [IndicatorDefineOut.model_validate(ind).model_dump() for ind in indicators],
        })

    return ResponseBase(data=result)


# ========== 指标值维护 CRUD ==========


@router.get("/values/list", response_model=PageResponse)
def list_indicator_values(
    indicator_id: int | None = Query(None, description="指标ID"),
    indicator_code: str | None = Query(None, description="指标编码"),
    bank_name: str | None = Query(None, description="机构名称"),
    bank_code: str | None = Query(None, description="机构代码"),
    report_year: int | None = Query(None, description="数据年份"),
    date_range: str | None = Query(None, description="日期范围"),
    verify_status: str | None = Query(None, description="审核状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取指标值列表（分页）- 支持前端筛选参数"""
    # 构建查询 - 左连接指标定义表和银行表获取名称
    from sqlalchemy.orm import joinedload
    
    query = db.query(
        IalmdIndicatorValue,
        IalmdIndicatorDefine.indicator_name,
        IalmdIndicatorDefine.unit,
        IalmdBankInstitution.short_name.label('bank_name'),
    ).outerjoin(
        IalmdIndicatorDefine,
        IalmdIndicatorValue.indicator_id == IalmdIndicatorDefine.id
    ).outerjoin(
        IalmdBankInstitution,
        IalmdIndicatorValue.institution_id == IalmdBankInstitution.id
    ).filter(
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    )

    # 处理 indicator_id 参数 - 通过 indicator_id 查找 indicator_code
    if indicator_id:
        indicator = db.query(IalmdIndicatorDefine).filter(
            IalmdIndicatorDefine.id == indicator_id,
            IalmdIndicatorDefine.status == 1,
        ).first()
        if indicator:
            query = query.filter(IalmdIndicatorValue.indicator_code == indicator.indicator_code)
    
    if indicator_code:
        query = query.filter(IalmdIndicatorValue.indicator_code == indicator_code)
    
    # 处理 bank_name 参数 - 通过机构名称查找 bank_code
    if bank_name:
        bank = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.short_name.like(f"%{bank_name}%"),
            IalmdBankInstitution.status == 1,
        ).first()
        if bank:
            query = query.filter(IalmdIndicatorValue.bank_code == bank.bank_code)
    
    if bank_code:
        query = query.filter(IalmdIndicatorValue.bank_code == bank_code)
    
    if report_year:
        query = query.filter(IalmdIndicatorValue.report_year == report_year)
    
    # 处理 date_range 参数 - 格式: "2024-01-01,2024-12-31"
    if date_range:
        try:
            date_parts = date_range.split(',')
            if len(date_parts) == 2:
                start_date, end_date = date_parts[0].strip(), date_parts[1].strip()
                # 解析日期范围并映射到 report_year 和 report_period
                from datetime import datetime
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(IalmdIndicatorValue.report_year >= start.year)
                query = query.filter(IalmdIndicatorValue.report_year <= end.year)
        except Exception:
            pass  # 忽略无效日期格式
    
    if verify_status:
        query = query.filter(IalmdIndicatorValue.verify_status == verify_status)

    total = query.count()
    items = query.order_by(IalmdIndicatorValue.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 构建前端期望的响应格式
    result_data = []
    period_map = {
        "FY": "年报",
        "H1": "半年报", 
        "Q1": "一季报",
        "Q3": "三季报",
        "PRELIM": "业绩快报",
    }
    
    for row in items:
        value = row[0]
        indicator_name = row[1] or value.indicator_code or ""
        unit = row[2] or ""
        bank_nm = row[3] or value.bank_code or ""
        
        # 将 report_period 映射为 report_type
        report_type = period_map.get(value.report_period, value.report_period or "年报")
        # 构建 report_date
        report_date = f"{value.report_year}-{value.report_period}" if value.report_period else str(value.report_year)
        
        result_data.append({
            "id": value.id,
            "indicator_id": value.indicator_id,
            "indicator_name": indicator_name,
            "bank_name": bank_nm,
            "report_type": report_type,
            "report_date": report_date,
            "value": value.value_numeric,
            "unit": unit,
            "verify_status": value.verify_status,
            "verify_remark": value.extract_context[:100] if value.extract_context else "",
            "created_by": str(value.created_by) if value.created_by else "",
            "created_at": value.created_at.isoformat() if value.created_at else "",
            "updated_at": value.updated_at.isoformat() if value.updated_at else "",
            # 保留原始字段供其他用途
            "indicator_code": value.indicator_code,
            "bank_code": value.bank_code,
            "report_year": value.report_year,
            "report_period": value.report_period,
        })

    return PageResponse(
        data=result_data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/values/{value_id}", response_model=ResponseBase)
def get_indicator_value(
    value_id: int,
    db: Session = Depends(get_db),
):
    """获取单个指标值详情"""
    value = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.id == value_id,
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).first()

    if not value:
        return ResponseBase(code=404, message="指标值不存在")

    return ResponseBase(data=IndicatorValueOut.model_validate(value).model_dump())


@router.post("/values", response_model=ResponseBase)
def create_indicator_value(
    data: IndicatorValueCreate,
    db: Session = Depends(get_db),
):
    """创建指标值"""
    # 查找指标定义获取indicator_id
    indicator = db.query(IalmdIndicatorDefine).filter(
        IalmdIndicatorDefine.indicator_code == data.indicator_code,
        IalmdIndicatorDefine.status == 1,
    ).first()

    if not indicator:
        return ResponseBase(code=404, message=f"指标 {data.indicator_code} 不存在")

    # 查找银行获取institution_id
    institution = db.query(IalmdBankInstitution).filter(
        IalmdBankInstitution.bank_code == data.bank_code,
        IalmdBankInstitution.status == 1,
    ).first()

    if not institution:
        return ResponseBase(code=404, message=f"银行 {data.bank_code} 不存在")

    # 创建指标值（无认证模式，使用默认值）
    value = IalmdIndicatorValue(
        indicator_code=data.indicator_code,
        bank_code=data.bank_code,
        indicator_id=indicator.id,
        institution_id=institution.id,
        value_numeric=data.value_numeric,
        value_text=data.value_text,
        report_year=data.report_year,
        report_period=data.report_period,
        extract_page=data.extract_page,
        extract_context=data.extract_context,
        confidence=1.0,
        verify_status="PENDING",
    )
    db.add(value)
    db.commit()
    db.refresh(value)

    return ResponseBase(data=IndicatorValueOut.model_validate(value).model_dump(), message="创建成功")


@router.put("/values/{value_id}", response_model=ResponseBase)
def update_indicator_value(
    value_id: int,
    data: IndicatorValueUpdate,
    db: Session = Depends(get_db),
):
    """更新指标值"""
    value = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.id == value_id,
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).first()

    if not value:
        return ResponseBase(code=404, message="指标值不存在")

    # 更新字段
    if data.value_numeric is not None:
        value.value_numeric = data.value_numeric
    if data.value_text is not None:
        value.value_text = data.value_text
    if data.report_year is not None:
        value.report_year = data.report_year
    if data.report_period is not None:
        value.report_period = data.report_period

    value.updated_at = datetime.now()
    # 更新后需重新审核
    value.verify_status = "PENDING"

    db.commit()
    db.refresh(value)

    return ResponseBase(data=IndicatorValueOut.model_validate(value).model_dump(), message="更新成功")


@router.delete("/values/{value_id}", response_model=ResponseBase)
def delete_indicator_value(
    value_id: int,
    db: Session = Depends(get_db),
):
    """删除指标值（软删除）"""
    value = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.id == value_id,
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).first()

    if not value:
        return ResponseBase(code=404, message="指标值不存在")

    value.is_deleted = 1
    value.status = 0
    value.updated_at = datetime.now()

    db.commit()

    return ResponseBase(message="删除成功")


@router.post("/values/{value_id}/verify", response_model=ResponseBase)
def verify_indicator_value(
    value_id: int,
    data: IndicatorValueVerify,
    db: Session = Depends(get_db),
):
    """审核指标值"""
    value = db.query(IalmdIndicatorValue).filter(
        IalmdIndicatorValue.id == value_id,
        IalmdIndicatorValue.status == 1,
        IalmdIndicatorValue.is_deleted == 0,
    ).first()

    if not value:
        return ResponseBase(code=404, message="指标值不存在")

    if data.verify_status not in ("APPROVED", "REJECTED"):
        return ResponseBase(code=400, message="审核状态只能是 APPROVED 或 REJECTED")

    value.verify_status = data.verify_status
    value.verified_at = datetime.now()
    value.updated_at = datetime.now()

    db.commit()
    db.refresh(value)

    status_text = "已通过" if data.verify_status == "APPROVED" else "已拒绝"
    return ResponseBase(data=IndicatorValueOut.model_validate(value).model_dump(), message=f"审核{status_text}")
