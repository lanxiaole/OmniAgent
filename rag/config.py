# rag 模块配置

from config.settings import PERSIST_DIR, KNOWLEDGE_DIR, EMBEDDING_MODEL, RAG_TOP_K, DASHSCOPE_API_KEY, OPENAI_API_KEY

# 哈希文件路径
HASH_FILE = "chroma_db/content.hash"

__all__ = [
    "PERSIST_DIR",
    "KNOWLEDGE_DIR",
    "EMBEDDING_MODEL",
    "RAG_TOP_K",
    "DASHSCOPE_API_KEY",
    "OPENAI_API_KEY",
    "HASH_FILE"
]
