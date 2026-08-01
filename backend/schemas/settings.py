from pydantic import BaseModel
from typing import Optional, List

class ServiceStatus(BaseModel):
    """单个服务状态"""
    name: str           # 服务名称
    key: str            # 唯一标识
    configured: bool    # 是否已配置
    status: str         # "active" / "inactive" / "unknown"

class StatusResponse(BaseModel):
    services: List[ServiceStatus]

class WorkspaceDirInfo(BaseModel):
    """单个目录信息"""
    name: str
    path: str
    size_bytes: int
    size_display: str   # 如 "12.5 MB"

class WorkspaceInfoResponse(BaseModel):
    total_bytes: int
    total_display: str
    dirs: List[WorkspaceDirInfo]

class CleanRequest(BaseModel):
    target: str  # "cache" | "temp" | "logs" | "uploads"

class CleanResponse(BaseModel):
    success: bool
    message: str
    freed_bytes: int
    freed_display: str