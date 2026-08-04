# 中间件配置模块
# 提供消息总结中间件和人工审批中间件

import uuid
import threading
import os
from typing import Any, Dict, Optional
from langchain.agents.middleware import SummarizationMiddleware
from agent_core.agent.model_factory import get_summarizer_model
from agent_core.config.settings import WORKSPACE_DIR
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
    summarization_middleware = SummarizationMiddleware(
        model=summarizer_model,
        trigger=("messages", 30),  # 当消息数达到30条时触发总结
        keep=("messages", 10),      # 保留最近10条消息
    )

    logger.info(f"SummarizationMiddleware 已配置，触发阈值: 30 条消息，保留最近 10 条消息")

    return [summarization_middleware]