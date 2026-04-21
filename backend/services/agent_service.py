from agent_core.agent import run_agent, clear_session as agent_clear_session
from agent_core.logger import get_logger

logger = get_logger(__name__)

async def get_agent_reply(message: str, thread_id: str) -> str:
    """调用 Agent 获取回复，thread_id 用于会话隔离和持久化
    
    Args:
        message: 用户输入的消息
        thread_id: 会话 ID，用于区分不同用户或会话
        
    Returns:
        str: Agent 的回复消息
    """
    try:
        # run_agent 是同步函数，FastAPI 会自动在线程池中执行
        reply = run_agent(message, thread_id)
        logger.info(f"Agent 调用成功，thread_id: {thread_id}")
        return reply
    except Exception as e:
        logger.error(f"Agent 调用失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        return "抱歉，服务暂时不可用，请稍后再试。"


def clear_session(thread_id: str) -> None:
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID
    """
    try:
        agent_clear_session(thread_id)
        logger.info(f"会话 {thread_id} 已清空")
    except Exception as e:
        logger.error(f"清空会话失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        raise