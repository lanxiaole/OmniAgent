# 模型工厂模块
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk
from agent_core.config import (
    LLM_API_KEY, LLM_MODEL, LLM_SUMMARIZER_MODEL,
    LLM_BASE_URL, LLM_TEMPERATURE,
)
from agent_core.logger import get_logger

logger = get_logger(__name__)


class ReasoningChatOpenAI(ChatOpenAI):
    """支持 reasoning_content 透传的 ChatOpenAI 子类

    DeepSeek-Reasoner 等推理模型在流式响应中返回 reasoning_content 字段，
    但 LangChain 的默认实现会丢弃该字段。本子类重写 chunk 解析逻辑，
    将 reasoning_content 注入到 AIMessageChunk.additional_kwargs 中，
    使下游（executor.py）能够提取并向前端推送思考过程。
    """

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None = None,
    ) -> Any:
        # 先调用父类方法获取标准的 generation_chunk
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if generation_chunk is None:
            return None

        # 从原始 chunk 中提取 reasoning_content（DeepSeek/Qwen 推理模型字段）
        choices = chunk.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {}) or {}
            reasoning = delta.get("reasoning_content", "")
            if reasoning and isinstance(generation_chunk.message, AIMessageChunk):
                # 注入到 additional_kwargs，executor.py 会读取该字段
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning

        return generation_chunk


def _create_model(temperature: float, model_name: str) -> ChatOpenAI:
    return ReasoningChatOpenAI(
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
