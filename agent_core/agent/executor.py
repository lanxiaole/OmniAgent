# Agent 执行器模块
import asyncio
import traceback
from typing import AsyncGenerator
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessageChunk
from agent_core.agent.checkpointer import get_checkpointer, get_async_checkpointer
from agent_core.agent.middleware import get_middlewares
from agent_core.agent.model_factory import get_llm_model
from agent_core.agent.config import SYSTEM_PROMPT
from agent_core.tools import TOOLS
from agent_core.logger import get_logger

logger = get_logger(__name__)


# ==================== 异常分级处理 ====================

def _classify_exception(e: Exception) -> str:
    """将异常分类为用户可理解的错误类型，并返回友好提示。

    分类优先级：
    1. OpenAI SDK 异常（AuthenticationError、RateLimitError 等）
    2. httpx 底层网络异常（ConnectError、TimeoutException 等）
    3. asyncio 取消异常（用户主动中止）
    4. 其他未知异常

    Args:
        e: 捕获到的异常实例

    Returns:
        str: 用户友好的错误提示信息
    """
    # 1. OpenAI SDK 异常（需延迟导入以避免循环依赖）
    try:
        from openai import (
            AuthenticationError,
            PermissionDeniedError,
            RateLimitError,
            NotFoundError,
            BadRequestError,
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            ConflictError,
            UnprocessableEntityError,
        )

        if isinstance(e, AuthenticationError):
            return "API Key 无效或已过期，请在 .env 文件中检查 LLM_API_KEY 配置。"

        if isinstance(e, PermissionDeniedError):
            return "当前 API Key 没有访问该模型的权限，请检查账户权限或更换 Key。"

        if isinstance(e, RateLimitError):
            return "请求过于频繁，已触发速率限制（429）。请稍后再试，或联系服务商提升配额。"

        if isinstance(e, NotFoundError):
            return f"模型不存在（404），请检查 LLM_MODEL 名称是否正确，以及服务商是否支持该模型。"

        if isinstance(e, BadRequestError):
            # 提取 API 返回的详细错误信息
            body = getattr(e, 'body', None)
            if isinstance(body, dict) and body.get('error', {}).get('message'):
                detail = body['error']['message']
                return f"请求参数错误：{detail}"
            return "请求参数错误（400），请检查输入内容是否合规。"

        if isinstance(e, APIConnectionError):
            return "无法连接到 AI 服务，请检查网络连接和 LLM_BASE_URL 是否正确。"

        if isinstance(e, APITimeoutError):
            return "请求超时，AI 服务响应过慢。请稍后重试，或检查网络状况。"

        if isinstance(e, InternalServerError):
            return "AI 服务端发生错误（5xx），这是服务端问题，请稍后重试。"

        if isinstance(e, ConflictError):
            return "请求冲突（409），可能资源状态已变更，请重试。"

        if isinstance(e, UnprocessableEntityError):
            return "请求无法处理（422），请检查输入内容格式是否正确。"

    except ImportError:
        pass

    # 2. httpx 底层网络异常
    try:
        import httpx

        if isinstance(e, httpx.ConnectTimeout):
            return "连接 AI 服务超时，请检查网络或 LLM_BASE_URL 是否可达。"

        if isinstance(e, httpx.ReadTimeout):
            return "接收 AI 响应超时，请稍后重试。"

        if isinstance(e, httpx.PoolTimeout):
            return "连接池耗尽，请稍后再试。"

        if isinstance(e, httpx.ConnectError):
            return "无法建立到 AI 服务的连接，请检查网络或 LLM_BASE_URL 是否正确。"

        if isinstance(e, httpx.ReadError):
            return "接收 AI 响应时网络中断，请检查网络连接后重试。"

        if isinstance(e, httpx.WriteError):
            return "发送请求时网络中断，请检查网络连接后重试。"

        if isinstance(e, httpx.HTTPStatusError):
            status_code = getattr(e, 'status_code', 0)
            return f"HTTP 请求失败（状态码 {status_code}），请检查 API 配置或稍后重试。"

    except ImportError:
        pass

    # 3. 用户主动取消
    if isinstance(e, asyncio.CancelledError):
        return ""  # 静默处理，不向用户显示错误

    # 4. 通用异常：提取异常消息
    error_msg = str(e)
    if error_msg:
        return f"发生错误：{error_msg[:200]}"

    return "抱歉，发生了未知错误，请稍后重试。"


def _log_exception(e: Exception, context: str) -> None:
    """记录异常的详细堆栈到日志，供开发者排查。

    Args:
        e: 捕获到的异常实例
        context: 异常发生的上下文描述（如 "run_agent" 或 "stream_agent"）
    """
    tb_text = traceback.format_exc()
    logger.error(
        f"[{context}] 异常类型: {type(e).__name__} | "
        f"异常信息: {str(e)} | "
        f"堆栈:\n{tb_text}"
    )

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

    Args:
        user_input: 用户输入
        thread_id: 对话线程 ID

    Returns:
        str: Agent 的回复，或用户友好的错误提示
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
        # 记录详细堆栈供排查
        _log_exception(e, "run_agent")
        # 返回用户友好的错误提示
        return _classify_exception(e)


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
    """流式获取 Agent 回复，逐 token 返回，并过滤掉内部摘要 token

    Args:
        user_input: 用户输入
        thread_id: 对话线程 ID

    Yields:
        str: AI 回复的 token 片段，或用户友好的错误提示
    """
    try:
        agent = await get_async_agent_executor()
        config = RunnableConfig(configurable={"thread_id": thread_id})

        # 第一步：获得原始的异步生成器
        raw_stream = agent.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode="messages"
        )

        # 第二步：创建一个过滤后的生成器
        async def filtered_stream():
            async for chunk in raw_stream:
                # 根据官方文档，chunk 是 (token, metadata) 元组
                token, metadata = chunk

                # 检查 token 是否是 AIMessageChunk 类型
                if not isinstance(token, AIMessageChunk):
                    continue

                # 过滤条件 1：排除内容为空的 token
                if not token.content:
                    continue

                # 过滤条件 2：排除包含摘要关键特征的 token
                content = token.content
                summarization_keywords = [
                    "## SESSION INTENT",
                    "## SUMMARY",
                    "## ARTIFACTS",
                    "## NEXT STEPS",
                    "SESSION INTENT",
                    "None — The user has"
                ]
                if any(keyword in content for keyword in summarization_keywords):
                    continue

                # 过滤条件 3：排除来自 "summarize" 或 "summarizer" 节点的 token
                node_name = metadata.get("langgraph_node", "")
                if "summar" in node_name.lower():
                    continue

                yield token

        # 第三步：遍历过滤后的生成器，yield 出干净的内容
        async for clean_token in filtered_stream():
            yield clean_token.content

    except asyncio.CancelledError:
        # 用户主动中止请求（前端 AbortController 触发），静默处理
        logger.info(f"[{thread_id}] 流式请求被用户主动中止")
        return

    except Exception as e:
        # 记录详细堆栈供排查
        _log_exception(e, "stream_agent")
        # 返回用户友好的错误提示
        error_msg = _classify_exception(e)
        if error_msg:
            yield error_msg


# 导出列表
__all__ = ["run_agent", "clear_session", "stream_agent"]
