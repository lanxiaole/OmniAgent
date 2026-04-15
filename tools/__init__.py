# tools 包初始化文件

from .time_tool import get_current_time
from .rag_tool import query_knowledge

TOOLS = [get_current_time, query_knowledge]

__all__ = ["TOOLS"]
