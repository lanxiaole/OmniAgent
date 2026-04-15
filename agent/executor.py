# Agent 执行器模块

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE
from tools import TOOLS
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 从环境变量读取 API Key
api_key = DASHSCOPE_API_KEY or OPENAI_API_KEY
if not api_key:
    raise Exception("未找到 API key。请在 .env 文件中设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY。")

# 创建模型实例
model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=api_key,
    temperature=TEMPERATURE
)

# 系统提示
system_prompt = """你是一个智能助手，名叫 OmniAgent。你可以使用工具来回答问题，比如获取当前时间或从知识库中检索信息。当你获得足够信息后，直接回答用户的问题。"""

# 创建 Agent 执行器
def create_agent_executor():
    """创建 Agent 执行器"""
    try:
        logger.info("创建 Agent 执行器...")
        
        # 创建 Agent
        agent = create_agent(
            model=model,
            tools=TOOLS,
            system_prompt=system_prompt
        )
        
        logger.info("Agent 执行器创建成功")
        return agent
    except Exception as e:
        logger.error(f"创建 Agent 执行器失败: {e}")
        raise

# 全局 Agent 执行器实例
global_agent_executor = create_agent_executor()

# 执行 Agent 调用
def run_agent(user_input: str, thread_id: str = "default") -> str:
    """执行 Agent 调用
    
    参数:
        input_text: 用户输入
        thread_id: 对话线程 ID
        
    返回:
        str: Agent 的回复
    """
    try:
        logger.debug(f"执行 Agent 调用，输入: {user_input}")
        
        # 执行 Agent 调用
        config = {"configurable": {"thread_id": thread_id}}
        result = global_agent_executor.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )
        
        logger.info("Agent 调用成功")
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Agent 调用失败: {e}")
        return "抱歉，我暂时无法回答这个问题。"
