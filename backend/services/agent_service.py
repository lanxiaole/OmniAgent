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


def _process_raw_messages(messages: list) -> list[dict]:
    """处理原始 LangChain 消息列表，转换为前端可用的 dict 格式

    与 get_session_history 中的消息处理逻辑相同，提取为独立函数
    以便同时在检查点消息和全量历史消息上使用。

    Args:
        messages: 原始 LangChain 消息列表

    Returns:
        list[dict]: 处理后的消息字典列表（未合并 assistant 连续消息）
    """
    result = []
    tool_call_registry: dict[str, tuple[int, int]] = {}

    for msg in messages:
        if isinstance(msg, HumanMessage):
            # 跳过总结中间件生成的总结 HumanMessage
            additional_kwargs = msg.additional_kwargs if hasattr(msg, "additional_kwargs") else {}
            if additional_kwargs.get("lc_source") == "summarization":
                continue
            result.append({
                "role": "user",
                "content": msg.content if hasattr(msg, "content") else ""
            })

        elif isinstance(msg, AIMessage):
            content = msg.content if hasattr(msg, "content") else ""
            reasoning = ""
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                reasoning = msg.additional_kwargs.get("reasoning_content", "") or ""

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
            tc_id = getattr(msg, "tool_call_id", "")
            if tc_id and tc_id in tool_call_registry:
                result_idx, tc_idx = tool_call_registry[tc_id]
                target = result[result_idx]
                if "toolCalls" in target and tc_idx < len(target["toolCalls"]):
                    target["toolCalls"][tc_idx]["result"] = str(msg.content) if msg.content else ""
                    target["toolCalls"][tc_idx]["status"] = "success"

        elif isinstance(msg, SystemMessage):
            additional_kwargs = msg.additional_kwargs if hasattr(msg, "additional_kwargs") else {}
            if additional_kwargs.get("is_summary_notice"):
                summary_data = additional_kwargs.get("summary_data", {})
                result.append({
                    "role": "system",
                    "content": "",
                    "isSummaryNotice": True,
                    "summaryData": summary_data,
                })

    return result


def _merge_assistant_messages(messages: list[dict]) -> list[dict]:
    """合并连续的 assistant 消息

    处理条件：当前与下一条均为 assistant，且下一条没有 toolCalls 且 content 非空
    场景：AIMessage(toolCalls, content="") + AIMessage(content="回复") → 合并为一条

    Args:
        messages: 消息字典列表

    Returns:
        list[dict]: 合并后的消息列表
    """
    merged = []
    i = 0
    while i < len(messages):
        curr = messages[i]
        next_msg = messages[i + 1] if i + 1 < len(messages) else None
        if (
            next_msg is not None
            and curr.get("role") == "assistant"
            and next_msg.get("role") == "assistant"
            and not next_msg.get("toolCalls")
            and next_msg.get("content", "").strip()
        ):
            curr_content = curr.get("content", "")
            next_content = next_msg.get("content", "")
            if curr_content.strip():
                curr["content"] = curr_content + "\n" + next_content
            else:
                curr["content"] = next_content
            if next_msg.get("reasoning") and not curr.get("reasoning"):
                curr["reasoning"] = next_msg["reasoning"]
            merged.append(curr)
            i += 2
        else:
            merged.append(curr)
            i += 1
    return merged


def get_session_history(thread_id: str) -> list[dict]:
    """从 LangGraph 检查点中读取会话历史消息

    优先从全量历史文件恢复（如果存在），再补充检查点中的新增消息。
    全量历史文件由总结中间件在压缩触发时保存，确保被压缩的历史对话不会丢失。

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

        # 1. 尝试加载全量历史文件（由总结中间件在压缩时保存）
        from agent_core.agent.middleware import _load_full_history
        full_msgs = _load_full_history(thread_id)

        if full_msgs:
            file_result = _process_raw_messages(full_msgs)

            # 检查点还存在时，补充检查点中新增的消息
            if checkpoint_tuple:
                channel_values = checkpoint_tuple.get("channel_values", {})
                checkpoint_messages = channel_values.get("messages", [])
                checkpoint_result = _process_raw_messages(checkpoint_messages)

                # 查找检查点中的总结通知
                summary_notice = None
                notice_idx = -1
                for i, msg in enumerate(checkpoint_result):
                    if msg.get("isSummaryNotice"):
                        summary_notice = msg
                        notice_idx = i
                        break

                if summary_notice is not None:
                    # 获取保留消息数
                    preserved_count = summary_notice.get("summaryData", {}).get("preserved_count", 0)
                    # 检查点中的消息结构：总结通知 + 保留消息(preserved_count条) + 新增消息
                    # 跳过总结通知和保留消息（已在文件结果中），只取新增消息
                    new_messages = checkpoint_result[notice_idx + 1 + preserved_count:]
                    # 无论是否有新增消息，都要包含总结通知
                    result = file_result + [summary_notice] + new_messages
                    if new_messages:
                        logger.info(
                            f"会话 {thread_id} 从全量历史恢复 {len(file_result)} 条历史 + "
                            f"{len(new_messages)} 条新增消息"
                        )
                    else:
                        logger.info(
                            f"会话 {thread_id} 从全量历史恢复 {len(file_result)} 条消息"
                        )
                    return _merge_assistant_messages(result)

            # 没有检查点或没有新增消息，直接返回文件结果
            logger.info(f"会话 {thread_id} 从全量历史恢复 {len(file_result)} 条消息")
            return _merge_assistant_messages(file_result)

        # 2. 没有全量历史文件，从检查点加载
        if not checkpoint_tuple:
            logger.info(f"会话 {thread_id} 无检查点数据")
            return []

        channel_values = checkpoint_tuple.get("channel_values", {})
        messages = channel_values.get("messages", [])

        result = _process_raw_messages(messages)
        merged = _merge_assistant_messages(result)

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
        # 同时删除全量历史文件，避免残留
        from agent_core.agent.middleware import _delete_full_history
        _delete_full_history(thread_id)
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