# 配置管理模块
#
# 设计原则：
#   1. 所有可通过设置页面 UI 修改的配置 → 存放在项目根目录 .env 文件中，
#      通过 getter 函数动态读取，保存后即时生效，无需重启。
#   2. 所有不可通过设置页面修改的配置 → 硬编码为模块级常量。
#   3. 目录/路径相关配置 → 硬编码为模块级常量。
#   4. .env 读写工具函数 → 保留在本文件中，供设置页面 API 使用。
#
# 新克隆项目时无需手动创建 .env 文件，启动后通过设置页面配置即可
# 自动生成 .env。

import os
import shutil
from pathlib import Path
import appdirs
from dotenv import load_dotenv


# =============================================================================
# 用户数据目录（操作系统标准位置）
# Windows: %APPDATA%\OmniAgent
# macOS:   ~/Library/Application Support/OmniAgent
# Linux:   ~/.local/share/OmniAgent
# =============================================================================
USER_DATA_DIR = appdirs.user_data_dir("OmniAgent", appauthor="", roaming=True)
os.makedirs(USER_DATA_DIR, exist_ok=True)

# 旧数据目录（项目根目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD_ENV_PATH = os.path.join(BASE_DIR, ".env")
OLD_WORKSPACE_PATH = os.path.join(BASE_DIR, "workspace")
NEW_ENV_PATH = os.path.join(USER_DATA_DIR, ".env")
NEW_WORKSPACE_PATH = os.path.join(USER_DATA_DIR, "workspace")

# 兼容迁移：若旧数据存在且新目录下没有，则自动迁移一次
_should_migrate_env = os.path.isfile(OLD_ENV_PATH) and not os.path.isfile(NEW_ENV_PATH)
_should_migrate_workspace = os.path.isdir(OLD_WORKSPACE_PATH) and not os.path.isdir(NEW_WORKSPACE_PATH)

if _should_migrate_env or _should_migrate_workspace:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    if _should_migrate_env:
        shutil.move(OLD_ENV_PATH, NEW_ENV_PATH)
    if _should_migrate_workspace:
        shutil.move(OLD_WORKSPACE_PATH, NEW_WORKSPACE_PATH)

# 从 USER_DATA_DIR/.env 加载配置
load_dotenv(dotenv_path=NEW_ENV_PATH, override=True)


# =============================================================================
# 动态配置（来自 .env，设置页面可管理）
# 使用 getter 函数每次从 os.environ 实时读取，保存后即时生效
# =============================================================================


# ==================== LLM 配置 ====================

def get_llm_base_url() -> str | None:
    return os.getenv("LLM_BASE_URL")

def get_llm_api_key() -> str | None:
    return os.getenv("LLM_API_KEY")

def get_llm_model_name() -> str | None:
    return os.getenv("LLM_MODEL")


# ==================== Embedding 配置 ====================

