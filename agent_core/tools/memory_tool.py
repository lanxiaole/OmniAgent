# 长期记忆工具模块
# 提供保存和检索用户长期记忆的工具

from langchain_core.tools import tool
from agent_core.memory.memory_manager import get_user_memory_store
from agent_core.logger import get_logger

logger = get_logger(__name__)


@tool
def save_user_memory(content: str) -> str:
    """保存用户的长期记忆。当用户提到自己的身份、偏好、习惯、项目、经历等个人信息时调用此工具。
    
    参数:
        content: 需要保存的记忆内容，描述用户的个人信息、偏好、习惯等。
        
    调用示例:
    - 用户: "我是小勒，我喜欢吃辣" -> 调用 save_user_memory("用户名字是小勒，喜欢吃辣")
    - 用户: "我住在北京" -> 调用 save_user_memory("用户住在北京")
    - 用户: "我正在做一个电商项目" -> 调用 save_user_memory("用户正在做一个电商项目")
    - 用户: "我不喜欢吃香菜" -> 调用 save_user_memory("用户不喜欢吃香菜")
    - 用户: "我会弹钢琴" -> 调用 save_user_memory("用户会弹钢琴")
    """
    try:
        logger.debug(f"调用保存记忆工具，内容: {content}")
        memory_store = get_user_memory_store()
        memory_store.add_memory(content)
        return f"已保存记忆: {content}"
    except Exception as e:
        logger.error(f"保存记忆失败: {e}")
        return "抱歉，保存记忆失败。"


@tool
def recall_user_memory(query: str) -> str:
    """检索用户的长期记忆。当用户询问与自己相关的问题，且当前会话记忆中没有答案时调用此工具。
    
    参数:
        query: 查询问题，用于检索相关记忆。
        
    调用示例:
    - 用户: "晚上吃什么" -> 调用 recall_user_memory("用户的饮食偏好")
    - 用户: "我叫什么名字" -> 调用 recall_user_memory("用户的名字")
    - 用户: "我喜欢什么" -> 调用 recall_user_memory("用户的喜好")
    - 用户: "我来自哪里" -> 调用 recall_user_memory("用户的住址或家乡")
    - 用户: "我的项目是什么" -> 调用 recall_user_memory("用户的项目")
    """
    try:
        logger.debug(f"调用检索记忆工具，查询: {query}")
        memory_store = get_user_memory_store()
        memories = memory_store.similarity_search(query)
        if not memories:
            return "未找到相关记忆。"
        result = "\n\n".join(memories)
        logger.info(f"记忆检索成功，返回 {len(memories)} 条")
        return result
    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        return "抱歉，检索记忆失败。"