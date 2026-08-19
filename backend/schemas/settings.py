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

class EnvConfigItem(BaseModel):
    """单个环境变量配置项"""
    key: str
    label: str
    value: str
    type: str = "text"      # text / password / select / number
    placeholder: str = ""
    options: list[str] = []
    hint: str = ""
    saved: bool = False     # 是否已写入 .env 文件（未保存的默认值不会持久化）

class EnvConfigResponse(BaseModel):
    """env 通用配置响应"""
    items: list[EnvConfigItem]

class EnvConfigUpdate(BaseModel):
    """更新单个环境变量"""
    key: str
    value: str


# ==================== 场景切换 Schema ====================

class ScenarioPreset(BaseModel):
    """场景预设（前端展示用）"""
    id: str
    name: str
    icon: str
    description: str
    system_prompt: str = ""
    enabled_tools: list[str] = []
    is_system: bool = False      # True 表示内置场景（只读），False 表示用户自定义
    display: bool = True         # 是否在启动页展示


class ScenarioListResponse(BaseModel):
    """场景列表响应"""
    presets: list[ScenarioPreset]


class ScenarioSwitchRequest(BaseModel):
    """场景切换请求"""
    scenario_id: str


class ScenarioCreateRequest(BaseModel):
    """创建自定义场景请求"""
    name: str
    icon: str = "ChatRound"
    description: str = ""
    system_prompt: str = ""
    enabled_tools: list[str] = ["all"]


class ScenarioActionResponse(BaseModel):
    """场景操作统一响应（删除成功后返回）"""
    success: bool
    message: str


class ScenarioDisplayUpdate(BaseModel):
    """更新场景显示状态请求"""
    display: bool


class ScenarioImportRequest(BaseModel):
    """导入场景请求（自定义场景 JSON 数据）"""
    id: str = ""
    name: str = ""
    icon: str = "ChatRound"
    description: str = ""
    system_prompt: str = ""
    enabled_tools: list[str] = ["all"]