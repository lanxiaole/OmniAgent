# 长期记忆工具模块
# 提供保存、检索和管理用户长期记忆的工具

from langchain_core.tools import tool
from agent_core.memory.memory_manager import get_user_memory_store
from agent_core.logger import get_logger

logger = get_logger(__name__)


@tool
def save_user_memory(content: str) -> str:
    """保存用户的长期记忆，会自动覆盖相似内容。当用户提到自己的身份、偏好、习惯、项目、经历等个人信息时调用此工具。
    
    参数:
        content: 需要保存的记忆内容，用第三人称描述用户的个人信息、偏好、习惯等。
        
    调用示例:
    - 用户: "我是小勒，我喜欢吃辣" -> 调用 save_user_memory("用户名字是小勒，喜欢吃辣")
    - 用户: "我住在北京" -> 调用 save_user_memory("用户住在北京")
    - 用户: "我正在做一个电商项目" -> 调用 save_user_memory("用户正在做一个电商项目")
    - 用户: "我不喜欢吃香菜" -> 调用 save_user_memory("用户不喜欢吃香菜")
    - 用户: "我不喜欢吃辣了" -> 调用 save_user_memory("用户不喜欢吃辣")，会自动覆盖"喜欢吃辣"
    
    注意: 此工具会自动检测相似记忆并覆盖，避免记忆冲突。
    """
    try:
        logger.debug(f"调用保存记忆工具，内容: {content}")
        memory_store = get_user_memory_store()
        # 使用 update_memory 方法，自动处理覆盖
        result = memory_store.update_memory(content)
        return result
    except Exception as e:
        logger.error(f"保存记忆失败: {e}")
        return "抱歉，保存记忆失败。"


@tool
def recall_user_memory(query: str) -> str:
    """【长期记忆（备选）】检索通过对话自动保存的用户偏好、习惯等记忆信息。此工具仅保存对话中用户随口提到的信息，**内容可能不完整**。
    
    优先级规则：**此工具是二级备选**。当用户询问与自己相关的问题时，必须先调用 search_personal_knowledge 查知识库。只有在知识库返回"未找到相关信息"后，才调用此工具。
    
    参数:
        query: 查询问题，用于检索相关记忆。
        
    调用示例:
    - 用户: "晚上吃什么" -> 先调用 search_personal_knowledge，未找到再调用 recall_user_memory("用户的饮食偏好")
    - 用户: "我叫什么名字" -> 先调用 search_personal_knowledge，未找到再调用 recall_user_memory("用户的名字")
    - 用户: "我喜欢什么" -> 先调用 search_personal_knowledge，未找到再调用 recall_user_memory("用户的喜好")
    - 用户: "我的项目是什么" -> 先调用 search_personal_knowledge，未找到再调用 recall_user_memory("用户的项目")
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


@tool
def list_user_memories() -> str:
    """列出所有用户长期记忆。当用户询问"你记得我什么"、"你知道我什么"时调用此工具。
    
    调用示例:
    - 用户: "你记得我什么" -> 调用 list_user_memories
    - 用户: "你知道关于我的什么" -> 调用 list_user_memories
    - 用户: "我让你记住过什么" -> 调用 list_user_memories
    """
    try:
        logger.debug("调用列出记忆工具")
        memory_store = get_user_memory_store()
        memories = memory_store.list_memories()
        if not memories:
            return "我还没有记住任何关于你的信息。"
        result = "我记住的关于你的信息：\n" + "\n".join(f"- {m['content']}" for m in memories)
        logger.info(f"列出记忆成功，共 {len(memories)} 条")
        return result
    except Exception as e:
        logger.error(f"列出记忆失败: {e}")
        return "抱歉，无法列出记忆。"


@tool
def delete_user_memory(query: str) -> str:
    """删除特定的用户记忆。当用户说"忘记我..."、"不要记住..."、"删除记忆..."时调用此工具。
    
    参数:
        query: 要删除的记忆内容的查询词。
        
    调用示例:
    - 用户: "忘记我喜欢吃辣" -> 调用 delete_user_memory("喜欢吃辣")
    - 用户: "不要记住我的住址" -> 调用 delete_user_memory("用户的住址")
    - 用户: "删除关于我名字的记忆" -> 调用 delete_user_memory("用户的名字")
    - 用户: "忘了我喜欢什么" -> 调用 delete_user_memory("用户的喜好")
    """
    try:
        logger.debug(f"调用删除记忆工具，查询: {query}")
        memory_store = get_user_memory_store()
        deleted_count = memory_store.delete_memory_by_query(query)
        if deleted_count > 0:
            return f"已删除 {deleted_count} 条记忆。"
        else:
            return "没有找到匹配的记忆。"
    except Exception as e:
        logger.error(f"删除记忆失败: {e}")
        return "抱歉，删除记忆失败。"


@tool
def clear_user_memories() -> str:
    """清空所有用户长期记忆。仅在用户明确要求"清空所有记忆"、"删除所有记忆"、"重新开始"时调用。
    
    调用示例:
    - 用户: "清空所有记忆" -> 调用 clear_user_memories
    - 用户: "删除我所有的记忆" -> 调用 clear_user_memories
    - 用户: "我想让你重新开始记住我" -> 调用 clear_user_memories
    """
    try:
        logger.debug("调用清空记忆工具")
        memory_store = get_user_memory_store()
        cleared_count = memory_store.clear_all_memories()
        if cleared_count > 0:
            return f"已清空所有记忆（共 {cleared_count} 条）。"
        else:
            return "没有需要清空的记忆。"
    except Exception as e:
        logger.error(f"清空记忆失败: {e}")
        return "抱歉，清空记忆失败。"