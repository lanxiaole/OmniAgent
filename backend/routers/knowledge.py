# 知识库管理路由模块
# 提供知识库状态查询、文件管理、向量库重建和检索测试等 API

import os
import threading
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette.concurrency import run_in_threadpool

from agent_core.rag.builder import build_vector_store, need_rebuild
from agent_core.rag.loaders import get_loader
from agent_core.rag.retriever import load_vector_store, reset_vector_store_cache
from agent_core.rag.config import VECTOR_STORE_DIR, KNOWLEDGE_DIR
from agent_core.logger import get_logger

from backend.schemas.knowledge import (
    KnowledgeStatusResponse,
    KnowledgeFileItem,
    KnowledgeFileListResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
    KnowledgeRebuildResponse,
    KnowledgeFileContentResponse,
    KnowledgeFileUpdateRequest,
    KnowledgeFileCreateRequest,
    BuildStatusResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# 支持的文件扩展名（与 agent_core/rag/loaders.py 中的 LOADER_REGISTRY 保持一致）
_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

# 可在线编辑（文本类）的文件扩展名
_EDITABLE_EXTENSIONS = {".txt", ".md"}

# 文件上传大小限制（100MB）
_MAX_FILE_SIZE = 100 * 1024 * 1024


# ==================== 后台索引构建任务 ====================
# 知识库构建（解析 + 向量化）可能耗时较长，尤其在文件较大时。
# 采用后台线程串行执行，前端通过 GET /build/status 轮询进度。

_build_state = {
    "building": False,
    "stage": "",          # preparing | parsing | embedding | done | error
    "current": 0,
    "total": 0,
    "message": "",
    "error": None,
}
_build_state_lock = threading.Lock()
_build_pending = threading.Event()
_pending_requested = False
_worker_started = False


def _request_build():
    """请求执行一次后台构建（重复触发会串行排队）"""
    global _pending_requested, _worker_started

    with _build_state_lock:
        _pending_requested = True

    _build_pending.set()

    if not _worker_started:
        _worker_started = True
        threading.Thread(target=_build_worker, name="knowledge-build", daemon=True).start()


def request_background_build():
    """供应用启动或外部模块触发的非阻塞后台重建入口。

    与 _request_build 等价，但作为公开 API 暴露，避免启动逻辑阻塞等待构建完成。
    """
    _request_build()


def _progress_cb(stage: str, current: int, total: int):
    """构建进度回调，更新全局状态"""
    with _build_state_lock:
        _build_state["stage"] = stage
        _build_state["current"] = current
        _build_state["total"] = total


def _build_worker():
    """后台构建工作线程：持续监听构建请求，串行执行，直至无待处理请求"""
    global _pending_requested

    while True:
        _build_pending.wait()
        _build_pending.clear()

        # 无待处理请求则继续等待
        if not _pending_requested:
            continue

        # 连续执行直到没有新的待处理请求（避免频繁上传时遗漏）
        while True:
            with _build_state_lock:
                _pending_requested = False
                _build_state["building"] = True
                _build_state["stage"] = "preparing"
                _build_state["current"] = 0
                _build_state["total"] = 0
                _build_state["message"] = ""
                _build_state["error"] = None

            try:
                build_vector_store(progress_cb=_progress_cb)
                with _build_state_lock:
                    _build_state["building"] = False
                    _build_state["stage"] = "done"
                    _build_state["message"] = "索引构建完成"
            except Exception as e:
                logger.error(f"后台构建向量库失败: {e}", exc_info=True)
                with _build_state_lock:
                    _build_state["building"] = False
                    _build_state["stage"] = "error"
                    _build_state["error"] = str(e)
                    _build_state["message"] = "索引构建失败"

            with _build_state_lock:
                if not _pending_requested:
                    break


def _get_build_state() -> dict:
    """获取当前构建进度的快照"""
    with _build_state_lock:
        return {
            "building": _build_state["building"],
            "stage": _build_state["stage"],
            "current": _build_state["current"],
            "total": _build_state["total"],
            "message": _build_state["message"],
            "error": _build_state["error"],
        }


def _ensure_knowledge_dir():
    """确保知识库目录存在"""
    Path(KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)


def _get_hash_file_path() -> str:
    """获取哈希文件的绝对路径（与 builder.py 中的 HASH_FILE 指向同一文件）"""
    return os.path.join(VECTOR_STORE_DIR, "content.hash")


def _get_chunk_count() -> int:
    """获取向量库中的 chunk 总数"""
    try:
        vector_store = load_vector_store()
        if vector_store is None:
            return 0
        return vector_store._collection.count()
    except Exception as e:
        logger.warning(f"获取 chunk 数失败: {e}")
        return 0


def _get_indexed_files() -> set[str]:
    """获取已索引的文件名集合（通过 Chroma 元数据中的 source 字段识别）"""
    try:
        vector_store = load_vector_store()
        if vector_store is None:
            return set()
        all_data = vector_store.get(include=["metadatas"])
        sources = set()
        for meta in all_data.get("metadatas", []):
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sources
    except Exception as e:
        logger.warning(f"获取已索引文件列表失败: {e}")
        return set()


# ==================== 端点实现 ====================


@router.get("/status", response_model=KnowledgeStatusResponse)
async def get_status():
    """获取知识库概览状态"""
    _ensure_knowledge_dir()

    # 统计知识目录下支持的文件数
    total_files = 0
    if os.path.exists(KNOWLEDGE_DIR):
        for fname in os.listdir(KNOWLEDGE_DIR):
            fpath = os.path.join(KNOWLEDGE_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            _, ext = os.path.splitext(fname)
            if ext.lower() in _SUPPORTED_EXTENSIONS:
                total_files += 1

    # 获取 chunk 数（重同步操作：首次会加载向量库并初始化 Embedding，放入线程池避免阻塞事件循环）
    total_chunks = await run_in_threadpool(_get_chunk_count)

    # 获取最后构建时间（哈希文件的修改时间）
    hash_file_path = _get_hash_file_path()
    last_build = None
    if os.path.exists(hash_file_path):
        mtime = os.path.getmtime(hash_file_path)
        last_build = datetime.fromtimestamp(mtime).isoformat()

    # 判断哈希是否变化（need_rebuild 返回 True 表示有变化）
    hash_changed = need_rebuild()

    return KnowledgeStatusResponse(
        total_files=total_files,
        total_chunks=total_chunks,
        last_build=last_build,
        hash_changed=hash_changed,
    )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传知识库文件（支持 .txt / .md / .pdf，最大 100MB）"""
    _ensure_knowledge_dir()

    # 校验文件扩展名
    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    if ext.lower() not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 .txt / .md / .pdf",
        )

    # 校验文件大小
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="文件大小超过 100MB 限制",
        )

    # 保存文件（重名则覆盖）
    file_path = os.path.join(KNOWLEDGE_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    logger.info(f"文件上传成功: {filename} ({len(content)} bytes)")

    # 触发后台重建向量库，前端通过 /build/status 查看进度
    _request_build()

    return {
        "success": True,
        "message": "文件已上传，正在后台构建索引",
        "filename": filename,
    }


@router.get("/files", response_model=KnowledgeFileListResponse)
async def list_files():
    """列出知识库中的所有文件及索引状态"""
    _ensure_knowledge_dir()

    # 获取已索引文件集合（重同步操作：会加载向量库，放入线程池避免阻塞事件循环）
    indexed_files = await run_in_threadpool(_get_indexed_files)
    files = []

    if os.path.exists(KNOWLEDGE_DIR):
        for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
            fpath = os.path.join(KNOWLEDGE_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            _, ext = os.path.splitext(fname)
            if ext.lower() not in _SUPPORTED_EXTENSIONS:
                continue

            stat = os.stat(fpath)
            files.append(KnowledgeFileItem(
                name=fname,
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                is_indexed=fname in indexed_files,
            ))

    return KnowledgeFileListResponse(files=files, total=len(files))


@router.delete("/files/{filename}", response_model=KnowledgeRebuildResponse)
async def delete_file(filename: str):
    """删除指定文件并重建向量库"""
    _ensure_knowledge_dir()

    # 防止路径穿越攻击
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(KNOWLEDGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {safe_filename}")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"路径不是文件: {safe_filename}")

    # 删除物理文件
    os.remove(file_path)
    logger.info(f"已删除文件: {safe_filename}")

    # 触发后台重建向量库（后台构建会扫描全部文件，自动反映删除）
    _request_build()
    return KnowledgeRebuildResponse(
        success=True,
        message=f"文件 {safe_filename} 已删除，正在后台重建索引",
    )


@router.get("/files/{filename}/content", response_model=KnowledgeFileContentResponse)
async def get_file_content(filename: str):
    """获取文件原始内容（只读预览）

    - .txt / .md：直接返回 UTF-8 文本内容，可在线编辑
    - .pdf：提取 PDF 文本用于预览，仅读不可编辑
    """
    _ensure_knowledge_dir()

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(KNOWLEDGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {safe_filename}")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"路径不是文件: {safe_filename}")

    _, ext = os.path.splitext(safe_filename)

    # 读取/解析文件为文本（PDF 解析耗时，放入线程池避免阻塞事件循环）
    def _read_content() -> str:
        if ext.lower() == ".pdf":
            docs = get_loader(file_path).load(file_path)
            return "\n\n".join(doc.page_content for doc in docs)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    try:
        content = await run_in_threadpool(_read_content)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不支持，仅支持 UTF-8 文本文件")

    return KnowledgeFileContentResponse(
        name=safe_filename,
        content=content,
        size=os.path.getsize(file_path),
    )


@router.put("/files/{filename}", response_model=KnowledgeRebuildResponse)
async def update_file(filename: str, request: KnowledgeFileUpdateRequest):
    """更新文件内容并重建向量库"""
    _ensure_knowledge_dir()

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(KNOWLEDGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {safe_filename}")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"路径不是文件: {safe_filename}")

    # PDF 为二进制文件，不支持文本在线编辑
    _, ext = os.path.splitext(safe_filename)
    if ext.lower() not in _EDITABLE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"文件格式 {ext} 不支持在线编辑，仅支持 .txt / .md",
        )

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        logger.info(f"文件已更新: {safe_filename} ({len(request.content)} bytes)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入文件失败: {e}")

    # 触发后台重建向量库
    _request_build()
    return KnowledgeRebuildResponse(
        success=True,
        message=f"文件 {safe_filename} 已更新，正在后台重建索引",
    )


@router.post("/files", response_model=KnowledgeRebuildResponse)
async def create_file(request: KnowledgeFileCreateRequest):
    """新建文件并重建向量库"""
    _ensure_knowledge_dir()

    safe_filename = os.path.basename(request.filename)

    # 校验文件扩展名（仅支持可在线编辑的文本格式）
    _, ext = os.path.splitext(safe_filename)
    if ext.lower() not in _EDITABLE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 .txt / .md",
        )

    file_path = os.path.join(KNOWLEDGE_DIR, safe_filename)

    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"文件已存在: {safe_filename}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        logger.info(f"文件已创建: {safe_filename} ({len(request.content)} bytes)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建文件失败: {e}")

    # 触发后台重建向量库
    _request_build()
    return KnowledgeRebuildResponse(
        success=True,
        message=f"文件 {safe_filename} 已创建，正在后台重建索引",
    )


@router.post("/rebuild", response_model=KnowledgeRebuildResponse)
async def rebuild():
    """强制重建向量库（后台执行，前端轮询 /build/status 查看进度）"""
    _ensure_knowledge_dir()

    # 删除哈希文件，强制触发 rebuild
    hash_file_path = _get_hash_file_path()
    if os.path.exists(hash_file_path):
        os.remove(hash_file_path)
        logger.info("已删除哈希文件，强制重建向量库")

    _request_build()
    return KnowledgeRebuildResponse(
        success=True,
        message="已开始重建索引，请稍候",
    )


@router.get("/build/status", response_model=BuildStatusResponse)
async def get_build_status():
    """获取后台索引构建进度"""
    state = _get_build_state()
    return BuildStatusResponse(**state)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """检索知识库（沙盒），返回带元数据的匹配结果"""
    from agent_core.rag.retriever import retrieve_docs_with_metadata
    # 检索含 Embedding 网络调用与向量搜索，放入线程池避免阻塞事件循环
    results = await run_in_threadpool(retrieve_docs_with_metadata, request.query, request.top_k)
    return KnowledgeSearchResponse(results=results)