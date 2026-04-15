# RAG 工具模块

from langchain_core.tools import tool
from rag.chain import run_rag_chain
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool

def query_knowledge(question: str) -> str:
    """当用户询问关于他/她自己的个人信息（如名字、家乡、学校、技术栈、项目细节、学习经历、游戏喜好、实习计划、感冒流程、饮水习惯等）时，必须使用此工具从知识库中查找答案。绝对不要用自己的知识回答个人信息问题。"""
    try:
        logger.debug(f"调用知识库查询工具，问题: {question}")
        result = run_rag_chain(question)
        logger.info("知识库查询成功")
        return result
    except Exception as e:
        logger.error(f"知识库查询错误: {e}")
        return "抱歉，我暂时无法回答这个问题。"
