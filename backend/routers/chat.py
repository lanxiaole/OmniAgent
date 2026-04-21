from fastapi import APIRouter
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.agent_service import get_agent_reply, clear_session

# 创建 APIRouter 实例
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天端点，处理用户消息并返回 Agent 的回复
    
    Args:
        request: 聊天请求对象，包含用户消息和会话 ID
        
    Returns:
        ChatResponse: 聊天响应对象，包含 Agent 的回复
    """
    reply = await get_agent_reply(request.message, request.thread_id)
    return ChatResponse(reply=reply)


@router.delete("/chat/history")
async def clear_chat_history(thread_id: str = "web_user"):
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID，默认为 "web_user"
        
    Returns:
        dict: 操作结果，包含状态和消息
    """
    try:
        clear_session(thread_id)
        return {"status": "success", "message": f"会话 {thread_id} 已清空"}
    except Exception as e:
        return {"status": "error", "message": f"清空失败: {str(e)}"}