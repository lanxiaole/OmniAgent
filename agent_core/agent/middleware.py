# 中间件配置模块
from langchain.agents.middleware import SummarizationMiddleware
from agent_core.config import MODEL_NAME
from agent_core.logger import get_logger

logger = get_logger(__name__)


def get_middlewares():
    """创建并返回中间件列表
    
    Returns:
        list: 中间件实例列表
    """
    # 创建 SummarizationMiddleware 实例
    summarization_middleware = SummarizationMiddleware(
        model=MODEL_NAME,
        trigger=("messages", 10),  # 当消息数达到10条时触发总结
        keep=("messages", 5),      # 保留最近5条消息
    )
    
    logger.info(f"SummarizationMiddleware 已配置，模型: {MODEL_NAME}，触发阈值: 10 条消息，保留最近 5 条消息")
    
    return [summarization_middleware]
