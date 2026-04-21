# 模型工厂模块
from langchain_openai import ChatOpenAI
from agent_core.config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE
from agent_core.logger import get_logger

logger = get_logger(__name__)


def get_llm_model():
    """创建并返回主 LLM 模型实例
    
    Returns:
        ChatOpenAI: 主模型实例
    """
    # 从环境变量读取 API Key
    api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
    
    # 创建模型实例
    model = ChatOpenAI(
        model=MODEL_NAME,
        base_url=BASE_URL,
        api_key=api_key,
        temperature=TEMPERATURE
    )
    
    logger.info(f"主模型已初始化: {MODEL_NAME}")
    return model


def get_summarizer_model():
    """创建并返回总结模型实例
    
    Returns:
        ChatOpenAI: 总结模型实例
    """
    # 从环境变量读取 API Key
    api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
    
    # 创建总结模型实例（使用更低的温度以获得更稳定的总结）
    summarizer_model = ChatOpenAI(
        model=MODEL_NAME,
        base_url=BASE_URL,
        api_key=api_key,
        temperature=0.3,
    )
    
    logger.info(f"总结模型已初始化: {MODEL_NAME}")
    return summarizer_model
