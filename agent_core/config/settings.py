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
from dotenv import load_dotenv

# 加载 .env（若不存在则静默跳过）
load_dotenv()


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

def get_embedding_base_url() -> str | None:
    return os.getenv("EMBEDDING_BASE_URL")

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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 所有 AI 生成的数据统一存放在 workspace/ 下，便于备份和迁移
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")

# 子目录定义（使用 os.path.join 确保跨平台兼容）
CHECKPOINT_DIR = os.path.join(WORKSPACE_DIR, "checkpoints")
VECTOR_STORE_DIR = os.path.join(WORKSPACE_DIR, "vector_stores")
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
LOGS_DIR = os.path.join(WORKSPACE_DIR, "logs")
CACHE_DIR = os.path.join(WORKSPACE_DIR, "cache")
TEMP_DIR = os.path.join(WORKSPACE_DIR, "temp")
UPLOAD_DIR = os.path.join(WORKSPACE_DIR, "uploads")

# 确保所有目录存在
for _dir in [WORKSPACE_DIR, CHECKPOINT_DIR, VECTOR_STORE_DIR, KNOWLEDGE_DIR, 
             LOGS_DIR, CACHE_DIR, TEMP_DIR, UPLOAD_DIR]:
    os.makedirs(_dir, exist_ok=True)

# 兼容旧模块引用（但值已指向 workspace 下的新路径）
PERSIST_DIR = VECTOR_STORE_DIR  # 原为 BASE_DIR/chroma_db

# ==================== RAG 配置 ====================
RAG_TOP_K = 3


# =============================================================================
# .env 读写工具（供设置页面 API 使用）
# =============================================================================
from pathlib import Path

# .env 文件路径（项目根目录）
ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

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