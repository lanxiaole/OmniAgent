# 审批 API 路由
# 提供人工审批相关的接口

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent_core.agent.middleware import (
    approve_request,
    get_pending_approval,
    get_pending_approvals,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ApproveRequest(BaseModel):
    """审批请求模型"""
    request_id: str
    approved: bool


class ApprovalStatusResponse(BaseModel):
    """审批状态响应模型"""
    success: bool
    request_id: str
    status: str  # approved | rejected


@router.post("/agent/approve")
async def handle_approval(request: ApproveRequest):
    """处理审批决策

    接收前端的审批结果（批准/拒绝），唤醒对应的等待请求。

    Args:
        request: 审批请求，包含 request_id 和 approved 字段

    Returns:
        dict: 操作结果
    """
    success = approve_request(request.request_id, request.approved)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"审批请求不存在或已过期: {request.request_id}"
        )

    status = "approved" if request.approved else "rejected"
    logger.info(f"审批请求已处理: {request.request_id}, 结果: {status}")

    return {
        "success": True,
        "request_id": request.request_id,
        "status": status,
        "message": f"审批已{'批准' if request.approved else '拒绝'}"
    }


@router.get("/agent/approve/pending/{request_id}")
async def get_pending_approval_status(request_id: str):
    """获取待审批请求的详细信息

    Args:
        request_id: 审批请求 ID

    Returns:
        dict: 审批请求信息
    """
    approval = get_pending_approval(request_id)
    if not approval:
        raise HTTPException(
            status_code=404,
            detail=f"审批请求不存在: {request_id}"
        )

    return {
        "success": True,
        "request_id": approval["request_id"],
        "tool": approval["tool"],
        "args": approval["args"],
        "reason": approval["reason"],
        "status": approval["status"],
    }


@router.get("/agent/approve/pending")
async def list_pending_approvals():
    """获取所有待审批的请求列表"""
    pending = get_pending_approvals()
    return {
        "success": True,
        "pending_approvals": pending,
        "count": len(pending),
    }