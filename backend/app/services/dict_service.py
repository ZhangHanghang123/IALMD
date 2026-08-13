"""字典服务 — 提供字典数据的统一访问接口"""
import logging
from typing import Optional
from ..models.system import SysDictType, SysDictData

logger = logging.getLogger(__name__)

# 字典缓存: {dict_code: {dict_key: {dict_label, dict_value, id}}}
_dict_cache: dict = {}


def reload_dict_cache():
    """重新加载字典缓存"""
    global _dict_cache
    _dict_cache = {}
    logger.info("字典缓存已重建")


def get_dict_by_code(dict_code: str) -> dict:
    """获取指定字典的所有数据
    
    Args:
        dict_code: 字典编码
        
    Returns:
        {dict_key: {dict_label, dict_value, id}}
    """
    from ..database import SessionLocal
    
    if dict_code in _dict_cache:
        return _dict_cache[dict_code]
    
    db = SessionLocal()
    try:
        dict_type = db.query(SysDictType).filter(
            SysDictType.dict_code == dict_code,
            SysDictType.status == 1,
            SysDictType.is_deleted == 0,
        ).first()
        
        if not dict_type:
            logger.warning(f"字典不存在或已禁用: {dict_code}")
            return {}
        
        datas = db.query(SysDictData).filter(
            SysDictData.dict_type_id == dict_type.id,
            SysDictData.status == 1,
            SysDictData.is_deleted == 0,
        ).order_by(SysDictData.sort_order.asc()).all()
        
        result = {}
        for d in datas:
            result[d.dict_key] = {
                "dict_label": d.dict_label,
                "dict_value": d.dict_value,
                "id": d.id,
            }
        
        _dict_cache[dict_code] = result
        return result
    finally:
        db.close()


def get_dict_label(dict_code: str, dict_key: str, default: str = "") -> str:
    """根据字典编码和键获取标签
    
    Args:
        dict_code: 字典编码
        dict_key: 字典键
        default: 默认值
        
    Returns:
        字典标签
    """
    data = get_dict_by_code(dict_code).get(dict_key)
    if data:
        return data["dict_label"]
    return default


def get_dict_value(dict_code: str, dict_label: str, default: str = "") -> str:
    """根据字典编码和标签获取键值
    
    Args:
        dict_code: 字典编码
        dict_label: 字典标签
        default: 默认值
        
    Returns:
        字典键值
    """
    data_dict = get_dict_by_code(dict_code)
    for key, val in data_dict.items():
        if val["dict_label"] == dict_label:
            return val["dict_value"]
    return default


def get_all_dict_codes() -> list[str]:
    """获取所有字典编码列表"""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        dict_types = db.query(SysDictType).filter(
            SysDictType.status == 1,
            SysDictType.is_deleted == 0,
        ).all()
        return [d.dict_code for d in dict_types]
    finally:
        db.close()
