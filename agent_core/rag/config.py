# rag 模块配置

import os
from agent_core.config.settings import VECTOR_STORE_DIR, KNOWLEDGE_DIR, RAG_TOP_K
from agent_core.config.settings import get_embedding_model, get_embedding_api_key, get_embedding_base_url

# 哈希文件路径（存放在 VECTOR_STORE_DIR 根目录，跨版本共享）
HASH_FILE = os.path.join(VECTOR_STORE_DIR, "content.hash")

# 活跃向量库版本指针文件
ACTIVE_POINTER = os.path.join(VECTOR_STORE_DIR, "active.txt")


def get_active_store_dir() -> str:
    """获取当前活跃的向量库目录路径（版本化目录或向后兼容的原始目录）"""
    if os.path.exists(ACTIVE_POINTER):
        try:
            with open(ACTIVE_POINTER, "r", encoding="utf-8") as f:
                version = f.read().strip()
            version_dir = os.path.join(VECTOR_STORE_DIR, version)
            if os.path.isdir(version_dir):
                return version_dir
            logger = get_logger(__name__)
            logger.warning(f"活跃版本目录 {version_dir} 不存在，回退到原始目录")
        except Exception:
            pass
    # 向后兼容：无指针时直接使用 VECTOR_STORE_DIR
    return VECTOR_STORE_DIR


def set_active_store_dir(version: str) -> None:
    """设置当前活跃的向量库版本"""
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    with open(ACTIVE_POINTER, "w", encoding="utf-8") as f:
        f.write(version)


def next_version_dir() -> tuple[str, str]:
    """生成下一个版本目录名称和路径

    返回:
        tuple[str, str]: (版本名称如 "v1", 版本目录绝对路径)
    """
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    max_ver = 0
    try:
        for entry in os.listdir(VECTOR_STORE_DIR):
            if entry.startswith("v") and entry[1:].isdigit():
                max_ver = max(max_ver, int(entry[1:]))
    except Exception:
        pass
    next_ver = f"v{max_ver + 1}"
    return next_ver, os.path.join(VECTOR_STORE_DIR, next_ver)


# 兼容旧名称：包装为函数，使用时自动调用 getter
EMBEDDING_MODEL = get_embedding_model
EMBEDDING_API_KEY = get_embedding_api_key
EMBEDDING_BASE_URL = get_embedding_base_url

__all__ = [
    "VECTOR_STORE_DIR",
    "KNOWLEDGE_DIR",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "EMBEDDING_BASE_URL",
    "RAG_TOP_K",
    "HASH_FILE",
    "ACTIVE_POINTER",
    "get_active_store_dir",
    "set_active_store_dir",
    "next_version_dir",
]
