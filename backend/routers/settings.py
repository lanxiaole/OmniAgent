# 设置管理路由
# 提供服务状态查询、工作区信息查看和清理功能

import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.schemas.settings import (
    ServiceStatus,
    StatusResponse,
    WorkspaceDirInfo,
    WorkspaceInfoResponse,
    CleanRequest,
    CleanResponse,
)
from agent_core.config.settings import (
    WORKSPACE_DIR,
    VECTOR_STORE_DIR,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


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
        LLM_API_KEY, LLM_MODEL, TAVILY_API_KEY, AMAP_API_KEY,
    )

    # 向量库状态：目录存在且有内容
    vector_store_active = Path(VECTOR_STORE_DIR).exists() and any(Path(VECTOR_STORE_DIR).iterdir())

    services = [
        ServiceStatus(
            name="LLM 模型",
            key="llm",
            configured=bool(LLM_API_KEY and LLM_MODEL),
            status="active" if bool(LLM_API_KEY and LLM_MODEL) else "inactive",
        ),
        ServiceStatus(
            name="Tavily 搜索",
            key="tavily",
            configured=bool(TAVILY_API_KEY),
            status="active" if bool(TAVILY_API_KEY) else "inactive",
        ),
        ServiceStatus(
            name="高德地图",
            key="amap",
            configured=bool(AMAP_API_KEY),
            status="active" if bool(AMAP_API_KEY) else "inactive",
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