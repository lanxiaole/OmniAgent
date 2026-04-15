# RAG 工具模块

from langchain_core.tools import tool
from rag.chain import run_rag_chain
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool

def query_knowledge(question: str) -> str:
    """从知识库中查询信息
    
    参数:
        question: 用户的问题
        
    返回:
        str: 知识库中的相关信息
    """
    try:
        logger.debug(f"调用知识库查询工具，问题: {question}")
        result = run_rag_chain(question)
        logger.info("知识库查询成功")
        return result
    except Exception as e:
        logger.error(f"知识库查询错误: {e}")
        return "抱歉，我暂时无法回答这个问题。"
