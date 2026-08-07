# OmniAgent 项目知识库

## 项目简介

OmniAgent 是一个智能桌面助手应用，三层架构：Python FastAPI 后端 + Vue 3 前端 + LangGraph AI Agent。用户可以通过自然语言与 Agent 对话，Agent 能够检索本地知识库、读写文件、执行代码、搜索网络等。

项目口号：**让 AI 住进你的电脑**。

## 技术栈

### 后端
- Python 3.11+
- FastAPI + uvicorn
- LangChain + LangGraph
- Chroma 向量数据库
- DashScope / OpenAI Embedding

### 前端
- Vue 3 + TypeScript
- Vite 构建工具
- Element Plus UI 组件库
- Markdown 渲染

### 桌面打包
- Electron
- PyInstaller（Python 后端打包为 exe）
- electron-builder（NSIS 安装包）

## 编码规范

### Python 规范
所有 Python 代码必须遵循 PEP8 规范：
- 函数命名：snake_case（如 `build_vector_store`）
- 类命名：PascalCase（如 `UserMemoryStore`）
- 常量命名：UPPER_SNAKE_CASE（如 `RAG_TOP_K`）
- 缩进：4 个空格，禁止 Tab
- 每行不超过 100 字符
- 类型注解：所有公开函数必须有类型注解

### TypeScript 规范
- 使用 ESLint + Prettier 统一代码风格
- 组件命名：PascalCase（如 `ChatPanel.vue`）
- 组合式 API（Composition API）优先
- 所有 API 调用封装在 `src/api/` 目录下

## 架构设计

### 三层架构
```
┌─────────────┐
│   前端 Vue 3 │  用户界面，对话交互
├─────────────┤
│  Electron   │  桌面外壳，窗口管理
├─────────────┤
│  后端 FastAPI│  HTTP API，静态文件托管
├─────────────┤
│  Agent Core │  LangGraph 智能体引擎
├─────────────┤
│  数据层     │  Chroma 向量库 + SQLite
└─────────────┘
```

### Agent 工作流
1. 用户输入消息 → 后端 `/api/chat` 接口
2. LangGraph Agent 接收消息，分析意图
3. 根据需要调用工具（知识库检索、记忆检索、文件操作等）
4. 流式返回回答 → 前端打字机效果展示

## 知识库使用说明

### 支持的文件格式
- `.txt`：纯文本，按行分块
- `.md`：Markdown，按标题分段

### 检索原理
知识库使用**向量检索**（语义搜索），不是关键词匹配。这意味着：
- "项目用了什么技术" 可以匹配到 "技术栈" 章节
- "怎么打包" 可以匹配到 "桌面打包" 章节
- 不需要精确的词语匹配，AI 能理解语义

### 最佳实践
1. 使用清晰的标题层级（# ## ###）
2. 每个段落尽量独立、完整
3. 避免超大文件，建议单文件不超过 5000 行
4. 修改文件后自动重建索引，无需手动操作

## 部署指南

### 开发环境启动
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端
python main.py

# 启动前端开发服务器
cd frontend && npm run dev

# 一键启动（含 Electron）
npm run dev:all
```

### 生产环境打包
```bash
# 完整构建流程
npm run dist

# 构建产物位置
# desktop/dist/OmniAgent Setup x.x.x.exe
```

### 环境变量配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| LLM_BASE_URL | 大模型 API 地址 | 无 |
| LLM_API_KEY | 大模型 API 密钥 | 无 |
| LLM_MODEL | 大模型名称 | 无 |
| EMBEDDING_BASE_URL | Embedding 服务地址 | DashScope |
| EMBEDDING_API_KEY | Embedding API 密钥 | 无 |
| AMAP_API_KEY | 高德地图 API 密钥 | 无 |

## 常见问题 FAQ

### Q: 知识库和记忆库有什么区别？
知识库：存储文档类知识（项目文档、技术方案、笔记等），由用户主动上传管理。
记忆库：存储用户个人信息（偏好、习惯、身份等），由 Agent 对话中自动收集。

### Q: 为什么检索结果不准确？
可能原因：文档内容过少、Embedding 模型不合适、检索数量（Top-K）太小。建议增加文档量或调大 Top-K。

### Q: 如何备份数据？
所有用户数据存储在 `%APPDATA%/OmniAgent/workspace/` 目录下，直接复制该目录即可备份。包括知识库、记忆、对话记录、日志等。

### Q: 如何切换大模型？
在设置页面修改 LLM_BASE_URL、LLM_API_KEY 和 LLM_MODEL，保存后即时生效。支持所有 OpenAI 兼容接口的模型（如 DeepSeek、通义千问、GLM 等）。

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-07 | 初始版本，基础对话 + 知识库 |
| v1.1 | 2026-08 | 新增长期记忆、文件操作、代码执行 |
| v1.2 | 2026-08 | 新增联网搜索、天气查询、桌面打包 |

## 团队联系

- 项目地址：192.168.3.254:9080 (内部 Git)
- 主要分支：develop（开发）、master（稳定）
- 技术栈偏好：Python + Vue + Electron
