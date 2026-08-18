# 上下文统计路由模块
# 提供会话上下文状态统计 API，用于前端上下文信息面板展示

import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, HTTPException

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, get_buffer_string
from agent_core.agent.model_factory import get_llm_model
from agent_core.agent.checkpointer import DB_PATH
from agent_core.config.settings import get_active_system_prompt, get_model_context_window, get_llm_model_name
from agent_core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/context", tags=["context"])


def _get_token_counter() -> callable:
    """获取 Token 计数器"""
    try:
        model = get_llm_model()
        return model.get_num_tokens_from_messages
    except Exception:
        # 降级：使用简单的估算（每字符约 0.25 token）
        def _estimate_tokens_from_messages(messages: list) -> int:
            total = 0
            for msg in messages:
                content = getattr(msg, "content", "") or ""
                total += int(len(str(content)) * 0.25) + 1
            return total
        return _estimate_tokens_from_messages


def _get_single_token_counter() -> callable:
    """获取单文本 Token 计数器"""
    try:
        model = get_llm_model()
        return model.get_num_tokens
    except Exception:
        def _estimate(text: str) -> int:
            return int(len(text) * 0.25) + 1
        return _estimate


def _read_messages_from_checkpoint(thread_id: str) -> list:
    """从 Checkpoint 数据库读取会话消息

    Args:
        thread_id: 会话 ID

    Returns:
        list: 消息列表
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        from langgraph.checkpoint.sqlite import SqliteSaver
        reader = SqliteSaver(conn)
        reader.setup()

        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = reader.get(config)
        conn.close()

        if not checkpoint_tuple:
            return []

        channel_values = checkpoint_tuple.get("channel_values", {})
        messages = channel_values.get("messages", [])
        return messages
    except Exception as e:
        logger.error(f"读取会话 {thread_id} Checkpoint 失败: {e}")
        return []


def _detect_summary(messages: list) -> dict:
    """检测会话中是否有上下文总结

    从消息列表中查找 HumanMessage 且内容包含 "summary of the conversation" 特征，
    以此判断是否已触发过总结。

    Args:
        messages: 消息列表

    Returns:
        dict: 总结状态信息
    """
    summary_status = {
        "is_summarized": False,
        "triggered_at": None,
        "original_count": None,
        "preserved_count": None,
        "summary_tokens": 0,
    }

    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = str(msg.content or "")
            if "summary of the conversation" in content.lower():
                summary_status["is_summarized"] = True
                # 尝试从消息的 additional_kwargs 中获取时间
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                    created_at = msg.additional_kwargs.get("created_at")
                    if created_at:
                        summary_status["triggered_at"] = created_at
                break

    return summary_status


@router.get("/{thread_id}/stats")
async def get_context_stats(thread_id: str):
    """获取会话上下文统计信息

    统计逻辑说明：
    - 系统提示词：从当前场景配置中获取 System Prompt 文本
    - 对话历史：从 Checkpoint 数据库中读取所有消息
    - 按消息角色/类型细分为 6 类：用户消息、AI 回复、工具调用、工具结果、总结、手动上下文
    - 总 Token 数 = 系统提示词 + 对话消息（不重复计数）

    Args:
        thread_id: 会话的唯一标识符

    Returns:
        dict: 包含上下文统计信息的响应
    """
    try:
        # 1. 获取当前会话的所有消息
        messages = _read_messages_from_checkpoint(thread_id)

        # 2. 获取当前场景的系统提示词
        system_prompt = get_active_system_prompt()

        # 3. 获取 Token 计数器
        single_token_counter = _get_single_token_counter()

        # 4. 统计各部分 Token
        # 系统提示词
        system_prompt_tokens = single_token_counter(system_prompt) if system_prompt else 0

        # 按消息角色/类型细粒度分类统计 Token
        #   - 用户消息：HumanMessage（不含总结）
        #   - AI 回复：AIMessage（不含工具调用）
        #   - 工具调用：AIMessage（含工具调用，含调用参数）
        #   - 工具结果：ToolMessage
        #   - 上下文总结：HumanMessage 且内容含 "summary of the conversation"
        #   - 手动上下文：预留
        user_tokens = 0
        ai_reply_tokens = 0
        tool_call_tokens = 0
        tool_result_tokens = 0
        summary_tokens = 0
        manual_context_tokens = 0  # 预留，后续对接手动上下文功能

        for msg in messages:
            content = str(getattr(msg, "content", "") or "")
            tokens = single_token_counter(content)

            if isinstance(msg, HumanMessage) and "summary of the conversation" in content.lower():
                # 上下文总结消息
                summary_tokens += tokens
            elif isinstance(msg, HumanMessage):
                # 用户消息
                user_tokens += tokens
            elif isinstance(msg, AIMessage):
                tool_calls = getattr(msg, "tool_calls", None) or getattr(msg, "additional_kwargs", {}).get("tool_calls")
                if tool_calls:
                    # 工具调用：content + 调用参数
                    tool_call_tokens += tokens
                    for tc in tool_calls:
                        args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                        if isinstance(args, dict):
                            tool_call_tokens += single_token_counter(json.dumps(args, ensure_ascii=False))
                        elif isinstance(args, str):
                            tool_call_tokens += single_token_counter(args)
                else:
                    # AI 回复
                    ai_reply_tokens += tokens
            elif isinstance(msg, ToolMessage):
                # 工具执行结果
                tool_result_tokens += tokens
            else:
                # 其他类型（SystemMessage 等），归入用户消息
                user_tokens += tokens

        # 对话历史总 Token = 各类别之和
        history_tokens = user_tokens + ai_reply_tokens + tool_call_tokens + tool_result_tokens + summary_tokens + manual_context_tokens

        # 5. 检测总结
        summary_status = _detect_summary(messages)
        if summary_status["is_summarized"]:
            summary_status["summary_tokens"] = summary_tokens

        # 6. 获取模型上下文窗口大小
        model_name = get_llm_model_name() or ""
        max_context_window = get_model_context_window(model_name)

        # 7. 计算总 Token 和百分比
        # 总 Token = 系统提示词 + 对话历史（不重复计数）
        total_tokens = system_prompt_tokens + history_tokens
        usage_percentage = round((total_tokens / max_context_window) * 100, 1) if max_context_window > 0 else 0.0

        # 8. 组装响应
        data = {
            "thread_id": thread_id,
            "message_count": len(messages),
            "total_tokens": total_tokens,
            "max_context_window": max_context_window,
            "usage_percentage": usage_percentage,
            "breakdown": {
                "system_prompt": system_prompt_tokens,
                "history_messages": history_tokens,
                "user_messages": user_tokens,
                "ai_replies": ai_reply_tokens,
                "tool_calls": tool_call_tokens,
                "tool_results": tool_result_tokens,
                "summary": summary_tokens,
                "manual_context": manual_context_tokens,
            },
            "summary_status": summary_status,
        }

        logger.info(
            f"上下文统计: thread_id={thread_id}, "
            f"messages={len(messages)}, "
            f"total_tokens={total_tokens}/{max_context_window} ({usage_percentage}%), "
            f"user={user_tokens} ai={ai_reply_tokens} "
            f"tool_call={tool_call_tokens} tool_result={tool_result_tokens} "
            f"summary={summary_tokens}"
        )
        return {"success": True, "data": data}

    except Exception as e:
        logger.error(f"获取上下文统计失败: thread_id={thread_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取上下文统计失败: {e}")