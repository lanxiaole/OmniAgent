from agent_core.agent import run_agent
from agent_core.logger import get_logger
import asyncio

logger = get_logger(__name__)


async def get_agent_reply(message: str, thread_id: str) -> str:
    """获取Agent的回复
    
    Args:
        message: 用户输入的消息
        thread_id: 会话ID
    
    Returns:
        str: Agent的回复消息
    """
    try:
        # 异步调用同步函数 run_agent
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, run_agent, message, thread_id)
        return reply
    except Exception as e:
        # 捕获所有异常并记录错误
        logger.error(f"Error in agent service: {str(e)}")
        # 返回通用错误提示
        return "抱歉，服务暂时不可用，请稍后再试。"
