# Agent 执行器模块

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, MODEL_NAME, BASE_URL, TEMPERATURE
from tools import TOOLS
from logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 会话记忆存储
_sessions: dict[str, list[dict]] = {}

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
system_prompt = """你是一个智能助手，名叫 OmniAgent。
对于用户询问个人信息（名字、家乡、学校、技术栈、项目、学习、游戏、实习等）的问题，你必须调用 `query_knowledge` 工具，然后基于工具返回的结果回答。
对于时间问题，调用 `get_current_time`。
其他普通问题直接回答。"""

# 创建 Agent 执行器
def create_agent_executor():
    """创建 Agent 执行器"""
    try:
        logger.info("创建 Agent 执行器...")
        
        # 打印 TOOLS 名称列表以便调试
        tool_names = [tool.name for tool in TOOLS]
        logger.debug(f"可用工具列表: {tool_names}")
        
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
        
        # 获取会话历史
        history = _sessions.get(thread_id, [])
        
        # 构造消息列表
        messages = history + [{"role": "user", "content": user_input}]
        
        # 执行 Agent 调用
        config = {"configurable": {"thread_id": thread_id}}
        result = global_agent_executor.invoke(
            {"messages": messages},
            config=config
        )
        
        # 调试打印，观察是否有 tool_calls
        logger.debug(f"Agent 调用结果: {result['messages'][-1]}")
        
        # 提取回复
        assistant_reply = result["messages"][-1].content
        
        # 更新会话历史
        if thread_id not in _sessions:
            _sessions[thread_id] = []
        _sessions[thread_id].append({"role": "user", "content": user_input})
        _sessions[thread_id].append({"role": "assistant", "content": assistant_reply})
        
        logger.info("Agent 调用成功")
        return assistant_reply
    except Exception as e:
        logger.error(f"Agent 调用失败: {e}")
        return "抱歉，我暂时无法回答这个问题。"


def clear_session(thread_id: str = "default") -> None:
    """清空指定会话的历史
    
    参数:
        thread_id: 对话线程 ID
    """
    if thread_id in _sessions:
        del _sessions[thread_id]
        logger.info(f"会话 {thread_id} 已清空")
