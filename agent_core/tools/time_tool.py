# OmniAgent 工具模块

from langchain_core.tools import tool


@tool
# type: ignore
def get_current_time() -> str:
    """获取当前日期和时间，当用户询问时间、几点、现在时刻时调用此工具。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
