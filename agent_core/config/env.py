# .env 配置读写与动态配置 getter 模块
#
# 职责：
#   1. 动态配置 getter：从 os.environ 实时读取 LLM / Embedding / Tavily / 高德 等配置。
#   2. .env 文件读写工具：供设置页面 API 使用。
# 本模块依赖 paths 模块提供的 USER_DATA_DIR。

import os
from pathlib import Path
from agent_core.config.paths import USER_DATA_DIR


# =====================================================================
# 动态配置 getter（来自 .env，设置页面可管理）
# 使用 getter 函数每次从 os.environ 实时读取，保存后即时生效
# =====================================================================

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


# =====================================================================
# .env 读写工具（供设置页面 API 使用）
# =====================================================================

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


__all__ = [
    "get_llm_base_url",
    "get_llm_api_key",
    "get_llm_model_name",
    "get_embedding_base_url",
    "get_embedding_api_key",
    "get_embedding_model",
    "get_amap_api_key",
    "get_tavily_api_key",
    "get_tavily_search_depth",
    "get_tavily_extract_depth",
    "get_tavily_max_results",
    "ENV_FILE_PATH",
    "read_env",
    "write_env_key",
    "delete_env_key",
    "get_env_keys",
]