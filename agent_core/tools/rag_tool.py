# RAG 工具模块

from langchain_core.tools import tool
from agent_core.rag.retriever import retrieve_docs
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool

def search_knowledge(question: str) -> str:
    """【知识库】检索知识库中的文档内容。知识库由用户上传和管理，可包含项目文档、技术方案、笔记、参考资料等任意知识内容。

    使用场景：当用户询问与文档/知识相关的问题时调用此工具。
    - 用户: "编码规范是什么" -> 调用 search_knowledge
    - 用户: "这个项目用了什么技术栈" -> 调用 search_knowledge
    - 用户: "怎么部署" -> 调用 search_knowledge
    - 用户: "我刚才说了啥" -> 不要调用（这是对话历史问题）

    注意：知识库与记忆库是独立的两个系统。知识库存文档类知识，记忆库存用户个人信息和偏好。
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
