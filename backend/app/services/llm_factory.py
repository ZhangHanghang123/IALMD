"""LLM 工厂 — 统一管理 LLM 实例创建，从数据库 sys_llm_config 表读取配置

支持两种模式:
1. 真实 LLM: 配置 API Key 并在数据库启用后，通过 langchain_openai.ChatOpenAI 调用 DeepSeek/Qwen/OpenAI
2. 模拟 LLM: 无 API Key 时，返回预置的结构化响应，保证工作流可独立运行

配置优先级:
  数据库 sys_llm_config (is_enabled=1 AND is_default=1) > 第一个启用的配置 > mock 模式
  如果 .env 中设置了 LLM_PROVIDER/LLM_API_KEY，数据库配置优先。
"""
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

from .llm_mock import MockChatModel

logger = logging.getLogger(__name__)

# 缓存最近一次有效的 LLM 实例（避免每次请求都查库）
_cached_llm: Optional[BaseChatModel] = None
_cached_provider_code: Optional[str] = None


def _load_config_from_db() -> dict | None:
    """从数据库加载当前启用的 LLM 配置（优先默认配置）"""
    try:
        from ..database import SessionLocal
        from ..models.system import SysLlmConfig

        db = SessionLocal()
        try:
            # 优先查找：启用 + 默认
            item = (
                db.query(SysLlmConfig)
                .filter(
                    SysLlmConfig.status == 1,
                    SysLlmConfig.is_enabled == 1,
                    SysLlmConfig.is_default == 1,
                )
                .first()
            )
            # 次优：第一个启用的非 mock 配置
            if not item:
                item = (
                    db.query(SysLlmConfig)
                    .filter(
                        SysLlmConfig.status == 1,
                        SysLlmConfig.is_enabled == 1,
                        SysLlmConfig.provider_code != "mock",
                    )
                    .order_by(SysLlmConfig.sort_order.asc())
                    .first()
                )

            if item and item.provider_code != "mock" and item.api_key:
                return {
                    "provider_code": item.provider_code,
                    "provider_name": item.provider_name,
                    "api_key": item.api_key,
                    "base_url": item.base_url,
                    "model": item.model_name,
                    "temperature": item.temperature,
                    "max_tokens": item.max_tokens,
                }
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"从数据库加载 LLM 配置失败: {e}")
        return None


def get_llm(force_reload: bool = False) -> BaseChatModel:
    """获取 LLM 实例 — 数据库配置优先

    Args:
        force_reload: 强制重新从数据库加载配置（用于配置变更后立即生效）
    """
    global _cached_llm, _cached_provider_code

    # 未强制刷新时，返回缓存
    if not force_reload and _cached_llm is not None:
        return _cached_llm

    config = _load_config_from_db()

    if config:
        # --- 真实 LLM 模式 ---
        try:
            from langchain_openai import ChatOpenAI

            kwargs = {
                "model": config["model"],
                "api_key": config["api_key"],
                "temperature": config.get("temperature", 0.1),
                "max_tokens": config.get("max_tokens", 4096),
            }
            if config.get("base_url"):
                kwargs["base_url"] = config["base_url"]

            llm = ChatOpenAI(**kwargs)
            _cached_llm = llm
            _cached_provider_code = config["provider_code"]

            logger.info(
                f"使用真实 LLM: {config['provider_name']} ({config['model']})"
            )
            return llm

        except ImportError:
            logger.warning("langchain_openai 未安装，回退到模拟模式")
        except Exception as e:
            logger.warning(f"LLM 初始化失败: {e}，回退到模拟模式")

    # --- 模拟模式兜底 ---
    logger.info("使用模拟 LLM 模式（无可用 API Key）")
    _cached_llm = MockChatModel()
    _cached_provider_code = "mock"
    return _cached_llm


def clear_llm_cache():
    """清除 LLM 缓存，下次调用 get_llm() 将重新从数据库加载"""
    global _cached_llm, _cached_provider_code
    _cached_llm = None
    _cached_provider_code = None
    logger.info("LLM 缓存已清除")
