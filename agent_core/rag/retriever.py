# RAG 检索模块

import os
from langchain_chroma import Chroma
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from .config import PERSIST_DIR, DASHSCOPE_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL, RAG_TOP_K
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


def load_vector_store():
    """加载已有向量库
    
    返回:
        Chroma | None: 向量库对象，如果不存在则返回 None
    """
    if os.path.exists(PERSIST_DIR):
        api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
        if not api_key:
            raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
        
        embeddings = DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=api_key
        )
        
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )
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
