# RAG 检索模块

import os
from langchain_chroma import Chroma
from agent_core.config.embedding import create_embeddings
from .config import VECTOR_STORE_DIR, get_active_store_dir, RAG_TOP_K
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 模块级缓存：避免每次检索都重新加载 Chroma 和 Embeddings
_vector_store = None


def reset_vector_store_cache():
    """重置向量库缓存（在重建向量库后调用）"""
    global _vector_store
    _vector_store = None
    logger.info("向量库缓存已重置")


def load_vector_store():
    """加载已有向量库（带单例缓存）

    首次调用时初始化 Chroma 和 Embeddings，后续调用直接返回缓存实例。
    在 build_vector_store() 重建后，会通过 reset_vector_store_cache() 清空缓存。

    返回:
        Chroma | None: 向量库对象，如果不存在则返回 None
    """
    global _vector_store

    if _vector_store is not None:
        return _vector_store

    store_dir = get_active_store_dir()
    if os.path.exists(store_dir):
        logger.info(f"首次加载向量库: {store_dir}")
        embeddings = create_embeddings()
        _vector_store = Chroma(
            persist_directory=store_dir,
            embedding_function=embeddings
        )
        logger.info("向量库加载完成，已缓存")
        return _vector_store
    else:
        return None


def retrieve(query: str, top_k: int = RAG_TOP_K) -> list[str]:
    """检索相关文档
    
    参数:
        query: 查询字符串
        top_k: 返回的文档数量
        
    返回:
        list[str]: 检索到的文档内容列表
    """
    try:
        # 记录查询
        logger.debug(f"检索查询: {query}")
        
        # 加载向量库
        vector_store = load_vector_store()
        
        if not vector_store:
            logger.warning("向量库不存在，请先运行 build_vector_store() 构建向量库")
            return []
        
        # 相似度搜索
        results = vector_store.similarity_search(query, k=top_k)
        
        # 记录检索结果数量
        logger.info(f"检索到 {len(results)} 个文档")
        
        # 返回文档内容列表
        return [result.page_content for result in results]
    except Exception as e:
        logger.error(f"RAG 错误: {e}")
        return []


def get_retriever(top_k: int = RAG_TOP_K):
    """获取向量库的检索器对象
    
    参数:
        top_k: 返回的文档数量
        
    返回:
        Retriever: 向量库检索器对象
    """
    vector_store = load_vector_store()
    if not vector_store:
        raise Exception("向量库不存在，请先运行 build_vector_store() 构建向量库")
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": top_k, "fetch_k": 20}
    )


def retrieve_docs(question: str, top_k: int = RAG_TOP_K) -> list[str]:
    """检索并返回文档内容列表（便捷函数）"""
    retriever = get_retriever(top_k=top_k)
    docs = retriever.invoke(question)
    return [doc.page_content for doc in docs]


def retrieve_docs_with_metadata(question: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """
    返回包含 page_content 和 metadata 的文档列表，用于前端沙盒展示。

    返回格式:
        [
            {
                "content": "文档内容...",
                "metadata": {"source": "file.md", "section": "标题", ...}
            }
        ]
    """
    retriever = get_retriever(top_k=top_k)
    docs = retriever.invoke(question)
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]
