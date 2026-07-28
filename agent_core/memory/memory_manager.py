# 长期记忆管理模块
# 实现基于向量检索的用户长期记忆存储和检索功能

import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from agent_core.config.settings import PERSIST_DIR, EMBEDDING_MODEL, EMBEDDING_API_KEY, EMBEDDING_BASE_URL
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 用户记忆集合名称，与 RAG 知识库隔离
MEMORY_COLLECTION_NAME = "user_memory"

# 模块级缓存：避免每次操作都重新初始化 Chroma 和 Embeddings
_memory_store_instance = None


def _get_embeddings():
    """根据 base_url 自动选择 Embedding 客户端

    - 阿里云百炼（dashscope）→ DashScopeEmbeddings（兼容新版模型）
    - 其他（OpenAI 等）→ OpenAIEmbeddings（OpenAI 兼容接口）
    """
    if "dashscope" in EMBEDDING_BASE_URL or "aliyun" in EMBEDDING_BASE_URL:
        return DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=EMBEDDING_API_KEY,
        )
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=EMBEDDING_BASE_URL,
        api_key=EMBEDDING_API_KEY,
    )


class UserMemoryStore:
    """用户长期记忆存储类

    使用 Chroma 向量数据库存储用户信息，支持添加记忆和相似度检索。
    通过 collection_name 与 RAG 知识库隔离，共享同一存储目录。
    """

    def __init__(self, persist_directory: str = PERSIST_DIR):
        """初始化用户记忆存储

        参数:
            persist_directory: 向量库持久化目录，默认为项目的 chroma_db 目录
        """
        self.persist_directory = persist_directory
        self.embeddings = _get_embeddings()
        
        # 创建或加载 Chroma 集合（使用独立的 collection_name 隔离）
        self.chroma = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=MEMORY_COLLECTION_NAME
        )
        logger.info(f"用户记忆存储已初始化，集合: {MEMORY_COLLECTION_NAME}")

    def add_memory(self, content: str) -> None:
        """添加一条用户记忆

        参数:
            content: 记忆内容字符串，如"用户喜欢吃辣"
        """
        try:
            self.chroma.add_texts([content])
            logger.info(f"用户记忆添加成功: {content[:50]}..." if len(content) > 50 else f"用户记忆添加成功: {content}")
        except Exception as e:
            logger.error(f"添加用户记忆失败: {e}")
            raise

    def similarity_search(self, query: str, top_k: int = 5) -> list[str]:
        """根据查询检索相关记忆

        参数:
            query: 查询字符串
            top_k: 返回的记忆数量，默认为 5

        返回:
            list[str]: 检索到的记忆内容列表，按相似度排序
        """
        try:
            results = self.chroma.similarity_search(query, k=top_k)
            logger.info(f"用户记忆检索成功，查询: {query}, 返回 {len(results)} 条")
            return [result.page_content for result in results]
        except Exception as e:
            logger.error(f"检索用户记忆失败: {e}")
            return []

    def get_memory_count(self) -> int:
        """获取当前存储的记忆数量

        返回:
            int: 记忆总数
        """
        try:
            count = self.chroma._collection.count()
            logger.debug(f"当前用户记忆数量: {count}")
            return count
        except Exception as e:
            logger.error(f"获取记忆数量失败: {e}")
            return 0


def get_user_memory_store() -> UserMemoryStore:
    """获取用户记忆存储实例（单例模式）

    返回:
        UserMemoryStore: 全局唯一的用户记忆存储实例
    """
    global _memory_store_instance
    if _memory_store_instance is None:
        _memory_store_instance = UserMemoryStore()
    return _memory_store_instance


def reset_memory_store_cache():
    """重置记忆存储缓存

    在需要重新初始化时调用（如配置变更后）
    """
    global _memory_store_instance
    _memory_store_instance = None
    logger.info("用户记忆存储缓存已重置")