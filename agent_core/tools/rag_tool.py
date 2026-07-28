# RAG 工具模块

from langchain_core.tools import tool
from agent_core.rag.retriever import retrieve_docs
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool

def search_personal_knowledge(question: str) -> str:
    """检索用户存储在知识库中的个人信息、偏好、项目、经历等。当用户询问与自己相关的事实性问题时调用。
    调用示例：
    - 用户: "我是谁呀" -> 调用 search_personal_knowledge
    - 用户: "我的博客项目用什么技术" -> 调用 search_personal_knowledge
    - 用户: "我喜欢什么" -> 调用 search_personal_knowledge
    - 用户: "我刚才说了啥" -> 不要调用（这是对话历史问题）
    - 用户: "我都问过你啥" -> 不要调用（这是对话历史问题）
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
