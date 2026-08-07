# RAG 构建模块

import os
import shutil
import hashlib
from langchain_chroma import Chroma
from langchain_core.documents import Document
from agent_core.config.embedding import create_embeddings
from .config import (
    VECTOR_STORE_DIR, KNOWLEDGE_DIR,
    HASH_FILE, next_version_dir, set_active_store_dir
)
from .loaders import get_loader, LOADER_REGISTRY
from .retriever import reset_vector_store_cache, load_vector_store
from agent_core.errors import DocumentLoadError
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


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
    """构建向量库（版本化目录方式，永不删除旧目录，彻底避免文件锁问题）"""
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

    # 获取 Embedding 实例
    embeddings = create_embeddings()

    # 生成新版本目录（如 v1, v2, v3...），在全新目录中构建，不碰旧目录
    version_name, version_dir = next_version_dir()
    logger.info(f"正在新版本目录中构建向量库: {version_name} ({version_dir})")

    try:
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=version_dir,
            collection_name="langchain",
        )
        logger.info(f"向量库构建成功，共 {len(documents)} 条文档")
    except Exception as e:
        logger.error(f"向量库构建失败: {e}")
        raise RuntimeError(f"向量库构建失败: {e}")

    # 切换活跃指针到新版本（原子操作：写入一个小文件）
    set_active_store_dir(version_name)
    logger.info(f"已切换活跃指针到 {version_name}")

    # 保存当前哈希
    save_content_hash()

    # 重置缓存，确保下次检索时重新加载新版本
    reset_vector_store_cache()

    # 清理旧版本目录（只保留当前活跃版本，释放磁盘空间）
    _cleanup_old_versions(version_name)

    logger.info(f"向量库构建完成（版本 {version_name}），共 {len(documents)} 条记录")


def _cleanup_old_versions(current_version: str):
    """删除当前活跃版本之外的所有旧版本目录，释放磁盘空间

    删除失败仅记录警告，不影响主流程（Windows 文件锁可能导致无法删除）。
    """
    if not os.path.isdir(VECTOR_STORE_DIR):
        return
    for entry in os.listdir(VECTOR_STORE_DIR):
        # 只处理 v1, v2, v3... 格式的版本目录
        if not (entry.startswith("v") and entry[1:].isdigit()):
            continue
        if entry == current_version:
            continue
        old_dir = os.path.join(VECTOR_STORE_DIR, entry)
        try:
            shutil.rmtree(old_dir)
            logger.info(f"已清理旧版本目录: {entry}")
        except Exception as e:
            logger.warning(f"清理旧版本目录 {entry} 失败（文件锁等），将保留: {e}")


# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
