from pydantic import BaseModel
from typing import List, Dict

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str  # 用户输入的消息
    thread_id: str  # 会话 ID，必需参数，无默认值

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str  # 机器人的回复消息

class Message(BaseModel):
    """消息模型"""
    role: str  # 消息角色，"user" 或 "assistant"
    content: str  # 消息内容

class HistoryResponse(BaseModel):
    """会话历史响应模型"""
    messages: List[Message]  # 历史消息列表