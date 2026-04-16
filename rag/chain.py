# RAG Chain 模块

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE
from config.prompt_loader import load_prompt
from .retriever import get_retriever
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 初始化模型
api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
if not api_key:
    raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=api_key,
    temperature=TEMPERATURE
)

# 定义 RAG 提示词
rag_template = load_prompt("rag")
prompt = ChatPromptTemplate.from_template(rag_template)

# 定义文档打印函数
def log_docs(docs):
    print("检索到的文档：")
    for i, doc in enumerate(docs):
        print(f"  {i+1}. {doc.page_content}")
    return docs

# 构建 LCEL RAG Chain
retriever = get_retriever()
rag_chain = (
    {"context": retriever | log_docs | (lambda docs: "\n\n".join(d.page_content for d in docs)),
     "question": RunnablePassthrough()}
    | prompt
    | model
)


def run_rag_chain(question: str) -> str:
    """运行 RAG Chain 回答问题
    
    参数:
        question: 用户问题
        
    返回:
        str: 回答结果
    """
    try:
        logger.debug(f"运行 RAG Chain，问题: {question}")
        result = rag_chain.invoke(question)
        logger.info("RAG Chain 运行成功")
        return result.content
    except Exception as e:
        logger.error(f"RAG Chain 错误: {e}")
        return "抱歉，我暂时无法回答这个问题。"
