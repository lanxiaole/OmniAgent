# OmniAgent RAG 模块（向量检索）

import os
from langchain_chroma import Chroma
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_core.documents import Document
from config import PERSIST_DIR, KNOWLEDGE_DIR, DASHSCOPE_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL, RAG_TOP_K

# 加载文档函数
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

# 构建向量库函数
def build_vector_store():
    """构建向量库"""
    # 加载文档
    documents = load_documents()
    
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
    
    print(f"向量库构建完成，共 {len(documents)} 条记录")

# 加载向量库函数
def load_vector_store():
    """加载已有向量库
    
    返回:
        Chroma | None: 向量库对象，如果不存在则返回 None
    """
    if os.path.exists(PERSIST_DIR):
        api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
        if not api_key:
            raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
        
        embeddings = DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=api_key
        )
        
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )
    else:
        return None

# 检索函数
def retrieve(query: str, top_k: int = RAG_TOP_K) -> list[str]:
    """检索相关文档
    
    参数:
        query: 查询字符串
        top_k: 返回的文档数量
        
    返回:
        list[str]: 检索到的文档内容列表
    """
    # 加载向量库
    vector_store = load_vector_store()
    
    if not vector_store:
        print("向量库不存在，请先运行 build_vector_store() 构建向量库")
        return []
    
    # 相似度搜索
    results = vector_store.similarity_search(query, k=top_k)
    
    # 返回文档内容列表
    return [result.page_content for result in results]

# 测试代码
if __name__ == "__main__":
    # 构建向量库
    build_vector_store()
    
    # 测试检索
    query = "博客技术"
    results = retrieve(query, top_k=1)
    print(f"检索 '{query}' 的结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")