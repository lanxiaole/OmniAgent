# 工作区只读浏览路由
# 提供 workspace/ 目录下的文件树浏览和文本文件内容预览功能

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from datetime import datetime
from agent_core.config.settings import WORKSPACE_DIR
from backend.schemas.workspace import WorkspaceNode, WorkspaceTreeResponse, FileContentResponse

router = APIRouter(prefix="/workspace", tags=["workspace"])

# 支持预览的文本文件扩展名
_TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml",
    ".xml", ".html", ".css", ".js", ".ts", ".log", ".toml",
    ".ini", ".cfg", ".conf", ".sh", ".bash"
}


def safe_path(relative_path: str = "") -> Path:
    """校验并返回安全的绝对路径，确保在 workspace 内

    参数:
        relative_path: 相对于 workspace 的路径

    返回:
        Path: 安全的绝对路径

    异常:
        HTTPException: 路径包含 .. 或越界访问
    """
    # 禁止路径穿越（在清理前先检测原始输入）
    if ".." in relative_path.replace("\\", "/").split("/"):
        raise HTTPException(status_code=400, detail="非法路径：禁止使用 ..")

    # 去除开头的 / 或 ./（使用正则或手动去前缀，而非 lstrip 字符集）
    clean = relative_path
    while clean.startswith("/") or clean.startswith("./"):
        if clean.startswith("/"):
            clean = clean[1:]
        if clean.startswith("./"):
            clean = clean[2:]

    abs_path = (Path(WORKSPACE_DIR) / clean).resolve()
    # 确保最终路径在 workspace 内
    if not str(abs_path).startswith(str(Path(WORKSPACE_DIR).resolve())):
        raise HTTPException(status_code=403, detail="禁止访问 workspace 外部的文件")
    return abs_path


@router.get("/tree", response_model=WorkspaceTreeResponse)
async def get_tree(path: str = Query("", description="相对于 workspace 的路径")):
    """获取指定路径下的文件和文件夹列表"""
    abs_path = safe_path(path)

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="路径不存在")
    if not abs_path.is_dir():
        raise HTTPException(status_code=400, detail="路径不是目录")

    nodes = []
    for item in sorted(abs_path.iterdir()):
        # 跳过隐藏文件
        if item.name.startswith("."):
            continue

        node = WorkspaceNode(
            name=item.name,
            path=str(item.relative_to(WORKSPACE_DIR)).replace("\\", "/"),
            type="directory" if item.is_dir() else "file",
        )
        if item.is_file():
            stat = item.stat()
            node.size = stat.st_size
            node.modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        nodes.append(node)

    return WorkspaceTreeResponse(
        nodes=nodes,
        current_path=path or "/"
    )


@router.get("/file", response_model=FileContentResponse)
async def get_file(path: str = Query(..., description="相对于 workspace 的文件路径")):
    """读取文件内容（仅限文本文件，最大 10MB）"""
    abs_path = safe_path(path)

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not abs_path.is_file():
        raise HTTPException(status_code=400, detail="路径不是文件")

    # 文件大小限制（10MB）
    size = abs_path.stat().st_size
    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件过大（超过 10MB）")

    # 格式校验
    ext = abs_path.suffix.lower()
    if ext not in _TEXT_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持预览 {ext} 格式的文件")

    # 读取文件内容
    try:
        content = abs_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不是 UTF-8，无法预览")

    return FileContentResponse(
        content=content,
        path=path,
        size=size,
        encoding="utf-8"
    )