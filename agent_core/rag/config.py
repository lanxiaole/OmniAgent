# rag 模块配置

import os
from agent_core.config.settings import VECTOR_STORE_DIR, KNOWLEDGE_DIR, EMBEDDING_MODEL, EMBEDDING_API_KEY, EMBEDDING_BASE_URL, RAG_TOP_K

# 哈希文件路径
HASH_FILE = os.path.join(VECTOR_STORE_DIR, "content.hash")

__all__ = [
    "VECTOR_STORE_DIR",
    "KNOWLEDGE_DIR",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "EMBEDDING_BASE_URL",
    "RAG_TOP_K",
    "HASH_FILE"
]
