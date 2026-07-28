# 统一异常处理模块
# 提供异常分类、用户友好提示、日志记录等功能

import asyncio
import traceback
from typing import Optional


def classify_exception(e: Exception) -> str:
    """将异常分类为用户可理解的错误类型，并返回友好提示。

    分类优先级：
    1. OpenAI SDK 异常（AuthenticationError、RateLimitError 等）
    2. httpx 底层网络异常（ConnectError、TimeoutException 等）
    3. asyncio 取消异常（用户主动中止）
    4. 其他未知异常

    Args:
        e: 捕获到的异常实例

    Returns:
        str: 用户友好的错误提示信息
    """
    # 1. OpenAI SDK 异常（需延迟导入以避免循环依赖）
    try:
        from openai import (
            AuthenticationError,
            PermissionDeniedError,
            RateLimitError,
            NotFoundError,
            BadRequestError,
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            ConflictError,
            UnprocessableEntityError,
        )

        if isinstance(e, AuthenticationError):
            return "API Key 无效或已过期，请在 .env 文件中检查 LLM_API_KEY 配置。"

        if isinstance(e, PermissionDeniedError):
            return "当前 API Key 没有访问该模型的权限，请检查账户权限或更换 Key。"

        if isinstance(e, RateLimitError):
            return "请求过于频繁，已触发速率限制（429）。请稍后再试，或联系服务商提升配额。"

        if isinstance(e, NotFoundError):
            return f"模型不存在（404），请检查 LLM_MODEL 名称是否正确，以及服务商是否支持该模型。"

        if isinstance(e, BadRequestError):
            # 提取 API 返回的详细错误信息
            body = getattr(e, 'body', None)
            if isinstance(body, dict) and body.get('error', {}).get('message'):
                detail = body['error']['message']
                return f"请求参数错误：{detail}"
            return "请求参数错误（400），请检查输入内容是否合规。"

        if isinstance(e, APIConnectionError):
            return "无法连接到 AI 服务，请检查网络连接和 LLM_BASE_URL 是否正确。"

        if isinstance(e, APITimeoutError):
            return "请求超时，AI 服务响应过慢。请稍后重试，或检查网络状况。"

        if isinstance(e, InternalServerError):
            return "AI 服务端发生错误（5xx），这是服务端问题，请稍后重试。"

        if isinstance(e, ConflictError):
            return "请求冲突（409），可能资源状态已变更，请重试。"

        if isinstance(e, UnprocessableEntityError):
            return "请求无法处理（422），请检查输入内容格式是否正确。"

    except ImportError:
        pass

    # 2. httpx 底层网络异常
    try:
        import httpx

        if isinstance(e, httpx.ConnectTimeout):
            return "连接 AI 服务超时，请检查网络或 LLM_BASE_URL 是否可达。"

        if isinstance(e, httpx.ReadTimeout):
            return "接收 AI 响应超时，请稍后重试。"

        if isinstance(e, httpx.PoolTimeout):
            return "连接池耗尽，请稍后再试。"

        if isinstance(e, httpx.ConnectError):
            return "无法建立到 AI 服务的连接，请检查网络或 LLM_BASE_URL 是否正确。"

        if isinstance(e, httpx.ReadError):
            return "接收 AI 响应时网络中断，请检查网络连接后重试。"

        if isinstance(e, httpx.WriteError):
            return "发送请求时网络中断，请检查网络连接后重试。"

        if isinstance(e, httpx.HTTPStatusError):
            status_code = getattr(e, 'status_code', 0)
            return f"HTTP 请求失败（状态码 {status_code}），请检查 API 配置或稍后重试。"

    except ImportError:
        pass

    # 3. 用户主动取消
    if isinstance(e, asyncio.CancelledError):
        return ""  # 静默处理，不向用户显示错误

    # 4. 通用异常：提取异常消息
    error_msg = str(e)
    if error_msg:
        return f"发生错误：{error_msg[:200]}"

    return "抱歉，发生了未知错误，请稍后重试。"


def log_exception(e: Exception, context: str, logger) -> None:
    """记录异常的详细堆栈到日志，供开发者排查。

    Args:
        e: 捕获到的异常实例
        context: 异常发生的上下文描述（如 "run_agent" 或 "stream_agent"）
        logger: 日志器实例
    """
    tb_text = traceback.format_exc()
    logger.error(
        f"[{context}] 异常类型: {type(e).__name__} | "
        f"异常信息: {str(e)} | "
        f"堆栈:\n{tb_text}"
    )


class DocumentLoadError(Exception):
    """文档加载异常"""
    pass


class AgentCreationError(Exception):
    """Agent 创建异常"""
    pass


class VectorStoreError(Exception):
    """向量库操作异常"""
    pass


__all__ = [
    "classify_exception",
    "log_exception",
    "DocumentLoadError",
    "AgentCreationError",
    "VectorStoreError",
]