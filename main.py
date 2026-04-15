# OmniAgent 主模块

import os
import memory
import model
import tools
from rag import retrieve, build_vector_store
from config import PERSIST_DIR
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)


# 构建增强消息函数
def build_enhanced_message(user_input: str) -> str:
    """构建增强消息
    
    参数:
        user_input: 用户输入
        
    返回:
        str: 增强后的消息
    """
    # 尝试使用工具
    tool_result = tools.maybe_use_tool(user_input)
    if tool_result is not None:
        return f"用户问：{user_input}\n[工具结果]：{tool_result}\n请根据工具结果回答用户。"
    
    # 尝试检索知识
    retrieval_results = retrieve(user_input)
    if retrieval_results:
        knowledge = retrieval_results[0]
        return f"用户问：{user_input}\n[参考知识]：{knowledge}\n请基于参考知识回答用户。如果参考知识不足以回答，可以说'我不确定'。"
    
    # 直接返回用户输入
    return user_input


# 主函数
def main():
    """主函数"""
    # 记录启动信息
    logger.info("OmniAgent 已启动，输入 quit 退出。")
    print("OmniAgent 已启动，输入 quit 退出。")
    
    # 自动检查并构建向量库
    logger.info("检查知识库状态...")
    build_vector_store()
    
    # 进入对话循环
    while True:
        # 获取用户输入
        user_input = input("你: ")
        
        # 记录用户输入
        logger.debug(f"用户输入: {user_input}")
        
        # 检查是否退出
        if user_input in ["quit", "exit", "q"]:
            logger.info("用户退出对话")
            print("再见！")
            break
        
        try:
            # 构建增强消息
            enhanced_input = build_enhanced_message(user_input)
            
            # 记录增强后的消息
            logger.debug(f"增强消息: {enhanced_input}")
            
            # 添加用户消息到记忆
            memory.add_user_message(enhanced_input)
            
            # 调用模型获取回复
            reply = model.chat(memory.get_messages())
            
            # 记录模型回复（截断长回复）
            logger.debug(f"助手回复: {reply[:100]}...")
            
            # 添加AI消息到记忆
            memory.add_ai_message(reply)
            
            # 打印回复
            print("助手: " + reply)
            
        except Exception as e:
            # 记录异常，包含堆栈信息
            logger.error(f"主循环错误: {e}", exc_info=True)
            print(f"[系统错误] {e}，已跳过本轮对话。")
            continue


if __name__ == "__main__":
    main()
