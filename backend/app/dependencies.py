"""FastAPI 通用依赖"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db

security = HTTPBearer(auto_error=False)

# 开发模式：当环境变量 AUTH_REQUIRED=false 时允许无 token 访问
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "true").lower() not in ("false", "0", "no")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """获取当前登录用户（JWT 验证）"""
    if credentials is None:
        if not AUTH_REQUIRED:
            return {"id": 1, "username": "admin", "real_name": "管理员", "roles": ["ADMIN"]}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id: int = int(payload.get("sub", 0))
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的Token")
        return {
            "id": user_id,
            "username": payload.get("username", ""),
            "real_name": payload.get("real_name", ""),
            "roles": payload.get("roles", []),
        }
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token验证失败")
