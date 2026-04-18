# OmniAgent

基于 LangChain 1.0 的多任务智能代理框架。

## 功能特性

- 多工具集成（天气、时间、知识库）
- 对话式界面
- 知识库管理

## 安装

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv pip install -e .
```

## 使用方法

```bash
uv run python main.py
```

## 依赖

- langchain>=1.0.0
- langchain-openai
- langchain-chroma
- langchain-community
- chromadb
- dashscope
- python-dotenv
- streamlit
- requests
- pypinyin
- langgraph

## 项目结构

- `agent/` - 代理执行器和核心逻辑
- `rag/` - 检索增强生成（RAG）功能
- `tools/` - 各种工具（天气、时间等）
- `config/` - 配置文件
- `prompts/` - 提示模板
- `knowledge/` - 知识库文件
- `web/` - Streamlit Web 界面
- `main.py` - 命令行入口点
