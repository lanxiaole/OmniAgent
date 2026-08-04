# tools 包初始化文件

from .time_tool import get_current_time
from .rag_tool import search_personal_knowledge
from .weather_tool import get_weather
from .memory_tool import (
    save_user_memory,
    recall_user_memory,
    list_user_memories,
    delete_user_memory,
    clear_user_memories,
)
from .file_tool import read_file, write_file, list_directory, search_files
from .executor_tool import execute_python
from .search_tool import search_web, read_webpage

# 包装需要审批的工具
from agent_core.agent.middleware import wrap_tool_with_approval

TOOLS = [
    get_current_time,
    search_personal_knowledge,
    get_weather,
    save_user_memory,
    recall_user_memory,
    list_user_memories,
    delete_user_memory,
    clear_user_memories,
    read_file,
    wrap_tool_with_approval(write_file),       # 写入操作审批
    list_directory,
    search_files,
    wrap_tool_with_approval(execute_python),    # 代码执行审批
    search_web,
    read_webpage,
]

__all__ = ["TOOLS"]