# RAG 构建模块

import os
import hashlib
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from .config import (
    PERSIST_DIR, KNOWLEDGE_DIR, EMBEDDING_MODEL, EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL, HASH_FILE
)
from .loaders import get_loader, LOADER_REGISTRY
from .retriever import reset_vector_store_cache
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
    # 确保 chroma_db 目录存在
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
        # 确保 chroma_db 目录存在
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

    # 初始化 Embeddings（自动根据平台选择客户端）
    embeddings = _get_embeddings()

    # 创建向量库
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )

    # 保存当前哈希
    save_content_hash()

    # 重置 retriever 的向量库缓存，以便下次检索时重新加载
    reset_vector_store_cache()

    logger.info(f"向量库构建完成，共 {len(documents)} 条记录")


# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
