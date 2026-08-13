"""应用配置管理"""
import os
from pydantic_settings import BaseSettings

# 项目根目录: backend/ 的上一级
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """应用配置"""
    # 数据库
    DATABASE_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/IALMD?charset=utf8mb4"
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    # JWT
    SECRET_KEY: str = "ialmd-dev-secret-key-change-in-production-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    # 服务
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    DEBUG: bool = True
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5174", "http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5174"]
    # 报告文件目录（跨平台：Windows 本地开发 / Linux 服务器部署）
    REPORTS_DIR: str = os.path.join(PROJECT_ROOT, "data", "保险经营报告下载")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"


settings = Settings()
