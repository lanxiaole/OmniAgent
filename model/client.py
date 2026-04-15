# OmniAgent 模型模块

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE
from tools import TOOLS
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)

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

# 绑定工具到模型
llm_with_tools = llm.bind_tools(TOOLS)


# 与模型聊天的函数（不使用工具）
def chat(messages: list[BaseMessage]) -> str:
    """与语言模型聊天
    
    参数:
        messages: BaseMessage 对象列表
        
    返回:
        str: 模型的回复内容
    """
    try:
        # 记录调用开始
        logger.debug(f"调用模型，消息数量: {len(messages)}")
        
        response = llm.invoke(messages)
        
        # 记录成功
        logger.info("模型响应成功")
        return response.content
    except Exception as e:
        # 记录异常
        logger.error(f"模型错误: {e}")
        return "抱歉，模型暂时无法响应，请稍后再试。"


# 与模型聊天的函数（使用工具）
def chat_with_tools(messages: list[BaseMessage]):
    """与语言模型聊天（使用工具）
    
    参数:
        messages: BaseMessage 对象列表
        
    返回:
        模型的原始响应（包含 tool_calls）
    """
    try:
        # 记录调用开始
        logger.debug(f"调用模型（带工具），消息数量: {len(messages)}")
        
        response = llm_with_tools.invoke(messages)
        
        # 记录成功
        logger.info("模型响应成功")
        return response
    except Exception as e:
        # 记录异常
        logger.error(f"模型错误: {e}")
        return None


# 测试代码
if __name__ == "__main__":
    # 测试聊天函数
    test_message = HumanMessage(content="你好")
    response = chat([test_message])
    logger.info(f"模型回复: {response}")
