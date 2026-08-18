from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str  # 用户输入的消息
    thread_id: str  # 会话 ID，必需参数，无默认值

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str  # 机器人的回复消息

class ToolCallSchema(BaseModel):
    """工具调用模型"""
    id: str
    name: str
    args: Dict[str, Any] = {}
    result: Optional[str] = None
    status: str = "pending"

class SummaryNoticeSchema(BaseModel):
    """总结通知数据结构"""
    summarized_count: int = 0
    preserved_count: int = 0
    triggered_at: str = ""
    content: str = ""

class Message(BaseModel):
    """消息模型"""
    role: str  # 消息角色，"user" 或 "assistant" 或 "system"
    content: str  # 消息内容
    reasoning: Optional[str] = None  # 思考/推理过程（DeepSeek 等模型）
    toolCalls: Optional[List[ToolCallSchema]] = None  # 工具调用列表
    isSummaryNotice: Optional[bool] = None  # 是否为总结通知
    summaryData: Optional[SummaryNoticeSchema] = None  # 总结通知数据

class HistoryResponse(BaseModel):
    """会话历史响应模型"""
    messages: List[Message]  # 历史消息列表