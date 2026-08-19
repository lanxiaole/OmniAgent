# 静态配置常量模块
#
# 职责：定义所有通过硬编码配置、不可在设置页面修改的常数值，
#       以及模型上下文窗口映射与查询函数。
# 本模块不依赖 paths/env/scenarios，属于纯常量模块。

# ==================== LLM 静态参数 ====================
# 温度参数（硬编码默认值，不可在设置页面修改）
LLM_TEMPERATURE = 0.7
# 总结模型：用于压缩历史消息。None 表示使用主模型
LLM_SUMMARIZER_MODEL = None

# ==================== 上下文压缩（总结）参数 ====================
# 触发总结的消息数阈值（测试期间设为3，生产环境改为30）
CONTEXT_SUMMARY_MESSAGE_TRIGGER = 30
# 压缩后保留的消息数（测试期间设为1，生产环境改为10）
CONTEXT_SUMMARY_KEEP_MESSAGES = 10

# ==================== Embedding 静态参数 ====================
# 向量维度（硬编码默认值，不可在设置页面修改）
EMBEDDING_DIMENSIONS = 1024

# ==================== 代码执行配置 ====================
# 系统目录黑名单，用于路径安全警告。None 表示使用 file_tool.py 中的默认列表
SYSTEM_DIRS = None
# 执行超时时间（秒）
EXECUTION_TIMEOUT = 30
# 最大重试次数
EXECUTION_MAX_RETRIES = 3
# 执行工作目录（None 表示使用 TEMP_DIR）
EXECUTION_WORK_DIR = None

# ==================== RAG 配置 ====================
RAG_TOP_K = 3

# ==================== 记忆检索配置 ====================
MEMORY_TOP_K = 3

# ==================== 模型上下文窗口配置 ====================
# 模型名称到上下文窗口大小的映射（单位：Token）
# 数据来源：各模型官方文档，随着模型版本更新可能需要调整
# 用于上下文统计面板展示 Token 使用率
MODEL_CONTEXT_WINDOWS = {
    # DeepSeek 系列
    "deepseek-v4-pro": 1_000_000,
    "deepseek-v4-flash": 1_000_000,
    "deepseek-v3": 131_072,
    "deepseek-v3.2": 131_072,
    "deepseek-r1": 131_072,
    "deepseek-coder-v2": 131_072,
    # Qwen 系列（通义千问）
    "qwen-3.8-max": 1_000_000,
    "qwen3.8-max": 1_000_000,
    "qwen-3.7-max": 1_000_000,
    "qwen3.7-max": 1_000_000,
    "qwen-max": 1_000_000,
    "qwen-plus": 131_072,
    "qwen-turbo": 1_000_000,
    "qwen-flash": 1_000_000,
    "qwen-72b": 131_072,
    "qwen72b": 131_072,
    "qwen-7b": 32_768,
    "qwen7b": 32_768,
    # OpenAI 系列
    "gpt-4": 8_192,
    "gpt-4-turbo": 128_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-5": 128_000,
    "o1": 200_000,
    "o3": 200_000,
    # Anthropic Claude 系列
    "claude-3": 200_000,
    "claude-3.5": 200_000,
    "claude-4": 200_000,
    "claude-opus": 200_000,
    "claude-sonnet": 200_000,
    "claude-haiku": 200_000,
    # Google Gemini 系列
    "gemini-2.5": 1_000_000,
    "gemini-2.0": 1_000_000,
    "gemini-1.5": 1_000_000,
    "gemini-1.0": 32_768,
    # 智谱 GLM 系列
    "glm-4": 128_000,
    "glm-4v": 128_000,
    "glm-3": 128_000,
    # 零一万物 Yi 系列
    "yi-34b": 200_000,
    "yi-6b": 200_000,
    # 月之暗面 Moonshot 系列
    "moonshot-v1": 128_000,
    "moonshot-v2": 128_000,
    "kimi": 128_000,
    # 百川 Baichuan 系列
    "baichuan-4": 128_000,
    "baichuan-3": 128_000,
    # 字节豆包系列
    "doubao": 128_000,
    "skylark": 128_000,
    # Meta LLaMA 系列
    "llama-3": 131_072,
    "llama-2": 4_096,
    # Mistral 系列
    "mistral-small": 32_768,
    "mistral-medium": 32_768,
    "mistral-large": 131_072,
    "mixtral": 32_768,
    "codestral": 256_000,
}


def get_model_context_window(model_name: str) -> int:
    """根据模型名称获取上下文窗口大小

    Args:
        model_name: 模型名称（如 qwen-max, deepseek-v4-flash）

    Returns:
        int: 上下文窗口大小（Token 数），默认 1_000_000
    """
    if not model_name:
        return 1000000
    model_lower = model_name.lower()
    for key, value in MODEL_CONTEXT_WINDOWS.items():
        if key in model_lower:
            return value
    return 1000000  # 默认值


__all__ = [
    "LLM_TEMPERATURE",
    "LLM_SUMMARIZER_MODEL",
    "CONTEXT_SUMMARY_MESSAGE_TRIGGER",
    "CONTEXT_SUMMARY_KEEP_MESSAGES",
    "EMBEDDING_DIMENSIONS",
    "SYSTEM_DIRS",
    "EXECUTION_TIMEOUT",
    "EXECUTION_MAX_RETRIES",
    "EXECUTION_WORK_DIR",
    "RAG_TOP_K",
    "MEMORY_TOP_K",
    "MODEL_CONTEXT_WINDOWS",
    "get_model_context_window",
]