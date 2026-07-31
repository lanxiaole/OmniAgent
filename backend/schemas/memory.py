from pydantic import BaseModel
from typing import Optional, List


class MemoryItem(BaseModel):
    """单条记忆"""
    id: str
    content: str
    metadata: dict = {}  # 包含 created_at 等


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    memories: List[MemoryItem]
    total: int


class MemoryAddRequest(BaseModel):
    """添加记忆请求"""
    content: str


class MemoryAddResponse(BaseModel):
    """添加记忆响应"""
    success: bool
    id: Optional[str] = None
    message: str


class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""
    content: str


class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    query: str
    top_k: Optional[int] = 5


class MemorySearchResponse(BaseModel):
    """搜索记忆响应"""
    results: List[MemoryItem]