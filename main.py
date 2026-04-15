# OmniAgent 主模块

import os
import memory
import model
from langchain_core.messages import ToolMessage
from rag import retrieve, build_vector_store
from tools import get_current_time
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
    # 尝试 RAG 检索
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
            logger.debug(f"增强消息: {enhanced_input}")
            
            # 添加用户消息到记忆
            memory.add_user_message(enhanced_input)
            
            # 调用模型获取回复（带工具）
            ai_msg = model.chat_with_tools(memory.get_messages())
            
            # 检查是否有工具调用
            if ai_msg and hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
                logger.info(f"模型调用了 {len(ai_msg.tool_calls)} 个工具")
                
                # 遍历工具调用
                for tool_call in ai_msg.tool_calls:
                    tool_name = tool_call.get('name')
                    logger.info(f"工具调用: {tool_name}")
                    
                    # 执行对应工具
                    if tool_name == 'get_current_time':
                        tool_result = get_current_time()
                    else:
                        tool_result = "未知工具"
                    
                    # 创建 ToolMessage
                    tool_message = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.get('id'),
                        name=tool_name
                    )
                    
                    # 添加 ToolMessage 到记忆
                    memory.add_ai_message(ai_msg)  # 添加 AI 消息（包含工具调用）
                    memory.add_user_message(tool_message)  # 添加工具结果
                
                # 再次调用模型生成最终回复
                final_reply = model.chat(memory.get_messages())
                logger.debug(f"助手最终回复: {final_reply[:100]}...")
                
                # 添加最终回复到记忆
                memory.add_ai_message(final_reply)
                
                # 打印回复
                print("助手: " + final_reply)
            else:
                # 直接使用模型回复
                if ai_msg and hasattr(ai_msg, 'content'):
                    reply = ai_msg.content
                else:
                    reply = "抱歉，模型暂时无法响应，请稍后再试。"
                
                logger.debug(f"助手回复: {reply[:100]}...")
                
                # 添加 AI 消息到记忆
                memory.add_ai_message(reply)
                
                # 打印回复
                print("助手: " + reply)
        except Exception as e:
            # 记录异常
            logger.error(f"主循环错误: {e}", exc_info=True)
            print(f"[系统错误] {e}，已跳过本轮对话。")
            continue


if __name__ == "__main__":
    main()
