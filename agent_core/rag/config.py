# rag 模块配置

from agent_core.config.settings import PERSIST_DIR, KNOWLEDGE_DIR, EMBEDDING_MODEL, EMBEDDING_API_KEY, EMBEDDING_BASE_URL, RAG_TOP_K

# 哈希文件路径
HASH_FILE = "chroma_db/content.hash"

__all__ = [
    "PERSIST_DIR",
    "KNOWLEDGE_DIR",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "EMBEDDING_BASE_URL",
    "RAG_TOP_K",
    "HASH_FILE"
]