def get_embedding_base_url() -> str:
    # 默认使用阿里云百炼（DashScope），与设置页面 ENV_CONFIG_DEFINITIONS 中的 default 一致
    return os.getenv("EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

def get_embedding_api_key() -> str | None:
    return os.getenv("EMBEDDING_API_KEY")

def get_embedding_model() -> str | None:
    return os.getenv("EMBEDDING_MODEL")


# ==================== 工具配置 ====================

def get_amap_api_key() -> str | None:
    return os.getenv("AMAP_API_KEY")


# ==================== Tavily 联网搜索配置 ====================

def get_tavily_api_key() -> str | None:
    return os.getenv("TAVILY_API_KEY")

def get_tavily_search_depth() -> str:
    return os.getenv("TAVILY_SEARCH_DEPTH", "basic")

def get_tavily_extract_depth() -> str:
    return os.getenv("TAVILY_EXTRACT_DEPTH", "basic")

def get_tavily_max_results() -> int:
    return int(os.getenv("TAVILY_MAX_RESULTS", "5"))


# =============================================================================
# 静态配置（硬编码，不可在设置页面修改）
# =============================================================================

# ==================== LLM 静态参数 ====================
# 温度参数（硬编码默认值，不可在设置页面修改）
LLM_TEMPERATURE = 0.7
# 总结模型：用于压缩历史消息。None 表示使用主模型
LLM_SUMMARIZER_MODEL = None

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

# ==================== 目录配置 ====================

# 所有 AI 生成的数据统一存放在 USER_DATA_DIR/workspace/ 下，便于备份和迁移
WORKSPACE_DIR = os.path.join(USER_DATA_DIR, "workspace")

# 子目录定义（使用 os.path.join 确保跨平台兼容）
CHECKPOINT_DIR = os.path.join(WORKSPACE_DIR, "checkpoints")
VECTOR_STORE_DIR = os.path.join(WORKSPACE_DIR, "vector_stores")
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
LOGS_DIR = os.path.join(WORKSPACE_DIR, "logs")
CACHE_DIR = os.path.join(WORKSPACE_DIR, "cache")
TEMP_DIR = os.path.join(WORKSPACE_DIR, "temp")
UPLOAD_DIR = os.path.join(WORKSPACE_DIR, "uploads")
MEMORY_DIR = os.path.join(WORKSPACE_DIR, "memory")

# 确保所有目录存在
for _dir in [WORKSPACE_DIR, CHECKPOINT_DIR, VECTOR_STORE_DIR, KNOWLEDGE_DIR, 
             LOGS_DIR, CACHE_DIR, TEMP_DIR, UPLOAD_DIR, MEMORY_DIR]:
    os.makedirs(_dir, exist_ok=True)

# 兼容旧模块引用（但值已指向 workspace 下的新路径）
PERSIST_DIR = VECTOR_STORE_DIR  # 原为 BASE_DIR/chroma_db

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


# =============================================================================
# .env 读写工具（供设置页面 API 使用）
# =============================================================================

# .env 文件路径（用户数据目录）
ENV_FILE_PATH = Path(USER_DATA_DIR) / ".env"

def read_env() -> dict[str, str]:
    """
    读取 .env 文件，返回键值对字典
    忽略空行和注释行（以 # 开头）
    """
    env_vars = {}
    if not ENV_FILE_PATH.exists():
        return env_vars
    with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def write_env_key(key: str, value: str) -> bool:
    """
    写入或更新 .env 文件中的单个变量（保留注释和原有顺序）
    如果文件不存在则自动创建
    """
    lines = []
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # 查找目标键所在的行（跳过注释行）
    target_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k == key:
                target_idx = i
                break

    if target_idx is not None:
        lines[target_idx] = f"{key}={value}\n"
    else:
        lines.append(f"{key}={value}\n")

    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    # 同步更新当前进程的环境变量
    os.environ[key] = value
    return True

def delete_env_key(key: str) -> bool:
    """
    从 .env 文件中删除指定变量（保留注释和原有顺序）
    返回是否删除成功
    """
    lines = []
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k == key:
                found = True
                continue
        new_lines.append(line)

    if not found:
        return False

    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    # 从当前进程的环境变量中删除
    os.environ.pop(key, None)
    return True

def get_env_keys(prefix: str) -> list[str]:
    """
    获取 .env 中所有以指定前缀开头的键名列表
    用于查找模型配置
    """
    env_vars = read_env()
    return [k for k in env_vars.keys() if k.startswith(prefix)]


# =============================================================================
# 场景切换（Scenario）配置
# =============================================================================

import json
import logging

# 场景配置文件路径（与 settings.py 同目录）
SCENARIOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios.json")

# 硬编码的默认预设（兜底方案）
_DEFAULT_PRESETS = [
    {
        "id": "default",
        "name": "通用助手",
        "icon": "ChatRound",
        "description": "均衡的日常助理，适用大部分场景",
        "system_prompt": "你是一个智能AI助手，名为 OmniAgent。",
        "enabled_tools": ["all"],
    }
]


def _create_default_scenarios_file() -> None:
    """创建默认的 scenarios.json 配置文件"""
    import shutil
    default_content = {
        "presets": [
            {
                "id": "default",
                "name": "通用助手",
                "icon": "ChatRound",
                "description": "均衡的日常助理，适用大部分场景",
                "system_prompt": "你是一个智能AI助手，名为 OmniAgent。\n\n## 核心能力\n你拥有以下工具可供使用，根据用户需求选择最合适的工具：\n\n### 信息查询\n- 当前时间查询\n- 联网搜索（获取实时信息）\n- 网页内容读取\n- 知识库检索（搜索本地知识库）\n\n### 天气查询\n- 查询指定城市天气\n\n### 记忆管理\n- 保存用户记忆（记住用户偏好和重要信息）\n- 回忆用户记忆（检索用户之前保存的信息）\n- 列出所有记忆\n- 删除指定记忆\n- 清空所有记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（需要用户审批）\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 回答问题前，先充分理解用户意图。\n3. 使用工具时，清晰说明正在做什么以及为什么。\n4. 如果工具调用失败，给出友好的错误提示和替代方案。\n5. 对于需要审批的操作（写入文件、执行代码），先向用户说明将要执行的操作，等待用户确认。\n6. 联网搜索时，在回答中标注信息来源。\n7. 使用记忆功能记住用户的关键偏好和上下文信息，提供更个性化的服务。\n8. 如果你不知道答案或无法获取信息，诚实地告诉用户，不要编造信息。",
                "enabled_tools": ["all"],
            },
            {
                "id": "coder",
                "name": "编程专家",
                "icon": "Cpu",
                "description": "专注代码编写、调试与架构设计",
                "system_prompt": "你是一位资深软件工程师，精通多种编程语言和软件架构设计。\n\n## 核心能力\n你可以使用以下工具来协助编程任务：\n\n### 文件操作\n- 读取文件内容\n- 写入文件（需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（需要用户审批）\n\n### 信息查询\n- 联网搜索（查找技术文档、解决方案）\n- 网页内容读取\n- 当前时间查询\n\n### 记忆管理\n- 保存用户记忆\n- 回忆用户记忆\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 在编写代码前，先理解需求并给出设计方案。\n3. 注释使用中文，代码中的变量名、函数名使用英文。\n4. 注重代码质量：可读性、可维护性、性能和安全性。\n5. 对于需要审批的操作，先向用户说明将要执行的操作。\n6. 调试时，系统性地分析问题，给出根因分析和修复方案。\n7. 提供完整的代码示例，而不仅仅是代码片段。\n8. 如果用户的项目涉及框架，遵循该框架的最佳实践和约定。",
                "enabled_tools": ["read_file", "write_file", "list_directory", "search_files", "execute_python", "search_web", "read_webpage", "get_current_time", "save_user_memory", "recall_user_memory"],
            },
            {
                "id": "researcher",
                "name": "研究顾问",
                "icon": "Search",
                "description": "深度信息检索与分析，研究报告撰写",
                "system_prompt": "你是一位专业的研究顾问，擅长信息检索、数据分析和研究报告撰写。\n\n## 核心能力\n你可以使用以下工具来进行研究工作：\n\n### 信息查询\n- 联网搜索（多角度搜索，获取全面信息）\n- 网页内容读取（深入阅读源材料）\n- 知识库检索（查询本地知识库）\n\n### 记忆管理\n- 保存用户记忆（保存研究过程中的关键发现）\n- 回忆用户记忆\n- 列出所有记忆\n- 删除指定记忆\n- 清空所有记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（保存研究笔记和报告，需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n### 代码执行\n- 执行 Python 代码（数据分析、数据可视化，需要用户审批）\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 研究过程要系统化：先明确问题，再收集信息，然后分析，最后得出结论。\n3. 多源交叉验证，避免单一信息源的偏见。\n4. 在回答中标注信息来源，提供可追溯的引用链接。\n5. 对于复杂主题，提供结构化的分析报告。\n6. 区分事实和观点，对不确定的信息说明置信度。\n7. 如果信息不足，明确指出局限性并建议进一步的研究方向。\n8. 保存关键研究发现到记忆中，以便后续查询时参考。",
                "enabled_tools": ["search_web", "read_webpage", "search_knowledge", "get_current_time", "save_user_memory", "recall_user_memory", "list_user_memories", "delete_user_memory", "clear_user_memories", "read_file", "write_file", "list_directory", "search_files", "execute_python"],
            },
            {
                "id": "writer",
                "name": "创意写作",
                "icon": "EditPen",
                "description": "文章创作、文案润色与内容策划",
                "system_prompt": "你是一位专业的创意写作助手，擅长各类文体创作、文案润色和内容策划。\n\n## 核心能力\n你可以使用以下工具辅助写作工作：\n\n### 信息查询\n- 联网搜索（查找参考资料和素材）\n- 网页内容读取\n- 当前时间查询\n\n### 记忆管理\n- 保存用户记忆（记住写作风格偏好）\n- 回忆用户记忆\n\n### 文件操作\n- 读取文件内容\n- 写入文件（保存创作内容，需要用户审批）\n- 列出目录内容\n- 搜索文件\n\n## 行为准则\n1. 始终使用中文回复用户，除非用户明确要求使用其他语言。\n2. 创作前先了解目标受众、文体要求和风格偏好。\n3. 提供多种写作方案供用户选择。\n4. 注重文字的美感、节奏和表现力。\n5. 润色时保留原文的核心信息和风格，提升表达质量。\n6. 对于长篇内容，提供清晰的结构大纲。\n7. 引用的资料和数据标注来源。\n8. 保存用户的写作风格偏好到记忆中，以便持续提供一致的写作体验。",
                "enabled_tools": ["search_web", "read_webpage", "get_current_time", "save_user_memory", "recall_user_memory", "read_file", "write_file", "list_directory", "search_files"],
            },
        ]
    }
    try:
        os.makedirs(os.path.dirname(SCENARIOS_FILE), exist_ok=True)
        with open(SCENARIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_content, f, ensure_ascii=False, indent=2)
        logging.getLogger(__name__).info(f"[Scenario] 已创建默认场景配置文件: {SCENARIOS_FILE}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"[Scenario] 创建默认场景配置文件失败: {e}")


def load_scenarios() -> dict:
    """读取 scenarios.json 并解析为 Python 字典

    如果文件不存在，自动创建默认配置文件后返回。
    如果文件存在但解析失败，记录错误日志并返回硬编码兜底配置。

    Returns:
        dict: 包含 presets 列表的字典
    """
    logger = logging.getLogger(__name__)

    # 文件不存在，自动创建
    if not os.path.isfile(SCENARIOS_FILE):
        logger.info(f"[Scenario] 场景配置文件不存在，自动创建: {SCENARIOS_FILE}")
        _create_default_scenarios_file()

    # 读取并解析
    try:
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "presets" not in data or not isinstance(data["presets"], list):
            raise ValueError("scenarios.json 缺少 presets 字段或不是数组")
        return data
    except Exception as e:
        logger.error(f"[Scenario] 加载配置文件失败，使用默认配置: {e}")
        return {"presets": _DEFAULT_PRESETS}


def get_scenario(scenario_id: str) -> dict:
    """获取指定 ID 的场景预设

    如果找不到匹配的场景，回退到 default 预设。
    返回值始终包含所有必填字段。

    Args:
        scenario_id: 场景唯一标识符

    Returns:
        dict: 场景配置对象
    """
    data = load_scenarios()
    presets = data.get("presets", [])

    # 查找匹配的场景
    for preset in presets:
        if preset.get("id") == scenario_id:
            return preset

    # 查找 default 预设
    for preset in presets:
        if preset.get("id") == "default":
            logging.getLogger(__name__).warning(
                f"[Scenario] 未找到场景 '{scenario_id}'，回退到 default"
            )
            return preset

    # 连 default 都没有，返回硬编码兜底
    logging.getLogger(__name__).warning(
        f"[Scenario] 未找到场景 '{scenario_id}' 且无 default 预设，使用硬编码兜底"
    )
    return dict(_DEFAULT_PRESETS[0])


def get_current_scenario_id() -> str:
    """从 .env 文件读取 OMNI_SCENARIO 环境变量

    实时读取（不使用缓存），因为用户可能在运行时切换场景。
    如果未设置，返回 "default"。

    Returns:
        str: 当前场景 ID
    """
    return os.getenv("OMNI_SCENARIO", "default")


def get_active_system_prompt() -> str:
    """获取当前场景的 System Prompt

    此函数完全替代原有的 SYSTEM_PROMPT 常量。
    所有调用方都应迁移到此函数。

    Returns:
        str: 当前场景的 system_prompt 文本
    """
    scenario_id = get_current_scenario_id()
    scenario = get_scenario(scenario_id)
    return scenario.get("system_prompt", "")