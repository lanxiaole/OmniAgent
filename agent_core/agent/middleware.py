# 中间件配置模块
# 提供消息总结中间件和人工审批中间件

import uuid
import threading
import os
from datetime import datetime
from typing import Any, Dict, Optional, cast
from langchain.agents.middleware import SummarizationMiddleware
from langchain.agents.middleware.types import AgentMiddleware, AgentState, ContextT, ResponseT
from langchain_core.messages import SystemMessage
from langgraph.runtime import Runtime
from agent_core.agent.model_factory import get_summarizer_model
from agent_core.config.settings import (
    WORKSPACE_DIR,
    CONTEXT_SUMMARY_MESSAGE_TRIGGER,
    CONTEXT_SUMMARY_KEEP_MESSAGES,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 人工审批（Human-in-the-loop）中间件
# =============================================================================

# 代码行数审批阈值（可配置）
APPROVAL_CODE_LINE_THRESHOLD = 50

# Python 危险操作模式列表
DANGEROUS_PATTERNS = [
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "__import__('os')",
    "shutil.rmtree",
    "os.remove(",
    "os.unlink(",
    "os.rmdir(",
    "os.removedirs(",
]

# 全局审批状态
_pending_approvals: Dict[str, Dict[str, Any]] = {}
_pending_approvals_lock = threading.Lock()
_approval_events: Dict[str, threading.Event] = {}


class HumanApprovalMiddleware:
    """人工审批中间件

    在工具调用前检查是否需要人工审批。
    触发条件：
    - write_file 写入路径不在 workspace/ 内
    - execute_python 代码行数超过阈值
    - execute_python 包含危险操作
    - delete_file 操作
    """

    def __init__(self, code_line_threshold: int = APPROVAL_CODE_LINE_THRESHOLD):
        self.code_line_threshold = code_line_threshold

    @staticmethod
    def check_tool(tool_name: str, tool_args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检查工具调用是否需要审批

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            如果需要审批，返回审批信息字典；否则返回 None
        """
        if tool_name == "write_file":
            file_path = tool_args.get("file_path", "")
            safe_path = os.path.abspath(os.path.expanduser(file_path))
            workspace_path = os.path.abspath(WORKSPACE_DIR)
            if not safe_path.startswith(workspace_path):
                return {
                    "reason": f"写入路径不在工作区内: {file_path}",
                    "tool": tool_name,
                    "args": dict(tool_args),
                }

        if tool_name == "execute_python":
            code = tool_args.get("code", "")
            lines = code.strip().split("\n")
            code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))

            # 检查是否包含危险操作
            for pattern in DANGEROUS_PATTERNS:
                if pattern in code:
                    return {
                        "reason": f"代码包含危险操作: {pattern}",
                        "tool": tool_name,
                        "args": dict(tool_args),
                    }

            # 检查代码行数是否超过阈值
            if code_lines > APPROVAL_CODE_LINE_THRESHOLD:
                return {
                    "reason": f"代码行数超过审批阈值 ({code_lines} > {APPROVAL_CODE_LINE_THRESHOLD})",
                    "tool": tool_name,
                    "args": dict(tool_args),
                }

        if tool_name == "delete_file":
            return {
                "reason": "删除文件操作需要审批",
                "tool": tool_name,
                "args": dict(tool_args),
            }

        return None


def create_approval_request(tool_name: str, tool_args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """创建审批请求

    Args:
        tool_name: 工具名称
        tool_args: 工具参数

    Returns:
        审批请求信息字典，如果不需要审批则返回 None
    """
    approval_info = HumanApprovalMiddleware.check_tool(tool_name, tool_args)
    if not approval_info:
        return None

    request_id = str(uuid.uuid4())
    request_data = {
        "request_id": request_id,
        "tool": tool_name,
        "args": tool_args,
        "reason": approval_info["reason"],
        "status": "pending",  # pending | approved | rejected
    }

    with _pending_approvals_lock:
        _pending_approvals[request_id] = request_data
        _approval_events[request_id] = threading.Event()

    logger.info(f"审批请求已创建: {request_id}, 工具: {tool_name}, 原因: {approval_info['reason']}")
    return request_data


def wait_for_approval(request_id: str, timeout: float = 300) -> bool:
    """等待审批结果（阻塞当前线程）

    Args:
        request_id: 审批请求 ID
        timeout: 超时时间（秒），默认 300 秒

    Returns:
        True 表示批准，False 表示拒绝或超时
    """
    event = _approval_events.get(request_id)
    if not event:
        logger.warning(f"审批事件不存在: {request_id}")
        return False

    if not event.wait(timeout=timeout):
        logger.warning(f"审批请求超时: {request_id}")
        with _pending_approvals_lock:
            if request_id in _pending_approvals:
                _pending_approvals[request_id]["status"] = "rejected"
        return False

    with _pending_approvals_lock:
        result = _pending_approvals.get(request_id, {}).get("status") == "approved"
    return result


def approve_request(request_id: str, approved: bool) -> bool:
    """处理审批决策

    Args:
        request_id: 审批请求 ID
        approved: 是否批准

    Returns:
        True 表示请求存在且已处理，False 表示请求不存在
    """
    with _pending_approvals_lock:
        if request_id not in _pending_approvals:
            return False

        _pending_approvals[request_id]["status"] = "approved" if approved else "rejected"

        event = _approval_events.get(request_id)
        if event:
            event.set()

    logger.info(f"审批请求已处理: {request_id}, 结果: {'批准' if approved else '拒绝'}")
    return True


def get_pending_approval(request_id: str) -> Optional[Dict[str, Any]]:
    """获取待审批请求信息

    Args:
        request_id: 审批请求 ID

    Returns:
        审批请求信息字典，不存在则返回 None
    """
    with _pending_approvals_lock:
        return _pending_approvals.get(request_id)


def get_pending_approvals() -> list[Dict[str, Any]]:
    """获取所有待审批的请求列表"""
    with _pending_approvals_lock:
        return [
            req for req in _pending_approvals.values()
            if req["status"] == "pending"
        ]


def cleanup_approval(request_id: str):
    """清理审批请求数据

    Args:
        request_id: 审批请求 ID
    """
    with _pending_approvals_lock:
        _pending_approvals.pop(request_id, None)
        _approval_events.pop(request_id, None)


# =============================================================================
# 工具包装函数
# =============================================================================

def wrap_tool_with_approval(tool):
    """包装工具函数，在调用前检查是否需要人工审批

    将原始 BaseTool 包装为带有审批逻辑的新工具。
    如果需要审批，工具会阻塞等待用户决策，审批通过后继续执行。

    Args:
        tool: 原始 BaseTool 实例

    Returns:
        BaseTool: 包装后的工具实例
    """
    from langchain_core.tools import StructuredTool

    tool_name = tool.name if hasattr(tool, 'name') else tool.__name__

    def _run_with_approval(**kwargs):
        # 检查是否需要审批
        approval_info = HumanApprovalMiddleware.check_tool(tool_name, kwargs)
        if approval_info:
            # 创建审批请求
            request_data = create_approval_request(tool_name, kwargs)
            if request_data:
                request_id = request_data["request_id"]
                logger.info(f"工具 {tool_name} 需要审批，等待用户决策...")

                # 等待审批结果（阻塞当前线程）
                is_approved = wait_for_approval(request_id)

                # 清理审批状态
                cleanup_approval(request_id)

                if not is_approved:
                    return (
                        f"## 用户已拒绝 — 立即停止，禁止重试\n\n"
                        f"**用户明确拒绝了以下操作，请不要再尝试任何替代方案，也不要继续执行。**\n\n"
                        f"- 工具: {tool_name}\n"
                        f"- 拒绝原因: {approval_info['reason']}\n\n"
                        f"---\n"
                        f"请直接告诉用户：「好的，我已理解您拒绝执行此操作，将不会继续执行。」\n"
                        f"---\n"
                        f"【系统指令】这是用户的最终决定，严禁尝试其他路径、参数或工具来绕过此拒绝。"
                        f"请直接结束当前操作并向用户确认。"
                    )

                logger.info(f"审批通过，继续执行工具: {tool_name}")

        # 执行原始工具（使用 invoke 而非 _run，内部会正确传递 config）
        return tool.invoke(kwargs)

    # 创建新的 BaseTool 实例，保留原始工具的所有元信息
    return StructuredTool.from_function(
        name=tool_name,
        description=tool.description if hasattr(tool, 'description') else "",
        func=_run_with_approval,
        args_schema=tool.args_schema if hasattr(tool, 'args_schema') else None,
    )


# =============================================================================
# 总结通知中间件
# =============================================================================

# 线程安全的总结通知存储：thread_id -> notice_data
_summary_notices: Dict[str, Dict[str, Any]] = {}
_summary_notices_lock = threading.Lock()


def get_summary_notice(thread_id: str) -> Optional[Dict[str, Any]]:
    """获取并清除指定会话的总结通知

    Args:
        thread_id: 会话 ID

    Returns:
        总结通知数据字典，如果不存在则返回 None
    """
    with _summary_notices_lock:
        return _summary_notices.pop(thread_id, None)


def _get_msg_dedup_key(msg) -> tuple:
    """生成消息去重键

    用于全量历史合并时判断消息是否已存在。
    注意：SystemMessage 总结通知的 content 为空，需要额外用 summary_data.content 区分。

    Args:
        msg: LangChain 消息对象

    Returns:
        tuple: (type_name, content, [summary_content])
    """
    msg_type = type(msg).__name__
    content = getattr(msg, 'content', '')
    additional_kwargs = getattr(msg, 'additional_kwargs', {}) or {}

    if msg_type == 'SystemMessage' and additional_kwargs.get('is_summary_notice'):
        summary_data = additional_kwargs.get('summary_data', {}) or {}
        summary_content = summary_data.get('content', '')
        return (msg_type, content, summary_content)

    return (msg_type, content)


def _save_full_history(thread_id: str, messages: list, preserved_count: int = 0):
    """将全量历史消息持久化到文件，与已有的全量历史进行合并

    在总结触发时保存压缩前的完整消息列表，确保刷新页面后
    仍能看到被压缩的历史对话内容。

    合并逻辑（支持多次压缩）：
    - 首次压缩：保存当前所有消息
    - 后续压缩：从当前消息中跳过保留消息（preserved_count 条），
      将新增消息追加到已有历史末尾

    Args:
        thread_id: 会话 ID
        messages: 完整的 LangChain 消息列表（来自 state["messages"]）
        preserved_count: 压缩后保留的消息数，用于定位新增消息
    """
    try:
        import json
        from langchain_core.messages import messages_to_dict, HumanMessage, RemoveMessage
        from agent_core.config.settings import FULL_HISTORY_DIR

        # 从当前消息中过滤掉总结相关的特殊消息和 RemoveMessage
        # 注意：保留 SystemMessage 总结通知（is_summary_notice），
        # 确保多次压缩后所有总结通知卡片都能在恢复时显示
        current_valid = []
        for msg in messages:
            if isinstance(msg, RemoveMessage):
                continue
            if isinstance(msg, HumanMessage) and msg.additional_kwargs.get("lc_source") == "summarization":
                continue
            current_valid.append(msg)

        # 加载已有的全量历史
        existing = _load_full_history(thread_id)

        if existing:
            # 已有历史存在，用消息特征去重找出新增消息
            # 避免用 preserved_count 定位（总结通知会偏移位置）
            # 注意：SystemMessage 总结通知的 content 为空，需要用 summary_data.content 区分
            existing_set = set()
            for msg in existing:
                key = _get_msg_dedup_key(msg)
                existing_set.add(key)

            truly_new = []
            for msg in current_valid:
                key = _get_msg_dedup_key(msg)
                if key not in existing_set:
                    truly_new.append(msg)

            merged = existing + truly_new
            if truly_new:
                logger.info(
                    f"全量历史合并: thread_id={thread_id}, "
                    f"已有 {len(existing)} 条, 新增 {len(truly_new)} 条"
                )
            else:
                logger.info(
                    f"全量历史无新增: thread_id={thread_id}, "
                    f"已有 {len(existing)} 条, 当前有效 {len(current_valid)} 条"
                )
        else:
            # 首次保存，保存当前所有有效消息
            merged = current_valid
            logger.info(f"全量历史首次保存: thread_id={thread_id}, 共 {len(merged)} 条")

        full_history_dir = FULL_HISTORY_DIR
        os.makedirs(full_history_dir, exist_ok=True)
        filepath = os.path.join(full_history_dir, f"{thread_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(messages_to_dict(merged), f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning(f"保存全量历史消息失败: thread_id={thread_id}, error={e}")


def _load_full_history(thread_id: str) -> Optional[list]:
    """从文件中加载全量历史消息

    Args:
        thread_id: 会话 ID

    Returns:
        完整的 LangChain 消息列表，如果文件不存在则返回 None
    """
    try:
        import json
        from langchain_core.messages import messages_from_dict
        from agent_core.config.settings import FULL_HISTORY_DIR

        filepath = os.path.join(FULL_HISTORY_DIR, f"{thread_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return messages_from_dict(data)
    except Exception as e:
        logger.warning(f"加载全量历史消息失败: thread_id={thread_id}, error={e}")
        return None


def _delete_full_history(thread_id: str):
    """删除全量历史消息文件

    在清空会话时调用，避免残留文件。

    Args:
        thread_id: 会话 ID
    """
    try:
        from agent_core.config.settings import FULL_HISTORY_DIR
        filepath = os.path.join(FULL_HISTORY_DIR, f"{thread_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.warning(f"删除全量历史消息文件失败: thread_id={thread_id}, error={e}")


class SummaryAwareMiddleware(AgentMiddleware):
    """总结通知中间件包装器

    继承自 AgentMiddleware，在 SummarizationMiddleware 触发总结后，
    在消息列表中插入总结通知节点，并记录总结信息供 executor 发射
    summary_notice 事件。

    总结通知节点以 SystemMessage 形式存入 Checkpoint，包含 is_summary_notice
    标记和 summary_data 数据，前端据此渲染为可视化卡片。
    """

    def __init__(self, base_middleware: SummarizationMiddleware):
        super().__init__()
        self.base_middleware = base_middleware

    def before_model(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """在模型调用前检查是否需要总结

        先委托 base_middleware 执行总结逻辑，如果触发了总结，则在结果中
        插入总结通知节点，并记录总结信息供后续使用。
        """
        # 记录总结前的消息总数，用于计算被总结的消息数
        total_count = len(state.get("messages", []))
        # 保存全量消息快照（压缩前的完整消息列表），用于后续持久化全量历史
        full_messages = list(state.get("messages", []))

        # 从 runtime.execution_info 获取 thread_id
        # AgentState 不包含 config 字段，只能通过 runtime 获取
        thread_id = "default"
        try:
            if runtime.execution_info and runtime.execution_info.thread_id:
                thread_id = runtime.execution_info.thread_id
        except Exception:
            pass

        result = self.base_middleware.before_model(state, runtime)
        if result and "messages" in result:
            self._inject_summary_notice(result, total_count, thread_id, full_messages)
        return result

    async def abefore_model(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """异步版本：在模型调用前检查是否需要总结"""
        total_count = len(state.get("messages", []))
        full_messages = list(state.get("messages", []))

        thread_id = "default"
        try:
            if runtime.execution_info and runtime.execution_info.thread_id:
                thread_id = runtime.execution_info.thread_id
        except Exception:
            pass

        result = await self.base_middleware.abefore_model(state, runtime)
        if result and "messages" in result:
            self._inject_summary_notice(result, total_count, thread_id, full_messages)
        return result

    def _inject_summary_notice(self, result: dict, total_count: int, thread_id: str, full_messages: list = None):
        """在总结结果中插入通知节点

        在 RemoveMessage + 总结 HumanMessage 之后、保留消息之前插入
        SystemMessage 通知节点。同时将全量历史消息持久化到文件，
        确保压缩前的对话不会丢失。
        """
        messages = result["messages"]

        # 验证结构：messages[0] = RemoveMessage, messages[1] = summary HumanMessage
        if len(messages) < 2:
            return

        summary_msg = messages[1]
        from langchain_core.messages import HumanMessage

        if not isinstance(summary_msg, HumanMessage):
            return
        if summary_msg.additional_kwargs.get("lc_source") != "summarization":
            return

        summary_content = summary_msg.content
        preserved_count = len(messages) - 2  # RemoveMessage + summary HumanMessage
        summarized_count = max(0, total_count - preserved_count)

        triggered_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"

        # 创建总结通知 SystemMessage
        notice = SystemMessage(
            content="",
            additional_kwargs={
                "is_summary_notice": True,
                "summary_data": {
                    "summarized_count": summarized_count,
                    "preserved_count": preserved_count,
                    "triggered_at": triggered_at,
                    "content": summary_content,
                },
            },
        )

        # 插入：RemoveMessage + summary HumanMessage + notice + preserved messages
        # 这样通知节点位于被总结消息和保留消息之间
        result["messages"] = [messages[0], messages[1], notice, *messages[2:]]

        # 记录总结信息，供 executor 发射 summary_notice 事件
        with _summary_notices_lock:
            _summary_notices[thread_id] = {
                "summarized_count": summarized_count,
                "preserved_count": preserved_count,
                "triggered_at": triggered_at,
                "summary_content": summary_content,
            }

        # 持久化全量历史消息：将压缩前的完整消息列表保存到文件，
        # 并传入 preserved_count 用于与已有历史合并（支持多次压缩）
        if full_messages:
            _save_full_history(thread_id, full_messages, preserved_count)

        logger.info(
            f"总结通知已插入: thread_id={thread_id}, "
            f"summarized={summarized_count}, preserved={preserved_count}"
        )


# =============================================================================
# 原有中间件配置
# =============================================================================

def get_middlewares():
    """创建并返回中间件列表

    Returns:
        list: 中间件实例列表
    """
    # 获取总结模型
    summarizer_model = get_summarizer_model()

    # 创建 SummarizationMiddleware 实例
    base_middleware = SummarizationMiddleware(
        model=summarizer_model,
        trigger=("messages", CONTEXT_SUMMARY_MESSAGE_TRIGGER),  # 当消息数达到阈值时触发总结
        keep=("messages", CONTEXT_SUMMARY_KEEP_MESSAGES),       # 保留最近 N 条消息
    )

    # 使用 SummaryAwareMiddleware 包装，在总结时插入通知节点
    wrapped_middleware = SummaryAwareMiddleware(base_middleware)

    logger.info(f"SummarizationMiddleware 已配置（带总结通知），触发阈值: 30 条消息，保留最近 10 条消息")

    return [wrapped_middleware]