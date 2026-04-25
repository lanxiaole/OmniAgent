# Agent 执行器模块
import asyncio
from typing import AsyncGenerator
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from agent_core.agent.checkpointer import get_checkpointer, get_async_checkpointer
from agent_core.agent.middleware import get_middlewares
from agent_core.agent.model_factory import get_llm_model
from agent_core.agent.config import SYSTEM_PROMPT
from agent_core.tools import TOOLS
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 获取依赖实例
checkpointer = get_checkpointer()
middlewares = get_middlewares()
model = get_llm_model()


# 创建 Agent 执行器
def create_agent_executor():
    """创建 Agent 执行器"""
    try:
        logger.info("创建 Agent 执行器（带 Checkpointer 和 SummarizationMiddleware）...")
        
        # 打印 TOOLS 名称列表以便调试
        tool_names = [tool.name for tool in TOOLS]
        logger.debug(f"可用工具列表: {tool_names}")
        
        # 创建 Agent
        agent = create_agent(
            model=model,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
            middleware=middlewares,
        )
        
        logger.info("Agent 执行器创建成功")
        return agent
    except Exception as e:
        logger.error(f"创建 Agent 执行器失败: {e}")
        raise


# 全局 Agent 执行器实例
global_agent_executor = create_agent_executor()


# 执行 Agent 调用
def run_agent(user_input: str, thread_id: str = "default") -> str:
    """执行 Agent 调用，对话状态自动通过 checkpointer 持久化
    
    参数:
        user_input: 用户输入
        thread_id: 对话线程 ID
        
    返回:
        str: Agent 的回复
    """
    try:
        logger.debug(f"执行 Agent 调用，输入: {user_input}, thread_id: {thread_id}")
        
        # 构造 RunnableConfig
        config = RunnableConfig(configurable={"thread_id": thread_id})
        
        # 调用 Agent
        result = global_agent_executor.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )
        
        assistant_reply = result["messages"][-1].content
        logger.info("Agent 调用成功")
        return assistant_reply
    except Exception as e:
        logger.error(f"Agent 调用失败: {e}")
        return "抱歉，我暂时无法回答这个问题。"


# 清空会话
def clear_session(thread_id: str = "default") -> None:
    """删除指定会话的 checkpoint
    
    参数:
        thread_id: 对话线程 ID
    """
    try:
        if hasattr(checkpointer, 'delete_thread'):
            checkpointer.delete_thread(thread_id)
            logger.info(f"会话 {thread_id} 已清空")
        else:
            logger.warning("当前 Checkpointer 不支持删除线程操作")
    except Exception as e:
        logger.error(f"清空会话失败: {e}")


# 异步获取 Agent 执行器
async def get_async_agent_executor():
    """异步获取 Agent 执行器"""
    try:
        logger.info("创建异步 Agent 执行器（带异步 Checkpointer 和 SummarizationMiddleware）...")
        
        # 获取异步 checkpointer
        async_checkpointer = await get_async_checkpointer()
        
        # 打印 TOOLS 名称列表以便调试
        tool_names = [tool.name for tool in TOOLS]
        logger.debug(f"可用工具列表: {tool_names}")
        
        # 创建 Agent
        agent = create_agent(
            model=model,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=async_checkpointer,
            middleware=middlewares,
        )
        
        logger.info("异步 Agent 执行器创建成功")
        return agent
    except Exception as e:
        logger.error(f"创建异步 Agent 执行器失败: {e}")
        raise


# 全局异步 Agent 执行器实例（按需初始化）


# 异步流式获取 Agent 回复
async def stream_agent(user_input: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    """异步流式获取 Agent 回复，逐 token 返回。"""
    try:
        # 确保使用异步 checkpointer 初始化的 Agent
        agent = await get_async_agent_executor()
        config = RunnableConfig(configurable={"thread_id": thread_id})
        
        # 关键：stream_mode 设为 "messages"
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode="messages"  # 正确的模式
        ):
            # 根据官方文档，chunk 是 (token, metadata) 元组
            token, metadata = chunk
            if hasattr(token, 'content') and token.content:
                yield token.content
                
    except Exception as e:
        from agent_core.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Agent 流式调用失败: {e}", exc_info=True)
        yield "抱歉，流式输出时发生错误。"


# 导出列表
__all__ = ["run_agent", "clear_session", "stream_agent"]
