# OmniAgent 模型模块

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage

# 加载环境变量
load_dotenv()

# 从环境变量读取 API Key，优先使用 DASHSCOPE_API_KEY，其次 OPENAI_API_KEY
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")

# 创建全局 ChatOpenAI 实例
llm = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=api_key,
    temperature=0.7
)

# 与模型聊天的函数
def chat(messages: list[BaseMessage]) -> str:
    """与语言模型聊天
    
    参数:
        messages: BaseMessage 对象列表
        
    返回:
        str: 模型的回复内容
    """
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"聊天函数出错: {e}")
        return ""

# 测试代码
if __name__ == "__main__":
    # 测试聊天函数
    test_message = HumanMessage(content="你好")
    response = chat([test_message])
    print(f"模型回复: {response}") 