# RAG 构建模块

import os
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_core.documents import Document
from .config import PERSIST_DIR, KNOWLEDGE_DIR, DASHSCOPE_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL, HASH_FILE
from logger import get_logger

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
                # 支持 .txt 文件，后续可扩展
                if filename.endswith(".txt"):
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
    
    返回:
        list[Document]: 文档列表，每行作为一个独立的 Document
    """
    documents = []
    
    # 遍历知识目录下的所有 .txt 文件
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".txt"):
            file_path = os.path.join(KNOWLEDGE_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # 每行作为一个独立的 Document
                        doc = Document(
                            page_content=line,
                            metadata={"source": filename}
                        )
                        documents.append(doc)
    
    return documents


def build_vector_store():
    """构建向量库"""
    # 检查是否需要重建
    if not need_rebuild():
        print("知识库已是最新，跳过构建")
        return
    
    logger.info("开始构建向量库...")
    
    # 加载文档
    documents = load_documents()
    logger.info(f"加载了 {len(documents)} 条文档")
    
    # 初始化 Embeddings
    api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
    
    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=api_key
    )
    
    # 创建向量库
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )
    
    # 保存当前哈希
    save_content_hash()
    
    logger.info(f"向量库构建完成，共 {len(documents)} 条记录")


# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
