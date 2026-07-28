# tools 包初始化文件

from .time_tool import get_current_time
from .rag_tool import search_personal_knowledge
from .weather_tool import get_weather

TOOLS = [get_current_time, search_personal_knowledge, get_weather]

__all__ = ["TOOLS"]
