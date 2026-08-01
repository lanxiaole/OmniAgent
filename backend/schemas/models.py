from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ModelConfig(BaseModel):
    """模型配置"""
    id: str                     # 唯一标识，如 "my_deepseek"
    name: str                   # 显示名称，如 "我的DeepSeek"
    provider: str               # deepseek / qwen / openai / custom
    base_url: str               # API 地址
    api_key: str                # API Key
    model: str                  # 模型名称
    is_default: bool = False    # 是否为默认模型

class ModelConfigResponse(BaseModel):
    """模型配置响应（用于列表返回，隐藏 api_key 的部分内容）"""
    id: str
    name: str
    provider: str
    base_url: str
    api_key_masked: str         # 显示前4位 + **** + 后4位
    model: str
    is_default: bool

class ModelAddRequest(BaseModel):
    """添加模型请求"""
    name: str
    provider: str
    base_url: str
    api_key: str
    model: str

class ModelUpdateRequest(BaseModel):
    """更新模型请求"""
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

class ModelListResponse(BaseModel):
    models: List[ModelConfigResponse]
    current_id: Optional[str] = None

class ModelTestRequest(BaseModel):
    """测试连接请求"""
    base_url: str
    api_key: str
    model: str