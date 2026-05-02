# OmniAgent 主模块

import os
from agent_core.rag import build_vector_store
from agent_core.agent import run_agent
from agent_core.logger import get_logger

# 创建 logger
logger = get_logger(__name__)


# 主函数
def main():
    """主函数"""
    # 记录启动信息
    logger.info("OmniAgent 已启动，输入 quit 退出。")
    print("OmniAgent 已启动，输入 quit 退出。")
    
    # 自动检查并构建向量库
    logger.info("检查知识库状态...")
    build_vector_store()
    
    # 对话线程 ID（可以基于时间戳或其他方式生成唯一 ID）
    thread_id = "default"
    
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
            # 执行 Agent 调用
            reply = run_agent(user_input, thread_id)
            logger.debug(f"助手回复: {reply[:100]}...")
            
            # 打印回复
            print("助手: " + reply)
        except Exception as e:
            # 记录异常
            logger.error(f"主循环错误: {e}", exc_info=True)
            print(f"[系统错误] {e}，已跳过本轮对话。")
            continue


if __name__ == "__main__":
    main()
