# 用户记忆管理路由模块
# 提供用户长期记忆的增删改查和搜索 API

from fastapi import APIRouter, HTTPException

from agent_core.memory.memory_manager import get_user_memory_store
from agent_core.logger import get_logger

from backend.schemas.memory import (
    MemoryItem,
    MemoryListResponse,
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryUpdateRequest,
    MemorySearchRequest,
    MemorySearchResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


def _get_store():
    """获取用户记忆存储单例实例"""
    return get_user_memory_store()


@router.get("/list", response_model=MemoryListResponse)
async def list_memories():
    """获取所有用户记忆"""
    store = _get_store()
    memories = store.list_memories()
    items = [MemoryItem(**m) for m in memories]
    return MemoryListResponse(memories=items, total=len(items))


@router.post("/add", response_model=MemoryAddResponse)
async def add_memory(request: MemoryAddRequest):
    """手动添加一条用户记忆"""
    try:
        store = _get_store()
        memory_id = store.add_memory(request.content)
        return MemoryAddResponse(
            success=True,
            id=memory_id,
            message="记忆添加成功",
        )
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加记忆失败: {e}")


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """搜索记忆（语义相似度检索）"""
    store = _get_store()
    results = store.search_memories(request.query, request.top_k)
    # search_memories 返回的 dict 包含 score 字段，但 MemoryItem 不需要
    items = [MemoryItem(id=r["id"], content=r["content"], metadata=r["metadata"]) for r in results]
    return MemorySearchResponse(results=items)


@router.put("/{memory_id}", response_model=MemoryAddResponse)
async def update_memory(memory_id: str, request: MemoryUpdateRequest):
    """根据 ID 更新记忆内容"""
    store = _get_store()
    new_id = store.update_memory_by_id(memory_id, request.content)
    if new_id is None:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return MemoryAddResponse(
        success=True,
        id=new_id,
        message="记忆更新成功",
    )


@router.delete("/all", response_model=MemoryAddResponse)
async def clear_all_memories():
    """清空所有用户记忆"""
    store = _get_store()
    count = store.clear_all_memories()
    return MemoryAddResponse(
        success=True,
        message=f"已清空所有记忆（共 {count} 条）",
    )


@router.delete("/{memory_id}", response_model=MemoryAddResponse)
async def delete_memory(memory_id: str):
    """根据 ID 删除单条记忆"""
    store = _get_store()
    # 检查记忆是否存在
    existing = store.get_memory_by_id(memory_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="记忆不存在")
    success = store.delete_memory_by_id(memory_id)
    return MemoryAddResponse(
        success=success,
        id=memory_id,
        message="记忆删除成功" if success else "记忆删除失败",
    )