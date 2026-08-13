"""保险经营智能分析平台 — FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routers import auth, dashboard, banks, indicators, benchmark, chat, workflow, llm_config, dict as dict_router, indicators_dashboard, ontology, report_collect, liquidity

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="保险经营智能分析平台 IALMD",
    description="AI驱动保险业经营分析智能对话平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(banks.router)
app.include_router(indicators.router)
app.include_router(benchmark.router)
app.include_router(chat.router)
app.include_router(workflow.router)
app.include_router(llm_config.router)
app.include_router(dict_router.router)
app.include_router(indicators_dashboard.router)
app.include_router(ontology.router)
app.include_router(report_collect.router)
app.include_router(liquidity.router)


@app.get("/")
def root():
    """服务健康检查"""
    return {
        "name": "IALMD API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/api/health")
def health_check():
    """健康检查（含 Redis）"""
    from .cache import redis_client
    redis_ok = False
    try:
        redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "mysql": "connected",
        "redis": "connected" if redis_ok else "disconnected",
    }
