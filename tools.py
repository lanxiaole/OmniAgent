# OmniAgent 工具模块

import datetime
from config import TIME_TOOL_KEYWORDS
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


# 获取当前时间的函数
def get_current_time() -> str:
    """获取当前时间
    
    返回:
        str: 当前时间的格式化字符串，格式为 "%Y-%m-%d %H:%M:%S"
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 工具字典，键为触发关键词元组，值为对应的工具函数
TOOLS = {
    tuple(TIME_TOOL_KEYWORDS): get_current_time
}


# 尝试使用工具的函数
def maybe_use_tool(user_input: str) -> str | None:
    """尝试使用工具
    
    参数:
        user_input: 用户输入
        
    返回:
        str | None: 如果匹配到工具，返回工具执行结果；否则返回 None
    """
    for keywords, tool_func in TOOLS.items():
        for keyword in keywords:
            if keyword in user_input:
                # 记录工具触发
                matched_keywords = [k for k in keywords if k in user_input]
                logger.info(f"工具触发: time_tool，匹配关键词: {matched_keywords}")
                return tool_func()
    return None
