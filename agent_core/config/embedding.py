"""Embedding 工具模块

提供统一的 Embedding 客户端创建逻辑，供 RAG 和 Memory 模块共用。
根据 base_url 自动选择 DashScope（阿里云百炼）或 OpenAI 兼容接口。
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from agent_core.config.settings import get_embedding_model, get_embedding_api_key, get_embedding_base_url
from agent_core.logger import get_logger

logger = get_logger(__name__)


def create_embeddings():
    """根据 base_url 自动选择 Embedding 客户端

    - 阿里云百炼（dashscope）→ DashScopeEmbeddings（兼容新版模型）
    - 其他（OpenAI 等）→ OpenAIEmbeddings（OpenAI 兼容接口）
    """
    embedding_base_url = get_embedding_base_url() or ""
    model = get_embedding_model()
    api_key = get_embedding_api_key()

    if "dashscope" in embedding_base_url or "aliyun" in embedding_base_url:
        logger.info(f"使用 DashScopeEmbeddings: {model}")
        return DashScopeEmbeddings(
            model=model,
            dashscope_api_key=api_key,
        )

    logger.info(f"使用 OpenAIEmbeddings: {model} @ {embedding_base_url}")
    return OpenAIEmbeddings(
        model=model,
        base_url=embedding_base_url,
        api_key=api_key,
    )
