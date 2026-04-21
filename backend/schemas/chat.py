from pydantic import BaseModel

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str  # 用户输入的消息
    thread_id: str = "web_user"  # 会话 ID，默认为 web_user

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str  # 机器人的回复消息