"""Redis 缓存连接管理"""
import redis
from .config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
)


def get_redis():
    """FastAPI 依赖注入: 获取 Redis 客户端"""
    return redis_client
