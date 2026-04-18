from fastapi import APIRouter
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.controllers.chat_controller import chat

# 创建 APIRouter 实例
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天端点
    
    Args:
        request: 聊天请求对象
    
    Returns:
        ChatResponse: 聊天响应对象
    """
    return await chat(request)
