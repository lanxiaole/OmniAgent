# 长期记忆管理模块
# 实现基于向量检索的用户长期记忆存储和检索功能

import os
from datetime import datetime
from langchain_chroma import Chroma
from agent_core.config.embedding import create_embeddings
from agent_core.config.settings import MEMORY_DIR, MEMORY_TOP_K
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 用户记忆集合名称，与 RAG 知识库隔离
MEMORY_COLLECTION_NAME = "user_memory"

# 模块级缓存：避免每次操作都重新初始化 Chroma 和 Embeddings
_memory_store_instance = None


class UserMemoryStore:
    """用户长期记忆存储类

    使用 Chroma 向量数据库存储用户信息，支持添加记忆和相似度检索。
    使用独立的存储目录与 RAG 知识库完全隔离。
    """

    def __init__(self, persist_directory: str = MEMORY_DIR):
        """初始化用户记忆存储

        参数:
            persist_directory: 记忆向量库持久化目录，默认为 workspace/memory
        """
        self.persist_directory = persist_directory
        self.embeddings = create_embeddings()
        
        # 创建或加载 Chroma 集合（使用独立的 collection_name 隔离）
        self.chroma = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=MEMORY_COLLECTION_NAME
        )
        logger.info(f"用户记忆存储已初始化，集合: {MEMORY_COLLECTION_NAME}")

    def add_memory(self, content: str, metadata: dict = None) -> str:
        """添加一条用户记忆，自动附加创建时间戳

        参数:
            content: 记忆内容字符串，如"用户喜欢吃辣"
            metadata: 可选的附加元数据

        返回:
            str: 新添加记忆的 ID（Chroma 自动生成）
        """
        try:
            _metadata = metadata or {}
            if "created_at" not in _metadata:
                _metadata["created_at"] = datetime.now().isoformat()
            # add_texts 返回添加的 ID 列表
            ids = self.chroma.add_texts([content], metadatas=[_metadata])
            added_id = ids[0] if ids else None
            logger.info(f"用户记忆添加成功（ID: {added_id}）: {content[:50]}..." if len(content) > 50 else f"用户记忆添加成功（ID: {added_id}）: {content}")
            return added_id
        except Exception as e:
            logger.error(f"添加用户记忆失败: {e}")
            raise

    def similarity_search(self, query: str, top_k: int = MEMORY_TOP_K) -> list[str]:
        """根据查询检索相关记忆

        参数:
            query: 查询字符串
            top_k: 返回的记忆数量，默认为 MEMORY_TOP_K

        返回:
            list[str]: 检索到的记忆内容列表，按相似度排序
        """
        try:
            results = self.chroma.similarity_search(query, k=top_k)
            logger.info(f"用户记忆检索成功，查询: {query}, 返回 {len(results)} 条")
            return [result.page_content for result in results]
        except Exception as e:
            logger.error(f"检索用户记忆失败: {e}")
            return []

    def get_memory_count(self) -> int:
        """获取当前存储的记忆数量

        返回:
            int: 记忆总数
        """
        try:
            count = self.chroma._collection.count()
            logger.debug(f"当前用户记忆数量: {count}")
            return count
        except Exception as e:
            logger.error(f"获取记忆数量失败: {e}")
            return 0

    def update_memory(self, new_content: str, query: str = None, similarity_threshold: float = 0.75) -> str:
        """智能更新用户记忆（先检索相似记忆，删除后重新添加）

        用于处理记忆覆盖场景，如用户说"我不喜欢吃辣了"来覆盖"用户喜欢吃辣"。

        参数:
            new_content: 新的记忆内容
            query: 用于查找旧记忆的查询词，默认使用 new_content
            similarity_threshold: 相似度阈值，超过此值才会删除旧记忆

        返回:
            str: 操作结果描述
        """
        if query is None:
            query = new_content

        try:
            # 检索相似记忆
            results = self.chroma.similarity_search_with_score(query, k=3)
            
            if not results:
                # 没有相似记忆，直接添加
                self.chroma.add_texts([new_content])
                logger.info(f"添加新记忆: {new_content}")
                return f"已保存新记忆: {new_content}"

            # 检查是否有足够相似的记忆需要更新
            deleted_count = 0
            for doc, score in results:
                # Chroma 返回的是距离，距离越小越相似（L2距离）
                # 转换为相似度：相似度 = 1 / (1 + 距离)
                # 或者直接用距离阈值，距离小于某个值就算相似
                # 这里用距离阈值，距离 < 0.5 表示高度相似
                if score < similarity_threshold:
                    # 删除这条旧记忆
                    old_id = self._get_memory_id(doc.page_content)
                    if old_id:
                        self.chroma._collection.delete(ids=[old_id])
                        deleted_count += 1
                        logger.info(f"删除旧记忆: {doc.page_content}")

            # 添加新记忆
            self.chroma.add_texts([new_content])
            logger.info(f"用户记忆更新成功: {new_content}")
            
            if deleted_count > 0:
                return f"已更新记忆（覆盖了 {deleted_count} 条旧记忆）: {new_content}"
            else:
                return f"已保存新记忆: {new_content}"

        except Exception as e:
            logger.error(f"更新用户记忆失败: {e}")
            raise

    def _get_memory_id(self, content: str) -> str | None:
        """根据内容获取记忆的 ID

        参数:
            content: 记忆内容

        返回:
            str | None: 记忆 ID，未找到返回 None
        """
        try:
            # 获取所有记忆，ids 是默认返回的
            result = self.chroma._collection.get(include=["documents"])
            documents = result.get("documents", [])
            ids = result.get("ids", [])
            for i, doc in enumerate(documents):
                if doc == content:
                    return ids[i]
            return None
        except Exception as e:
            logger.error(f"获取记忆 ID 失败: {e}")
            return None

    def list_memories(self) -> list[dict]:
        """列出所有用户记忆，包含 ID、内容和元数据

        返回:
            list[dict]: [
                {
                    "id": "uuid",
                    "content": "记忆内容",
                    "metadata": {"created_at": "2026-01-01T12:00:00", ...}
                }
            ]
        """
        try:
            result = self.chroma._collection.get(include=["documents", "metadatas"])
            ids = result.get("ids", [])
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])
            memories = [
                {
                    "id": ids[i],
                    "content": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {}
                }
                for i in range(len(ids))
            ]
            logger.info(f"列出所有记忆，共 {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            return []

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        """根据 ID 获取单条记忆

        返回:
            dict: {"id": "...", "content": "...", "metadata": {...}} 或 None
        """
        try:
            result = self.chroma._collection.get(ids=[memory_id], include=["documents", "metadatas"])
            if not result or not result.get("ids"):
                return None
            return {
                "id": result["ids"][0],
                "content": result["documents"][0],
                "metadata": result["metadatas"][0] if result.get("metadatas") else {}
            }
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None

    def update_memory_by_id(self, memory_id: str, new_content: str) -> str | None:
        """根据 ID 更新记忆内容（覆盖式更新，保留原 created_at）

        Chroma 不支持原地更新，采用删除旧记录 + 添加新记录的方式。
        新记录会由 Chroma 自动生成新 ID。

        参数:
            memory_id: 要更新的记忆 ID
            new_content: 新的记忆内容

        返回:
            str | None: 新记忆的 ID（更新成功）或 None（更新失败/ID 不存在）
        """
        # 1. 获取原记忆的元数据
        old = self.get_memory_by_id(memory_id)
        if not old:
            return None

        try:
            # 2. 删除旧记录
            self.chroma._collection.delete(ids=[memory_id])

            # 3. 添加新记录，保留原 created_at
            metadata = old.get("metadata", {})
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.now().isoformat()
            ids = self.chroma.add_texts([new_content], metadatas=[metadata])
            new_id = ids[0] if ids else None
            logger.info(f"记忆更新成功（旧ID: {memory_id} -> 新ID: {new_id}）")
            return new_id
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return None

    def search_memories(self, query: str, top_k: int = MEMORY_TOP_K) -> list[dict]:
        """搜索记忆，返回完整对象（含 id、content、metadata）

        使用 Chroma 的 similarity_search_with_score 检索语义相似记忆，
        然后通过 content 匹配补齐 ID 和元数据。

        参数:
            query: 搜索查询字符串
            top_k: 返回的记忆数量，默认为 MEMORY_TOP_K

        返回:
            list[dict]: [
                {
                    "id": "uuid",
                    "content": "记忆内容",
                    "metadata": {"created_at": "2026-01-01T12:00:00", ...},
                    "score": float  # 距离分数，越小越相似
                }
            ]
        """
        try:
            # 1. 用语义搜索获取结果
            results = self.chroma.similarity_search_with_score(query, k=top_k)
            if not results:
                return []

            # 2. 获取所有记忆的完整列表用于匹配 content -> id/metadata
            all_memories = self.list_memories()
            content_map = {m["content"]: m for m in all_memories}

            # 3. 组装返回结果
            output = []
            for doc, score in results:
                matched = content_map.get(doc.page_content)
                if matched:
                    output.append({
                        "id": matched["id"],
                        "content": matched["content"],
                        "metadata": matched["metadata"],
                        "score": score,
                    })
            logger.info(f"搜索记忆成功，查询: {query}, 返回 {len(output)} 条")
            return output
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []

    def delete_memory_by_id(self, memory_id: str) -> bool:
        """根据 ID 删除单条记忆

        返回:
            bool: 是否删除成功
        """
        try:
            self.chroma._collection.delete(ids=[memory_id])
            logger.info(f"记忆删除成功（ID: {memory_id}）")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    def delete_memory_by_query(self, query: str, similarity_threshold: float = 0.75) -> int:
        """根据查询删除相似的记忆

        参数:
            query: 查询词
            similarity_threshold: 相似度阈值

        返回:
            int: 删除的记忆数量
        """
        try:
            results = self.chroma.similarity_search_with_score(query, k=5)
            deleted_count = 0
            
            for doc, score in results:
                if score < similarity_threshold:
                    old_id = self._get_memory_id(doc.page_content)
                    if old_id:
                        self.chroma._collection.delete(ids=[old_id])
                        deleted_count += 1
                        logger.info(f"删除记忆: {doc.page_content}")

            logger.info(f"删除了 {deleted_count} 条记忆")
            return deleted_count

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return 0

    def clear_all_memories(self) -> int:
        """清空所有用户记忆

        返回:
            int: 删除的记忆数量
        """
        try:
            # 获取所有记忆的 ids（ids 是默认返回的）
            result = self.chroma._collection.get()
            ids = result.get("ids", [])
            if ids:
                self.chroma._collection.delete(ids=ids)
                logger.info(f"清空所有记忆，共 {len(ids)} 条")
                return len(ids)
            return 0
        except Exception as e:
            logger.error(f"清空记忆失败: {e}")
            return 0


def get_user_memory_store() -> UserMemoryStore:
    """获取用户记忆存储实例（单例模式）

    返回:
        UserMemoryStore: 全局唯一的用户记忆存储实例
    """
    global _memory_store_instance
    if _memory_store_instance is None:
        try:
            _memory_store_instance = UserMemoryStore()
        except Exception as e:
            logger.error(f"初始化用户记忆存储失败: {e}")
            raise RuntimeError(f"初始化用户记忆存储失败: {e}")
    return _memory_store_instance


def reset_memory_store_cache():
    """重置记忆存储缓存

    在需要重新初始化时调用（如配置变更后）
    """
    global _memory_store_instance
    _memory_store_instance = None
    logger.info("用户记忆存储缓存已重置")