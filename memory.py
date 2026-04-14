# OmniAgent 记忆模块

from langchain_core.messages import HumanMessage, AIMessage

# 全局消息列表，用于存储对话历史
_messages = []

# 添加用户消息到对话历史
def add_user_message(content: str):
    """添加用户消息到对话历史
    
    参数:
        content: 用户消息内容
    """
    message = HumanMessage(content=content)
    _messages.append(message)

# 添加AI消息到对话历史
def add_ai_message(content: str):
    """添加AI消息到对话历史
    
    参数:
        content: AI消息内容
    """
    message = AIMessage(content=content)
    _messages.append(message)

# 获取对话历史消息列表
def get_messages() -> list:
    """获取对话历史消息列表
    
    返回:
        list: 对话历史消息列表
    """
    return _messages

# 清空对话历史
def clear():
    """清空对话历史"""
    _messages.clear()

# 获取最近k条消息
def get_last_k(k: int) -> list:
    """获取最近k条消息
    
    参数:
        k: 要获取的消息数量
        
    返回:
        list: 最近k条消息
    """
    return _messages[-k:] if k < len(_messages) else _messages