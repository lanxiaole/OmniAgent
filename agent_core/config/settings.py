# 配置管理模块
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def _require_env(var_names: list[str], config_label: str) -> None:
    """
    校验必填环境变量，缺失时抛出异常
    @param var_names: 需要校验的环境变量名列表
    @param config_label: 配置标签（如 "LLM" 或 "Embedding"），用于生成友好错误信息
    """
    missing = [name for name in var_names if not os.getenv(name)]
    if missing:
        raise ValueError(
            f".env 中缺少必需的 {config_label} 配置项: {', '.join(missing)}。"
            f"请参考 .env.example 中的示例填写。"
        )


# ==================== LLM 配置 ====================
# LLM 和 Embedding 是完全独立的两套配置，互不影响。
# 每个值都需要从对应的服务商文档获取，直接填入即可。

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
# 总结模型：用于压缩历史消息。默认与主模型相同，可单独指定更便宜的模型
LLM_SUMMARIZER_MODEL = os.getenv("LLM_SUMMARIZER_MODEL") or LLM_MODEL

# LLM 必填项校验
_require_env(["LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"], "LLM")


# ==================== Embedding 配置 ====================
# Embedding 完全独立配置，可与 LLM 使用不同平台。
# 例如：LLM 用 DeepSeek（不支持 Embedding），Embedding 用阿里云百炼。

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
# 向量维度（可选，部分模型如 text-embedding-v3/v4 支持自定义）
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

# Embedding 必填项校验
_require_env(["EMBEDDING_BASE_URL", "EMBEDDING_API_KEY", "EMBEDDING_MODEL"], "Embedding")


# ==================== 工具配置 ====================
AMAP_API_KEY = os.getenv("AMAP_API_KEY")

# ==================== 文件系统配置 ====================
# 系统目录黑名单（逗号分隔），用于路径安全警告
SYSTEM_DIRS = os.getenv("SYSTEM_DIRS")

# ==================== 代码执行配置 ====================
# 执行超时时间（秒）
EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "30"))
# 最大重试次数
EXECUTION_MAX_RETRIES = int(os.getenv("EXECUTION_MAX_RETRIES", "3"))
# 执行工作目录
EXECUTION_WORK_DIR = os.getenv("EXECUTION_WORK_DIR")


# ==================== Tavily 联网搜索配置 ====================
# Tavily API Key（从 https://app.tavily.com 获取，每月 1000 免费积分）
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# 搜索深度：basic（1积分/次）或 advanced（2积分/次），默认 basic
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
# 提取深度：basic（每5个成功URL消耗1积分）或 advanced（每5个成功URL消耗2积分），默认 basic
TAVILY_EXTRACT_DEPTH = os.getenv("TAVILY_EXTRACT_DEPTH", "basic")
# 每次搜索返回的最大结果数（0-20），默认 5
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "5"))


# ==================== 目录配置 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== Workspace 统一目录 ====================
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
