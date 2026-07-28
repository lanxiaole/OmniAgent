import json
import sqlite3
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from agent_core.agent import run_agent, clear_session as agent_clear_session
from agent_core.agent.checkpointer import get_checkpointer, DB_PATH
from agent_core.logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)

async def get_agent_reply(message: str, thread_id: str) -> str:
    """调用 Agent 获取回复，thread_id 用于会话隔离和持久化

    Args:
        message: 用户输入的消息
        thread_id: 会话 ID，必需参数

    Returns:
        str: Agent 的回复消息，或用户友好的错误提示
    """
    try:
        # run_agent 是同步函数，FastAPI 会自动在线程池中执行
        # run_agent 内部已处理所有异常并返回友好提示
        reply = run_agent(message, thread_id)
        logger.info(f"Agent 调用成功，thread_id: {thread_id}")
        return reply
    except Exception as e:
        # 安全网：捕获 run_agent 调用本身的异常（理论上不会触发）
        logger.error(f"Agent 调用失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        return "抱歉，服务暂时不可用，请稍后再试。"


def get_session_history(thread_id: str) -> list[dict]:
    """从 LangGraph 检查点中读取会话历史消息

    通过 checkpointer.get() 获取最新检查点，提取 channel_values 中的 messages，
    过滤掉 ToolMessage 和空内容的消息，只返回 user 和 assistant 的对话。

    Args:
        thread_id: 会话 ID

    Returns:
        list[dict]: [{"role": "user"/"assistant", "content": "..."}]
    """
    try:
        # 创建独立的只读 checkpointer 连接，避免干扰主 Agent 的 checkpointer
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        from langgraph.checkpoint.sqlite import SqliteSaver
        reader = SqliteSaver(conn)
        reader.setup()

        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = reader.get(config)

        conn.close()

        if not checkpoint_tuple:
            logger.info(f"会话 {thread_id} 无检查点数据")
            return []

        # 提取 channel_values 中的 messages
        channel_values = checkpoint_tuple.get("channel_values", {})
        messages = channel_values.get("messages", [])

        result = []
        for msg in messages:
            # 只保留 HumanMessage 和 AIMessage
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                # 跳过 ToolMessage、SystemMessage 等
                continue

            content = msg.content if hasattr(msg, "content") else ""
            # 跳过空内容（如工具调用前的空 AIMessage）
            if not content or not content.strip():
                continue

            result.append({"role": role, "content": content})

        logger.info(f"会话 {thread_id} 读取到 {len(result)} 条历史消息")
        return result

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