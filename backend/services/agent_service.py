import json
import sqlite3
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from agent_core.agent import run_agent, clear_session as agent_clear_session
from agent_core.agent.checkpointer import get_checkpointer, DB_PATH
from agent_core.logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

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
        # 记录 AIMessage 中 tool_call 的位置，后续 ToolMessage 将结果回填
        tool_call_registry: dict[str, tuple[int, int]] = {}  # tool_call_id -> (result_index, tc_index)

        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({
                    "role": "user",
                    "content": msg.content if hasattr(msg, "content") else ""
                })

            elif isinstance(msg, AIMessage):
                content = msg.content if hasattr(msg, "content") else ""

                # 提取 reasoning_content
                reasoning = ""
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                    reasoning = msg.additional_kwargs.get("reasoning_content", "") or ""

                # 提取 tool_calls；checkpoint 中能存下来的表示已执行过，初始状态用 running
                tool_calls = None
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls = []
                    for tc in msg.tool_calls:
                        tc_entry = {
                            "id": tc.get("id", ""),
                            "name": tc.get("name", "unknown"),
                            "args": tc.get("args", {}),
                            "status": "running"
                        }
                        tool_calls.append(tc_entry)
                        tool_call_registry[tc_entry["id"]] = (len(result), len(tool_calls) - 1)

                entry: dict = {"role": "assistant", "content": content}
                if reasoning:
                    entry["reasoning"] = reasoning
                if tool_calls:
                    entry["toolCalls"] = tool_calls

                result.append(entry)

            elif isinstance(msg, ToolMessage):
                # 将工具结果回填到对应的 AIMessage.toolCalls，标记 success
                tc_id = getattr(msg, "tool_call_id", "")
                if tc_id and tc_id in tool_call_registry:
                    result_idx, tc_idx = tool_call_registry[tc_id]
                    target = result[result_idx]
                    if "toolCalls" in target and tc_idx < len(target["toolCalls"]):
                        target["toolCalls"][tc_idx]["result"] = str(msg.content) if msg.content else ""
                        target["toolCalls"][tc_idx]["status"] = "success"

            elif isinstance(msg, SystemMessage):
                # 检查是否为总结通知节点
                additional_kwargs = msg.additional_kwargs if hasattr(msg, "additional_kwargs") else {}
                if additional_kwargs.get("is_summary_notice"):
                    summary_data = additional_kwargs.get("summary_data", {})
                    result.append({
                        "role": "system",
                        "content": "",
                        "isSummaryNotice": True,
                        "summaryData": summary_data,
                    })

        # 后处理：合并连续的 assistant 消息
        # 合并条件：当前与下一条均为 assistant，且下一条没有 toolCalls 且 content 非空
        # 场景：AIMessage(toolCalls, content="") + AIMessage(content="回复") → 合并为一条
        # 场景：AIMessage(content="前文") + AIMessage(content="续文") → 合并（追加）
        merged = []
        i = 0
        while i < len(result):
            curr = result[i]
            next_msg = result[i + 1] if i + 1 < len(result) else None
            if (
                next_msg is not None
                and curr.get("role") == "assistant"
                and next_msg.get("role") == "assistant"
                and not next_msg.get("toolCalls")
                and next_msg.get("content", "").strip()
            ):
                # 将下一条 content 追加到当前 content 末尾（用换行分隔）
                curr_content = curr.get("content", "")
                next_content = next_msg.get("content", "")
                if curr_content.strip():
                    curr["content"] = curr_content + "\n" + next_content
                else:
                    # 当前 content 为空时，直接使用下一条 content，避免出现前导换行
                    curr["content"] = next_content
                # 合并 reasoning：当前没有但下一条有时补充
                if next_msg.get("reasoning") and not curr.get("reasoning"):
                    curr["reasoning"] = next_msg["reasoning"]
                merged.append(curr)
                i += 2  # 跳过下一条
            else:
                merged.append(curr)
                i += 1

        logger.info(f"会话 {thread_id} 读取到 {len(merged)} 条历史消息（原始 {len(result)} 条）")
        return merged

    except Exception as e:
        logger.error(f"获取会话历史失败，thread_id: {thread_id}，错误: {e}", exc_info=True)
        return []


def clear_session(thread_id: str) -> None:
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID，必需参数
    """
    try:
        agent_clear_session(thread_id)
        logger.info(f"会话 {thread_id} 已清空")
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