# 配置管理模块
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API Key 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AMAP_API_KEY = os.getenv("AMAP_API_KEY")

# 模型配置
MODEL_NAME = "qwen3-vl-32b-thinking"
# 总结模型配置（用于 SummarizationMiddleware，使用更轻量的模型）
SUMMARIZER_MODEL_NAME = "qwen3.6-plus"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
TEMPERATURE = 0.7

# 目录配置 - 基于项目根目录的绝对路径
# 获取当前文件所在目录的父目录（即项目根目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "agent_core", "knowledge")

# RAG 配置
RAG_TOP_K = 3

# Embedding 模型配置
EMBEDDING_MODEL = "text-embedding-v3"

# 工具配置
