# tools 包初始化文件

from .time_tool import get_current_time
from .rag_tool import identify_user
from .weather_tool import get_weather

TOOLS = [get_current_time, identify_user, get_weather]

__all__ = ["TOOLS"]
