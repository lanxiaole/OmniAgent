# config 包初始化文件

from .settings import (
    DASHSCOPE_API_KEY,
    OPENAI_API_KEY,
    MODEL_NAME,
    BASE_URL,
    TEMPERATURE,
    PERSIST_DIR,
    KNOWLEDGE_DIR,
    RAG_TOP_K,
    EMBEDDING_MODEL
)

__all__ = [
    "DASHSCOPE_API_KEY",
    "OPENAI_API_KEY",
    "MODEL_NAME",
    "BASE_URL",
    "TEMPERATURE",
    "PERSIST_DIR",
    "KNOWLEDGE_DIR",
    "RAG_TOP_K",
    "EMBEDDING_MODEL"
]
