# OmniAgent 模型模块

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE

# 从环境变量读取 API Key，优先使用 DASHSCOPE_API_KEY，其次 OPENAI_API_KEY
api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
if not api_key:
    raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")

# 创建全局 ChatOpenAI 实例
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=api_key,
    temperature=TEMPERATURE
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