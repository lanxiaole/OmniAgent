"""Embedding 工具模块

提供统一的 Embedding 客户端创建逻辑，供 RAG 和 Memory 模块共用。
支持三种提供商，通过 EMBEDDING_PROVIDER 或 base_url 自动识别：
- ollama      → 本地 Ollama（OpenAI 兼容 /v1/embeddings 接口，无需 API Key）
- dashscope   → 阿里云百炼（DashScopeEmbeddings，兼容新版模型）
- openai/auto → 其他 OpenAI 兼容接口（OpenAIEmbeddings）
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from agent_core.config.settings import (
    get_embedding_model,
    get_embedding_api_key,
    get_embedding_base_url,
    get_embedding_provider,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)


def create_embeddings():
    """根据提供商设置创建 Embedding 客户端

    - 提供商为 ollama 或 base_url 指向本地 Ollama → OpenAIEmbeddings（兼容接口）
    - 提供商为 auto 且 base_url 含 dashscope/aliyun → DashScopeEmbeddings
    - 其他 → OpenAIEmbeddings（OpenAI 兼容接口）
    """
    provider = (get_embedding_provider() or "auto").lower()
    embedding_base_url = get_embedding_base_url() or ""
    model = get_embedding_model()
    api_key = get_embedding_api_key()

    # 本地 Ollama：走原生 OllamaEmbeddings 接口（/api/embeds），避免 OpenAI 兼容接口类型不兼容
    if provider == "ollama" or "11434" in embedding_base_url or "ollama" in embedding_base_url:
        logger.info(f"使用 OllamaEmbeddings: {model} @ {embedding_base_url}")
        # base_url 指向 Ollama 根地址（原生接口不走 /v1，直接对根地址 POST /api/embeds）
        ollama_base = embedding_base_url.rstrip("/")
        if ollama_base.endswith("/v1"):
            ollama_base = ollama_base[:-3]
        return OllamaEmbeddings(
            model=model,
            base_url=ollama_base,
        )

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
