import json
import sqlite3
from pathlib import Path
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
        # 数据库文件路径
        DATA_DIR = Path(__file__).parent.parent.parent / "agent_core" / "data"
        DB_PATH = DATA_DIR / "agent_checkpoints.db"
        
        # 创建数据库连接
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        cursor = conn.cursor()
        
        # 查询最新的 checkpoint
        cursor.execute("""
            SELECT checkpoint FROM checkpoints 
            WHERE thread_id = ? 
            ORDER BY checkpoint_id DESC 
            LIMIT 1
        """, (thread_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # 解析 checkpoint JSON
            checkpoint = json.loads(result[0])
            messages = checkpoint.get("messages", [])
            
            # 转换为前端格式
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    formatted_messages.append({"role": role, "content": content})
                else:
                    # 处理 LangChain 消息对象
                    if hasattr(msg, "role") and hasattr(msg, "content"):
                        formatted_messages.append({"role": msg.role, "content": msg.content})
            
            return formatted_messages
        else:
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
            
            # 删除指定 thread_id 的所有 checkpoint
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