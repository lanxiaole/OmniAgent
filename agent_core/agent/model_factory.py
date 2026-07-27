# 模型工厂模块
from langchain_openai import ChatOpenAI
from agent_core.config import (
    LLM_API_KEY, LLM_MODEL, LLM_SUMMARIZER_MODEL,
    LLM_BASE_URL, LLM_TEMPERATURE,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)


def _create_model(temperature: float, model_name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=temperature,
    )


def get_llm_model() -> ChatOpenAI:
    logger.info(f"主模型已初始化: {LLM_MODEL} @ {LLM_BASE_URL}")
    return _create_model(LLM_TEMPERATURE, LLM_MODEL)


def get_summarizer_model() -> ChatOpenAI:
    logger.info(f"总结模型已初始化: {LLM_SUMMARIZER_MODEL} @ {LLM_BASE_URL}")
    return _create_model(0.3, LLM_SUMMARIZER_MODEL)
