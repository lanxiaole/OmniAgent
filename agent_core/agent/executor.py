# Agent 执行器模块
import asyncio
import json
from typing import AsyncGenerator, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessageChunk, ToolMessage
from agent_core.agent.checkpointer import get_async_checkpointer
from agent_core.agent.factory import AgentFactory
from agent_core.errors import classify_exception, log_exception
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 摘要关键词：这些内容不向前端推送
_SUMMARIZATION_KEYWORDS = [
    "## SESSION INTENT",
    "## SUMMARY",
    "## ARTIFACTS",
    "## NEXT STEPS",
    "SESSION INTENT",
    "None — The user has",
]


# 全局 Agent 执行器实例（使用工厂创建）
_factory = AgentFactory()
global_agent_executor = _factory.create_agent()


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
        log_exception(e, "run_agent", logger)
        # 返回用户友好的错误提示
        return classify_exception(e)


# 清空会话
def clear_session(thread_id: str = "default") -> None:
    """删除指定会话的 checkpoint

    参数:
        thread_id: 对话线程 ID
    """
    try:
        from agent_core.agent.checkpointer import get_checkpointer
        checkpointer = get_checkpointer()
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

        # 使用工厂创建异步 Agent
        factory = AgentFactory(checkpointer=async_checkpointer)
        agent = factory.create_agent()

        logger.info("异步 Agent 执行器创建成功")
        return agent
    except Exception as e:
        logger.error(f"创建异步 Agent 执行器失败: {e}")
        raise


def _safe_parse_json(text: str) -> Any:
    """安全解析 JSON 字符串，失败时返回原始字符串"""
    if not text:
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _flush_pending_tool_calls(pending: dict) -> list[dict]:
    """将累积的 tool_call_chunks 转为结构化事件，并清空 pending
    过滤掉 id 和 name 同时为空的无效条目（流式片段中的纯参数碎片）"""
    events = []
    for idx in sorted(pending.keys()):
        tc = pending[idx]
        tc_id = tc.get("id", "")
        tc_name = tc.get("name", "")
        # 过滤空碎片：id 和 name 都为空说明这只是参数片段，不是完整调用
        if not tc_id and not tc_name:
            continue
        args = _safe_parse_json(tc.get("args", ""))
        events.append({
            "type": "tool_call",
            "id": tc_id or f"tc_{idx}",
            "name": tc_name or "unknown",
            "args": args,
        })
    pending.clear()
    return events


# 异步流式获取 Agent 回复
async def stream_agent(user_input: str, thread_id: str = "default") -> AsyncGenerator[dict, None]:
    """流式获取 Agent 回复，产出结构化事件字典

    事件类型:
        {"type": "token", "content": "..."}             — 文本片段
        {"type": "reasoning", "content": "..."}          — 思考过程片段
        {"type": "tool_call", "id": "...", "name": "...", "args": {...}}  — 工具调用
        {"type": "tool_result", "id": "...", "result": "..."}  — 工具结果
        {"type": "error", "message": "..."}              — 错误

    Args:
        user_input: 用户输入
        thread_id: 对话线程 ID

    Yields:
        dict: 结构化事件
    """
    try:
        agent = await get_async_agent_executor()
        config = RunnableConfig(configurable={"thread_id": thread_id})

        raw_stream = agent.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode="messages"
        )

        # 累积流式工具调用片段：{index: {"id": ..., "name": ..., "args": "部分JSON"}}
        pending_tool_calls: dict[int, dict] = {}

        async for chunk, metadata in raw_stream:
            # 过滤摘要节点
            node_name = metadata.get("langgraph_node", "")
            if "summar" in node_name.lower():
                continue

            # ---- 处理 AIMessageChunk（AI 输出的文本/工具调用/思考过程） ----
            if isinstance(chunk, AIMessageChunk):
                # 1. 思考过程（reasoning_content，部分模型如 DeepSeek 支持）
                reasoning = ""
                if hasattr(chunk, "additional_kwargs"):
                    reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                if reasoning:
                    yield {"type": "reasoning", "content": reasoning}

                # 2. 文本内容
                content = chunk.content or ""
                if content and isinstance(content, str):
                    # 过滤摘要关键词
                    if any(kw in content for kw in _SUMMARIZATION_KEYWORDS):
                        continue
                    yield {"type": "token", "content": content}

                # 3. 工具调用 — 流式片段累积（唯一的 tool_call 来源）
                # 不直接 yield chunk.tool_calls，避免与 pending 累积产生重复事件
                tool_call_chunks = getattr(chunk, "tool_call_chunks", None) or []
                if tool_call_chunks:
                    for tc_chunk in tool_call_chunks:
                        idx = tc_chunk.get("index", 0)
                        if idx not in pending_tool_calls:
                            pending_tool_calls[idx] = {
                                "id": tc_chunk.get("id", ""),
                                "name": tc_chunk.get("name", ""),
                                "args": "",
                            }
                        else:
                            # 补充可能后续到达的 id/name
                            if tc_chunk.get("id"):
                                pending_tool_calls[idx]["id"] = tc_chunk["id"]
                            if tc_chunk.get("name"):
                                pending_tool_calls[idx]["name"] = tc_chunk["name"]
                        # 累积参数片段
                        pending_tool_calls[idx]["args"] += tc_chunk.get("args", "")

            # ---- 处理 ToolMessage（工具执行结果） ----
            elif isinstance(chunk, ToolMessage):
                # 先 flush 所有 pending 的工具调用
                if pending_tool_calls:
                    for event in _flush_pending_tool_calls(pending_tool_calls):
                        yield event

                # 提取工具结果
                result_content = chunk.content
                if isinstance(result_content, str):
                    result_data = _safe_parse_json(result_content)
                else:
                    result_data = result_content

                yield {
                    "type": "tool_result",
                    "id": chunk.tool_call_id,
                    "result": result_data,
                }

        # 流结束前 flush 残留的 pending
        if pending_tool_calls:
            for event in _flush_pending_tool_calls(pending_tool_calls):
                yield event

    except asyncio.CancelledError:
        # 用户主动中止请求（前端 AbortController 触发），静默处理
        logger.info(f"[{thread_id}] 流式请求被用户主动中止")
        return

    except Exception as e:
        # 记录详细堆栈供排查
        log_exception(e, "stream_agent", logger)
        # 返回用户友好的错误提示
        error_msg = classify_exception(e)
        if error_msg:
            yield {"type": "error", "message": error_msg}


# 导出列表
__all__ = ["run_agent", "clear_session", "stream_agent"]
