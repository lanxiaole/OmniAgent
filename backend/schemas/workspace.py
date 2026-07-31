# 工作区浏览 API Schemas

from pydantic import BaseModel
from typing import List, Optional


class WorkspaceNode(BaseModel):
    """文件树节点"""
    name: str
    path: str          # 相对于 workspace 的路径
    type: str          # "file" 或 "directory"
    size: Optional[int] = None        # 文件大小（字节），目录无此字段
    modified_at: Optional[str] = None  # ISO 格式时间


class WorkspaceTreeResponse(BaseModel):
    """目录树响应"""
    nodes: List[WorkspaceNode]
    current_path: str   # 当前请求的路径


class FileContentResponse(BaseModel):
    """文件内容响应"""
    content: str
    path: str
    size: int
    encoding: str = "utf-8"