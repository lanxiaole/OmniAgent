from fastapi import APIRouter
from backend.schemas.chat import ChatRequest, ChatResponse, HistoryResponse, Message
from backend.services.agent_service import get_agent_reply, get_session_history, clear_session

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


@router.get("/chat/history", response_model=HistoryResponse)
async def get_chat_history(thread_id: str):
    """获取指定会话的历史消息
    
    Args:
        thread_id: 会话 ID，必需参数
        
    Returns:
        HistoryResponse: 包含历史消息列表的响应
    """
    messages = get_session_history(thread_id)
    # 转换为 Message 模型列表
    message_models = [Message(**msg) for msg in messages]
    return HistoryResponse(messages=message_models)


@router.delete("/chat/history")
async def delete_chat_history(thread_id: str):
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID，必需参数
        
    Returns:
        dict: 操作结果，包含状态和消息
    """
    try:
        clear_session(thread_id)
        return {"status": "success", "message": f"会话 {thread_id} 已清空"}
    except Exception as e:
        return {"status": "error", "message": f"清空失败: {str(e)}"}