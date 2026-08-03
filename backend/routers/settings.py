# 设置管理路由
# 提供服务状态查询、工作区信息查看和清理功能

import os
import shutil
import sys
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.schemas.settings import (
    ServiceStatus,
    StatusResponse,
    WorkspaceDirInfo,
    WorkspaceInfoResponse,
    CleanRequest,
    CleanResponse,
    EnvConfigItem,
    EnvConfigResponse,
    EnvConfigUpdate,
)
from agent_core.config.settings import (
    WORKSPACE_DIR,
    VECTOR_STORE_DIR,
    USER_DATA_DIR,
)
from agent_core import __version__
from agent_core.config.settings import read_env, write_env_key
from agent_core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 记录进程启动时间，用于计算运行时间
_process_start_time = time.time()


def get_dir_size(path: Path) -> int:
    """递归计算目录大小"""
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


# ==================== 端点 1：服务状态 ====================

@router.get("/settings/status", response_model=StatusResponse)
async def get_status():
    """获取所有服务的配置状态"""
    from agent_core.config.settings import (
        get_llm_api_key, get_llm_model_name, get_tavily_api_key, get_amap_api_key,
    )

    llm_api_key = get_llm_api_key()
    llm_model = get_llm_model_name()
    tavily_api_key = get_tavily_api_key()
    amap_api_key = get_amap_api_key()

    # 向量库状态：目录存在且有内容
    vector_store_active = Path(VECTOR_STORE_DIR).exists() and any(Path(VECTOR_STORE_DIR).iterdir())

    services = [
        ServiceStatus(
            name="LLM 模型",
            key="llm",
            configured=bool(llm_api_key and llm_model),
            status="active" if bool(llm_api_key and llm_model) else "inactive",
        ),
        ServiceStatus(
            name="Tavily 搜索",
            key="tavily",
            configured=bool(tavily_api_key),
            status="active" if bool(tavily_api_key) else "inactive",
        ),
        ServiceStatus(
            name="高德地图",
            key="amap",
            configured=bool(amap_api_key),
            status="active" if bool(amap_api_key) else "inactive",
        ),
        ServiceStatus(
            name="向量库",
            key="vector_store",
            configured=vector_store_active,
            status="active" if vector_store_active else "inactive",
        ),
    ]
    return StatusResponse(services=services)


# ==================== 端点 2：工作区信息 ====================

@router.get("/settings/workspace/info", response_model=WorkspaceInfoResponse)
async def get_workspace_info():
    """获取 workspace 目录信息"""
    workspace_path = Path(WORKSPACE_DIR)
    if not workspace_path.exists():
        return WorkspaceInfoResponse(
            total_bytes=0,
            total_display="0 B",
            dirs=[],
        )

    subdirs = ["checkpoints", "vector_stores", "logs", "cache", "temp", "knowledge", "uploads"]
    dirs_info = []
    total = 0

    for sub in subdirs:
        sub_path = workspace_path / sub
        if sub_path.exists():
            size = get_dir_size(sub_path)
            total += size
            dirs_info.append(WorkspaceDirInfo(
                name=sub,
                path=str(sub_path),
                size_bytes=size,
                size_display=format_size(size),
            ))

    return WorkspaceInfoResponse(
        total_bytes=total,
        total_display=format_size(total),
        dirs=dirs_info,
    )


# ==================== 端点 3：清理工作区目录 ====================

@router.post("/settings/workspace/clean", response_model=CleanResponse)
async def clean_workspace(request: CleanRequest):
    """清理指定的 workspace 子目录"""
    allowed_targets = ["cache", "temp", "logs", "uploads"]
    if request.target not in allowed_targets:
        raise HTTPException(status_code=400, detail=f"不支持的清理目标: {request.target}")

    target_path = Path(WORKSPACE_DIR) / request.target
    if not target_path.exists():
        return CleanResponse(
            success=True,
            message=f"{request.target} 目录不存在，无需清理",
            freed_bytes=0,
            freed_display="0 B",
        )

    # 计算清理前大小
    before_size = get_dir_size(target_path)

    # 删除目录下所有内容（保留目录本身）
    for item in target_path.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    # 清理后大小
    after_size = get_dir_size(target_path)
    freed = before_size - after_size

    logger.info(f"工作区清理完成: {request.target}，释放 {format_size(freed)}")

    return CleanResponse(
        success=True,
        message=f"{request.target} 目录清理完成",
        freed_bytes=freed,
        freed_display=format_size(freed),
    )


