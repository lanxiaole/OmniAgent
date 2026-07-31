# RAG 构建模块

import os
import gc
import time
import shutil
import hashlib
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from .config import (
    VECTOR_STORE_DIR, KNOWLEDGE_DIR, EMBEDDING_MODEL, EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL, HASH_FILE
)
from .loaders import get_loader, LOADER_REGISTRY
from .retriever import reset_vector_store_cache, load_vector_store
from agent_core.errors import DocumentLoadError
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


def _get_embeddings():
    """根据 base_url 自动选择 Embedding 客户端

    - 阿里云百炼（dashscope）→ DashScopeEmbeddings（兼容新版模型）
    - 其他（OpenAI 等）→ OpenAIEmbeddings（OpenAI 兼容接口）
    """
    if "dashscope" in EMBEDDING_BASE_URL or "aliyun" in EMBEDDING_BASE_URL:
        logger.info(f"使用 DashScopeEmbeddings: {EMBEDDING_MODEL}")
        return DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=EMBEDDING_API_KEY,
        )
    logger.info(f"使用 OpenAIEmbeddings: {EMBEDDING_MODEL} @ {EMBEDDING_BASE_URL}")
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=EMBEDDING_BASE_URL,
        api_key=EMBEDDING_API_KEY,
    )


def compute_content_hash() -> str:
    """计算所有知识文档的联合 MD5 哈希

    返回:
        str: 十六进制哈希字符串
    """
    md5_hash = hashlib.md5()

    try:
        # 确保知识目录存在
        if not os.path.exists(KNOWLEDGE_DIR):
            logger.warning(f"知识目录 {KNOWLEDGE_DIR} 不存在")
            return ""

        # 遍历知识目录下的所有文件
        for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
            file_path = os.path.join(KNOWLEDGE_DIR, filename)

            # 只处理文件（跳过目录）
            if os.path.isfile(file_path):
                # 获取文件扩展名
                _, ext = os.path.splitext(filename)
                ext = ext.lower()

                # 只处理支持的文件格式
                if ext in LOADER_REGISTRY:
                    try:
                        # 读取文件二进制内容
                        with open(file_path, "rb") as f:
                            while True:
                                chunk = f.read(4096)
                                if not chunk:
                                    break
                                md5_hash.update(chunk)
                    except Exception as e:
                        logger.error(f"读取文件 {filename} 失败: {e}")

        return md5_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算内容哈希失败: {e}")
        return ""


def need_rebuild() -> bool:
    """判断是否需要重建向量库
    
    返回:
        bool: 如果需要重建返回 True，否则返回 False
    """
    # 确保向量库目录存在
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    
    # 如果哈希文件不存在，需要重建
    if not os.path.exists(HASH_FILE):
        logger.info("哈希文件不存在，需要重建向量库")
        return True
    
    # 读取旧哈希
    try:
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            old_hash = f.read().strip()
    except Exception as e:
        logger.error(f"读取哈希文件失败: {e}")
        return True
    
    # 计算当前哈希
    current_hash = compute_content_hash()
    
    # 比较哈希值
    if old_hash != current_hash:
        logger.info("知识库内容已变化，需要重建向量库")
        return True
    else:
        logger.info("知识库已是最新，跳过构建")
        return False


def save_content_hash():
    """保存当前哈希到文件"""
    try:
        # 确保向量库目录存在
        os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
        
        # 计算当前哈希
        current_hash = compute_content_hash()
        
        # 写入哈希文件
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        
        logger.info("哈希文件已更新")
    except Exception as e:
        logger.error(f"保存哈希文件失败: {e}")


def load_documents() -> list[Document]:
    """加载知识目录下的所有文档

    根据文件扩展名自动选择对应的加载器：
    - .txt → TxtLoader（按行分割）
    - .md → MarkdownLoader（按标题分段）

    返回:
        list[Document]: 文档列表
    """
    documents = []

    # 确保知识目录存在
    if not os.path.exists(KNOWLEDGE_DIR):
        logger.warning(f"知识目录 {KNOWLEDGE_DIR} 不存在")
        return documents

    # 遍历知识目录下的所有文件
    for filename in os.listdir(KNOWLEDGE_DIR):
        file_path = os.path.join(KNOWLEDGE_DIR, filename)

        # 只处理文件（跳过目录）
        if not os.path.isfile(file_path):
            continue

        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 只处理支持的文件格式
        if ext not in LOADER_REGISTRY:
            logger.debug(f"跳过不支持的文件格式: {filename}")
            continue

        try:
            # 根据扩展名获取对应的加载器
            loader = get_loader(file_path)

            # 加载文档
            docs = loader.load(file_path)
            documents.extend(docs)

            logger.info(f"加载 {filename} 成功，共 {len(docs)} 条文档")

        except DocumentLoadError as e:
            logger.error(f"加载文档失败: {e}")
        except Exception as e:
            logger.error(f"加载文档时发生未知错误: {filename} - {e}", exc_info=True)

    return documents


def build_vector_store():
    """构建向量库"""
    # 检查是否需要重建
    if not need_rebuild():
        logger.info("知识库已是最新，跳过构建")
        return

    logger.info("开始构建向量库...")

    # 加载文档
    documents = load_documents()
    logger.info(f"加载了 {len(documents)} 条文档")

    if not documents:
        logger.warning("没有加载到任何文档，跳过向量库构建")
        return

    # 优先使用现有 Chroma 实例的 API 清空后重建，完全避免 Windows 文件锁问题
    rebuilt = False
    existing_store = load_vector_store()
    if existing_store is not None:
        try:
            # 通过 Chroma API 清空现有集合中的所有数据（不操作文件系统）
            all_data = existing_store._collection.get()
            old_ids = all_data.get("ids", []) if all_data else []
            if old_ids:
                existing_store._collection.delete(old_ids)
                logger.info(f"已通过 API 清空 {len(old_ids)} 个旧向量块")

            # 添加新文档到同一集合
            existing_store.add_documents(documents)
            logger.info(f"已添加 {len(documents)} 条新文档到向量库")
            rebuilt = True
        except Exception as e:
            logger.warning(f"通过 API 重建失败，回退到目录重建方式: {e}")

    if not rebuilt:
        # 回退方式（首次创建或 API 方式失败）：重置缓存 + 强制垃圾回收 + 删除目录
        reset_vector_store_cache()
        gc.collect()
        if os.path.exists(VECTOR_STORE_DIR):
            for attempt in range(3):
                try:
                    shutil.rmtree(VECTOR_STORE_DIR)
                    break
                except PermissionError:
                    if attempt < 2:
                        logger.warning(f"删除旧向量库失败（第 {attempt + 1} 次），等待后重试...")
                        gc.collect()
                        time.sleep(1)
                        continue
                    logger.error(f"删除旧向量库失败，无法释放文件锁: {VECTOR_STORE_DIR}")
                    raise
        embeddings = _get_embeddings()
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=VECTOR_STORE_DIR
        )

    # 保存当前哈希
    save_content_hash()

    # 重置缓存，确保下次检索时重新加载
    reset_vector_store_cache()

    logger.info(f"向量库构建完成，共 {len(documents)} 条记录")


# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
