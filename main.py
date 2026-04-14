# OmniAgent 主模块

import os
import memory
import model
import tools
import rag

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
    retrieval_results = rag.retrieve(user_input, top_k=1)
    if retrieval_results:
        knowledge = retrieval_results[0]
        return f"用户问：{user_input}\n[参考知识]：{knowledge}\n请基于参考知识回答用户。如果参考知识不足以回答，可以说'我不确定'。"
    
    # 直接返回用户输入
    return user_input

# 主函数
def main():
    """主函数"""
    # 打印欢迎语
    print("OmniAgent 已启动，输入 quit 退出。")
    
    # 检查向量库是否存在
    if not os.path.exists(rag.PERSIST_DIR):
        print("请先运行 python rag.py 构建向量库。")
    
    # 进入对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ")
            
            # 检查是否退出
            if user_input in ["quit", "exit", "q"]:
                print("再见！")
                break
            
            # 构建增强消息
            enhanced_input = build_enhanced_message(user_input)
            
            # 添加用户消息到记忆
            memory.add_user_message(enhanced_input)
            
            # 调用模型获取回复
            reply = model.chat(memory.get_messages())
            
            # 添加AI消息到记忆
            memory.add_ai_message(reply)
            
            # 打印回复
            print("助手: " + reply)
            
        except Exception as e:
            print(f"发生错误: {e}")
            continue

if __name__ == "__main__":
    main()