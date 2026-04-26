import json
import sqlite3
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from agent_core.agent import run_agent, clear_session as agent_clear_session
from agent_core.logger import get_logger

logger = get_logger(__name__)

async def get_agent_reply(message: str, thread_id: str) -> str:
    """调用 Agent 获取回复，thread_id 用于会话隔离和持久化
    
    Args:
        message: 用户输入的消息
        thread_id: 会话 ID，必需参数
        
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


def get_session_history(thread_id: str) -> list[dict]:
    """获取指定会话的历史消息
    
    Args:
        thread_id: 会话 ID，必需参数
        
    Returns:
        list[dict]: 历史消息列表，格式为 [{"role": "user"/"assistant", "content": ...}]
    """
    try:
        # 直接返回空列表，因为我们现在使用前端本地存储
        logger.info(f"获取会话历史，thread_id: {thread_id}，使用前端本地存储")
        return []
    except Exception as e:
        logger.error(f"获取会话历史失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        return []


def clear_session(thread_id: str) -> None:
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID，必需参数
    """
    try:
        # 先尝试调用 agent_clear_session
        agent_clear_session(thread_id)
        logger.info(f"会话 {thread_id} 已清空")
    except AttributeError:
        # 如果 agent_clear_session 不存在，直接操作数据库
        try:
            # 数据库文件路径
            DATA_DIR = Path(__file__).parent.parent.parent / "agent_core" / "data"
            DB_PATH = DATA_DIR / "agent_checkpoints.db"
            
            # 创建数据库连接
            conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            cursor = conn.cursor()
            
            # 删除指定 thread_id 的所有记录
            cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"会话 {thread_id} 已清空")
        except Exception as e:
            logger.error(f"清空会话失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"清空会话失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        raise


async def stream_agent_reply(message: str, thread_id: str) -> AsyncGenerator[str, None]:
    """流式调用 Agent，逐 token 返回（支持取消）"""
    from agent_core.agent.executor import stream_agent
    
    try:
        async for token in stream_agent(message, thread_id):
            yield token
    except asyncio.CancelledError:
        # 客户端断开，优雅中止
        logger.info(f"Agent 流式任务被取消，thread_id: {thread_id}")
    # 注意：不要吞掉其他异常，让上层处理