# 配置管理模块
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


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
_missing_llm = [
    name for name, value in (
        ("LLM_BASE_URL", LLM_BASE_URL),
        ("LLM_API_KEY", LLM_API_KEY),
        ("LLM_MODEL", LLM_MODEL),
    ) if not value
]
if _missing_llm:
    raise ValueError(
        f".env 中缺少必需的 LLM 配置项: {', '.join(_missing_llm)}。"
        f"请参考 .env.example 中的示例填写。"
    )


# ==================== Embedding 配置 ====================
# Embedding 完全独立配置，可与 LLM 使用不同平台。
# 例如：LLM 用 DeepSeek（不支持 Embedding），Embedding 用阿里云百炼。

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
# 向量维度（可选，部分模型如 text-embedding-v3/v4 支持自定义）
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

# Embedding 必填项校验
_missing_emb = [
    name for name, value in (
        ("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL),
        ("EMBEDDING_API_KEY", EMBEDDING_API_KEY),
        ("EMBEDDING_MODEL", EMBEDDING_MODEL),
    ) if not value
]
if _missing_emb:
    raise ValueError(
        f".env 中缺少必需的 Embedding 配置项: {', '.join(_missing_emb)}。"
        f"请参考 .env.example 中的示例填写。"
    )


# ==================== 工具配置 ====================
AMAP_API_KEY = os.getenv("AMAP_API_KEY")


# ==================== 目录配置 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "agent_core", "knowledge")

# ==================== RAG 配置 ====================
RAG_TOP_K = 3
