"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from ..database import get_db
from ..models import SysUser
from ..schemas.common import ResponseBase
from ..config import settings
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=ResponseBase)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(SysUser).filter(
        SysUser.username == req.username,
        SysUser.status == 1,
        SysUser.is_deleted == 0,
    ).first()

    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 生成 JWT
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "real_name": user.real_name or user.username,
        "roles": [r.role_code for r in user.roles] if user.roles else ["DEMO"],
        "exp": expire,
    }
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    return ResponseBase(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name or user.username,
            "roles": [r.role_code for r in user.roles] if user.roles else ["DEMO"],
        },
    })


@router.get("/me", response_model=ResponseBase)
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return ResponseBase(data={
        "id": current_user["id"],
        "username": current_user["username"],
        "real_name": current_user.get("real_name", ""),
        "roles": current_user.get("roles", []),
    })


@router.post("/logout", response_model=ResponseBase)
def logout(current_user: dict = Depends(get_current_user)):
    """退出登录（客户端清除 token 即可，服务端记录）"""
    return ResponseBase(message="已退出登录")

