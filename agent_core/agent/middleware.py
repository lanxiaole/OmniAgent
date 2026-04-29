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
    
    # 创建 SummarizationMiddleware 实例
    summarization_middleware = SummarizationMiddleware(
        model=summarizer_model,
        trigger=("messages", 100),  # 当消息数达到10条时触发总结
        keep=("messages", 10),      # 保留最近5条消息
    )
    
    logger.info(f"SummarizationMiddleware 已配置，触发阈值: 10 条消息，保留最近 5 条消息")
    
    return [summarization_middleware]
