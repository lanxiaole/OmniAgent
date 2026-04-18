from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.agent_service import get_agent_reply


async def chat(request: ChatRequest) -> ChatResponse:
    """处理聊天请求
    
    Args:
        request: 聊天请求对象
    
    Returns:
        ChatResponse: 聊天响应对象
    """
    # 调用 agent_service 获取回复
    reply = await get_agent_reply(request.message, request.thread_id)
    # 返回响应对象
    return ChatResponse(reply=reply)
