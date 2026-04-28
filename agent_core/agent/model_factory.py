# 模型工厂模块
from langchain_openai import ChatOpenAI
from agent_core.config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, SUMMARIZER_MODEL_NAME, BASE_URL, TEMPERATURE
from agent_core.logger import get_logger

logger = get_logger(__name__)


def _create_model(temperature: float, model_name: str = MODEL_NAME) -> ChatOpenAI:
    api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")
    return ChatOpenAI(
        model=model_name,
        base_url=BASE_URL,
        api_key=api_key,
        temperature=temperature
    )


def get_llm_model():
    logger.info(f"主模型已初始化: {MODEL_NAME}")
    return _create_model(TEMPERATURE)


def get_summarizer_model():
    logger.info(f"总结模型已初始化: {SUMMARIZER_MODEL_NAME}")
    return _create_model(0.3, SUMMARIZER_MODEL_NAME)
