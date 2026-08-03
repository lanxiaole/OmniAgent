# config 包初始化文件
#
# 动态配置（来自 .env）通过 getter 函数导出，保证保存后即时生效。
# 静态配置（硬编码常量）直接导出为模块级常量。

from .settings import (
    # 动态配置 - getter 函数
    get_llm_base_url,
    get_llm_api_key,
    get_llm_model_name,
    get_embedding_base_url,
    get_embedding_api_key,
    get_embedding_model,
    get_amap_api_key,
    # 静态配置 - 模块级常量
    LLM_TEMPERATURE,
    LLM_SUMMARIZER_MODEL,
    EMBEDDING_DIMENSIONS,
    PERSIST_DIR,
    VECTOR_STORE_DIR,
    CHECKPOINT_DIR,
    KNOWLEDGE_DIR,
    LOGS_DIR,
    CACHE_DIR,
    TEMP_DIR,
    UPLOAD_DIR,
    WORKSPACE_DIR,
    MEMORY_DIR,
    USER_DATA_DIR,
    RAG_TOP_K,
)

__all__ = [
    # 动态配置
    "get_llm_base_url",
    "get_llm_api_key",
    "get_llm_model_name",
    "get_embedding_base_url",
    "get_embedding_api_key",
    "get_embedding_model",
    "get_amap_api_key",
    # 静态配置
    "LLM_TEMPERATURE",
    "LLM_SUMMARIZER_MODEL",
    "EMBEDDING_DIMENSIONS",
    "PERSIST_DIR",
    "VECTOR_STORE_DIR",
    "CHECKPOINT_DIR",
    "KNOWLEDGE_DIR",
    "LOGS_DIR",
    "CACHE_DIR",
    "TEMP_DIR",
    "UPLOAD_DIR",
    "WORKSPACE_DIR",
    "MEMORY_DIR",
    "USER_DATA_DIR",
    "RAG_TOP_K",
]