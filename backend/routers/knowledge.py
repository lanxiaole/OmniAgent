# 知识库管理路由模块
# 提供知识库状态查询、文件管理、向量库重建和检索测试等 API

import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File

from agent_core.rag.builder import build_vector_store, need_rebuild
from agent_core.rag.retriever import load_vector_store, reset_vector_store_cache
from agent_core.rag.config import PERSIST_DIR, KNOWLEDGE_DIR
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
)

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# 支持的文件扩展名（与 agent_core/rag/loaders.py 中的 LOADER_REGISTRY 保持一致）
_SUPPORTED_EXTENSIONS = {".txt", ".md"}

# 文件上传大小限制（10MB）
_MAX_FILE_SIZE = 10 * 1024 * 1024


def _ensure_knowledge_dir():
    """确保知识库目录存在"""
    Path(KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)


def _get_hash_file_path() -> str:
    """获取哈希文件的绝对路径（与 builder.py 中的 HASH_FILE 指向同一文件）"""
    return os.path.join(PERSIST_DIR, "content.hash")


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

    # 获取 chunk 数
    total_chunks = _get_chunk_count()

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
    """上传知识库文件（支持 .txt / .md，最大 10MB）"""
    _ensure_knowledge_dir()

    # 校验文件扩展名
    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    if ext.lower() not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 .txt / .md",
        )

    # 校验文件大小
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="文件大小超过 10MB 限制",
        )

    # 保存文件（重名则覆盖）
    file_path = os.path.join(KNOWLEDGE_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    logger.info(f"文件上传成功: {filename} ({len(content)} bytes)")

    # 重建向量库
    try:
        build_vector_store()
    except Exception as e:
        logger.error(f"重建向量库失败: {e}")
        return {
            "success": True,
            "message": "文件已上传，但重建向量库失败",
            "filename": filename,
        }

    return {
        "success": True,
        "message": "上传成功",
        "filename": filename,
    }


@router.get("/files", response_model=KnowledgeFileListResponse)
async def list_files():
    """列出知识库中的所有文件及索引状态"""
    _ensure_knowledge_dir()

    indexed_files = _get_indexed_files()
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

    # 重建向量库（build_vector_store 内部会检测变化并重建）
    try:
        build_vector_store()
        return KnowledgeRebuildResponse(
            success=True,
            message=f"文件 {safe_filename} 已删除并重建向量库",
        )
    except Exception as e:
        logger.error(f"重建向量库失败: {e}")
        return KnowledgeRebuildResponse(
            success=False,
            message=f"文件已删除，但重建向量库失败: {e}",
        )


@router.get("/files/{filename}/content", response_model=KnowledgeFileContentResponse)
async def get_file_content(filename: str):
    """获取文件原始内容（只读预览）"""
    _ensure_knowledge_dir()

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(KNOWLEDGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {safe_filename}")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"路径不是文件: {safe_filename}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不支持，仅支持 UTF-8 文本文件")

    return KnowledgeFileContentResponse(
        name=safe_filename,
        content=content,
        size=os.path.getsize(file_path),
    )


@router.post("/rebuild", response_model=KnowledgeRebuildResponse)
async def rebuild():
    """强制重建向量库"""
    _ensure_knowledge_dir()

    # 获取重建前的 chunk 数
    before_count = _get_chunk_count()

    # 删除哈希文件，强制触发 rebuild
    hash_file_path = _get_hash_file_path()
    if os.path.exists(hash_file_path):
        os.remove(hash_file_path)
        logger.info("已删除哈希文件，强制重建向量库")

    try:
        build_vector_store()
        after_count = _get_chunk_count()
        chunks_added = after_count - before_count
        return KnowledgeRebuildResponse(
            success=True,
            message="向量库重建完成",
            chunks_added=chunks_added,
        )
    except Exception as e:
        logger.error(f"重建向量库失败: {e}")
        return KnowledgeRebuildResponse(
            success=False,
            message=f"重建向量库失败: {e}",
        )


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """检索知识库（沙盒），返回带元数据的匹配结果"""
    from agent_core.rag.retriever import retrieve_docs_with_metadata
    results = retrieve_docs_with_metadata(request.query, request.top_k)
    return KnowledgeSearchResponse(results=results)