# ==================== 端点 5：env 通用配置读写 ====================

# 可配置的 env 变量定义（不包含 OMNI_MODEL_* 模型配置，由 /api/models 管理）
ENV_CONFIG_DEFINITIONS: list[dict] = [
    # ---- Embedding ----
    {"key": "EMBEDDING_BASE_URL", "label": "Embedding Base URL", "type": "text", "default": "https://dashscope.aliyuncs.com/compatible-mode/v1", "placeholder": "https://dashscope.aliyuncs.com/compatible-mode/v1", "hint": "Embedding 模型的 API 地址"},
    {"key": "EMBEDDING_API_KEY", "label": "Embedding API Key", "type": "password", "placeholder": "sk-...", "hint": "Embedding 模型的 API Key"},
    {"key": "EMBEDDING_MODEL", "label": "Embedding Model", "type": "text", "placeholder": "text-embedding-v3", "hint": "Embedding 模型名称"},
    # ---- Tavily 搜索 ----
    {"key": "TAVILY_API_KEY", "label": "Tavily API Key", "type": "password", "placeholder": "tvly-...", "hint": "从 https://app.tavily.com 获取"},
    {"key": "TAVILY_SEARCH_DEPTH", "label": "搜索深度", "type": "select", "options": ["basic", "advanced"], "hint": "basic=1积分/次, advanced=2积分/次"},
    {"key": "TAVILY_EXTRACT_DEPTH", "label": "提取深度", "type": "select", "options": ["basic", "advanced"], "hint": "basic=1积分/5URL, advanced=2积分/5URL"},
    {"key": "TAVILY_MAX_RESULTS", "label": "最大结果数", "type": "number", "placeholder": "5", "hint": "每次搜索返回的最大结果数（0-20）"},
    # ---- 高德地图 ----
    {"key": "AMAP_API_KEY", "label": "高德地图 API Key", "type": "password", "placeholder": "请输入高德地图 API Key", "hint": "用于天气查询工具，从 https://console.amap.com 获取"},
]


@router.get("/settings/env-config", response_model=EnvConfigResponse)
async def get_env_config():
    """获取所有可配置的 env 变量（不含模型配置）"""
    env_vars = read_env()
    items = []
    for cfg in ENV_CONFIG_DEFINITIONS:
        in_env = cfg["key"] in env_vars
        value = env_vars.get(cfg["key"], "")
        if not value and cfg.get("default"):
            value = cfg["default"]
        items.append(EnvConfigItem(
            key=cfg["key"],
            label=cfg["label"],
            value=value,
            type=cfg.get("type", "text"),
            placeholder=cfg.get("placeholder", ""),
            options=cfg.get("options", []),
            hint=cfg.get("hint", ""),
            saved=in_env,  # 实际存在于 .env 中才算已保存
        ))
    return EnvConfigResponse(items=items)


@router.put("/settings/env-config")
async def update_env_config(request: EnvConfigUpdate):
    """更新单个 env 变量"""
    write_env_key(request.key, request.value)
    logger.info(f"env 配置更新: {request.key}")
    return {"success": True, "message": f"{request.key} 已更新"}


# ==================== 端点 6：关于信息 ====================

def _format_uptime(seconds: float) -> str:
    """将秒数格式化为可读的运行时间"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分")
    parts.append(f"{secs}秒")
    return "".join(parts)


@router.get("/settings/about")
async def get_about():
    """获取应用信息：版本、Python 版本、运行时间"""
    uptime_seconds = time.time() - _process_start_time
    return {
        "version": __version__,
        "python_version": sys.version,
        "uptime_seconds": int(uptime_seconds),
        "uptime_display": _format_uptime(uptime_seconds),
    }


# ==================== 端点 7：配置目录路径 ====================

@router.get("/settings/config-path")
async def get_config_path():
    """返回用户数据目录的绝对路径"""
    return {"path": USER_DATA_DIR}


# ==================== 端点 8：打开配置目录 ====================

@router.post("/settings/open-config-path")
async def open_config_path():
    """在系统文件管理器中打开配置目录"""
    import platform
    import subprocess

    path = USER_DATA_DIR
    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
        logger.info(f"已打开配置目录: {path}")
        return {"success": True, "message": "目录已打开"}
    except Exception as e:
        logger.error(f"打开配置目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"打开目录失败: {str(e)}")