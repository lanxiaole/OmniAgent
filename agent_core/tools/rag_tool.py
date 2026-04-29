# RAG 工具模块

from langchain_core.tools import tool
from agent_core.rag.retriever import retrieve_docs
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool

def identify_user(question: str) -> str:
    """仅在用户明确询问关于其自身的基本身份信息时调用。这包括问“我是谁”或“你是谁”这类直接问题。
    在其他任何情况下，绝对不要调用此工具。
    调用示例：
    - 用户: "我是谁呀" -> 调用 identify_user
    - 用户: "你是谁" -> 调用 identify_user
    - 用户: "我刚才说了啥" -> 不要调用
    - 用户: "我都问过你啥" -> 不要调用
    - 用户: "我都跟你说了什么" -> 不要调用
    """
    try:
        logger.debug(f"调用知识库检索，问题: {question}")
        docs = retrieve_docs(question)
        if not docs:
            return "未找到相关信息。"
        result = "\n\n".join(docs)
        logger.info(f"知识库检索成功，返回 {len(docs)} 条文档")
        return result
    except Exception as e:
        logger.error(f"知识库检索错误: {e}")
        return "抱歉，我暂时无法回答这个问题。"
