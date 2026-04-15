# RAG 构建模块

import os
from langchain_chroma import Chroma
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_core.documents import Document
from .config import PERSIST_DIR, KNOWLEDGE_DIR, DASHSCOPE_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


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
    
    logger.info(f"向量库构建完成，共 {len(documents)} 条记录")


# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
