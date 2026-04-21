# 中间件配置模块
from langchain.agents.middleware import SummarizationMiddleware
from agent_core.agent.model_factory import get_summarizer_model
from agent_core.logger import get_logger

logger = get_logger(__name__)


def get_middlewares():
    """创建并返回中间件列表
    
    Returns:
        list: 中间件实例列表
    """
    # 获取总结模型
    summarizer_model = get_summarizer_model()
    
    # 当消息 token 超过 4000 时触发总结，保留最近 20 条消息不总结
    summarization_middleware = SummarizationMiddleware(
        model=summarizer_model,
        trigger=("tokens", 4000),
        keep=("messages", 20),
    )
    
    logger.info("SummarizationMiddleware 已配置，触发阈值: 4000 tokens，保留最近 20 条消息")
    
    return [summarization_middleware]
