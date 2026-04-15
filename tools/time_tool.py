# OmniAgent 工具模块

from langchain_core.tools import tool
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


@tool
# type: ignore
def get_current_time() -> str:
    """获取当前日期和时间，当用户询问时间、几点、现在时刻时调用此工具。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 工具列表
TOOLS = [get_current_time]
