# OmniAgent - 个人智能助手系统

基于 LangChain 1.0 + LangGraph 的全栈智能助手，具备流式对话、自动工具调用、RAG 知识检索、多轮记忆、会话管理等能力。

---

## ✨ 功能清单

| 功能          | 描述                                            |
| :------------ | :---------------------------------------------- |
| 🏗️ 全栈架构   | Vue3 + FastAPI + LangChain Agent 核心           |
| 💬 流式打字机 | 逐字显示，50ms/字，打字机效果                   |
| ⏸️ 暂停/中止  | 前后端协同，随时中断 Agent 回复                 |
| 🧠 多轮记忆   | AsyncSqliteSaver + 前端 localStorage 双层持久化 |
| 📚 RAG 知识库 | Chroma + DashScope Embedding + MMR 多样性检索   |
| 🌤️ 天气查询   | 高德 API，600s 缓存，支持 3202 个城市           |
| 🕐 时间查询   | 实时获取当前日期时间                            |
| 📝 编辑消息   | 截断对话 + 新 thread_id + 重塑上下文            |
| 💬 会话管理   | 新建/切换/清空，侧边栏管理                      |
| 📜 长对话压缩 | SummarizationMiddleware，100条触发，保留10条    |
| 📊 统一日志   | 控制台 + 文件，按大小滚动，UTF-8 编码           |

---

## 🏛️ 架构设计

```text
前端 (Vue3 + TypeScript + Element Plus)
  ├── composables/（useChatMessages / useMessageEdit / useSessionManager）
  ├── components/（ChatContainer / MessageList / MessageItem / ChatInput / Sidebar）
  └── utils/storage.ts（统一 localStorage）
        │
        ▼ HTTP (SSE 流式)
后端 (FastAPI)
  ├── routers/chat.py（/api/chat/stream，SSE 流式，带断连检测）
  ├── services/agent_service.py（薄层转发）
  └── schemas/chat.py（Pydantic 模型）
        │
        ▼
Agent 核心层 (LangChain 1.0 + LangGraph)
  ├── executor.py（Agent 创建、同步/异步调用、流式输出）
  ├── model_factory.py（模型工厂，主模型 qwen-max，总结模型 qwen3.6-plus）
  ├── checkpointer.py（AsyncSqliteSaver，对话状态持久化）
  ├── middleware.py（SummarizationMiddleware，长对话压缩）
  ├── config.py（SYSTEM_PROMPT）
  └── tools/（get_current_time / identify_user / get_weather）
        │
        ▼
RAG 模块
  ├── retriever.py（MMR 检索，向量存储缓存）
  ├── builder.py（文档加载、MD5 增量构建）
  └── knowledge/my_knowledge.txt（知识文档）
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js ^20.19.0 || >=22.12.0
- SQLite 3

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd OmniAgent
```

### 2. 后端配置

```bash
# 方式 1：使用 uv 包管理器（推荐，最快）
uv sync  # 自动安装 pyproject.toml 中定义的所有依赖

# 方式 2：使用 pip
# pip install -r requirements.txt

# 配置环境变量
# Windows (PowerShell):
Copy-Item .env.example -Destination .env

# Linux/Mac:
# cp .env.example .env

# 编辑 .env，填入 API Key：
# DASHSCOPE_API_KEY=your_key    (必选，通义千问 API Key)
# OPENAI_API_KEY=your_key       (可选，OpenAI 兼容 API)
# AMAP_API_KEY=your_key         (可选，高德地图 API Key)
```

**获取 API Key：**

- DASHSCOPE_API_KEY: [阿里云百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home)
- AMAP_API_KEY: [高德开放平台](https://lbs.amap.com/)

### 3. 构建知识库

```bash
# 方式 1：直接运行（推荐）
python -c "from agent_core.rag.builder import build_vector_store; build_vector_store()"

# 方式 2：如果 PYTHONPATH 设置正确
python -m agent_core.rag.builder
```

### 4. 启动后端

```bash
# 方式 1：从 backend 目录启动（推荐）
cd backend
uvicorn main:app --reload --port 8000

# 方式 2：使用命令行版本（可选）
# python main.py
```

### 5. 前端配置

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 开始使用。

---

## 📁 项目结构

```text
OmniAgent/
├── agent_core/                  # Agent 核心
│   ├── agent/
│   │   ├── executor.py          # Agent 执行器（同步/异步/流式）
│   │   ├── model_factory.py     # 模型工厂
│   │   ├── checkpointer.py      # 对话持久化
│   │   ├── middleware.py         # 中间件配置
│   │   └── config.py            # 系统提示词
│   ├── tools/
│   │   ├── rag_tool.py          # 身份鉴定工具（identify_user）
│   │   ├── time_tool.py         # 时间工具
│   │   └── weather_tool.py      # 天气工具（高德 API + 缓存）
│   ├── rag/
│   │   ├── retriever.py         # MMR 检索
│   │   └── builder.py           # 向量库构建（MD5 增量）
│   ├── config/
│   │   ├── settings.py          # 全局配置（模型、路径、API Key）
│   │   └── prompt_loader.py     # 提示词加载
│   ├── logger/
│   │   └── setup.py             # 日志配置
│   ├── prompts/
│   │   └── system.txt           # Prompt 模板
│   ├── resources/               # 资源文件
│   │   ├── city_codes.json      # 城市编码
│   │   └── AMap_adcode_citycode.xlsx
│   ├── scripts/                 # 工具脚本
│   ├── tests/                   # 测试模块
│   └── knowledge/               # 知识文档
│       └── my_knowledge.txt
├── backend/                     # FastAPI 后端
│   ├── routers/chat.py          # 路由（SSE 流式端点）
│   ├── services/agent_service.py # 服务层
│   ├── schemas/chat.py          # Pydantic 模型
│   └── main.py                  # 应用入口
├── frontend/                    # Vue3 前端
│   └── src/
│       ├── composables/         # 状态管理
│       ├── components/          # UI 组件
│       ├── api/chat.ts          # API 层（fetch + SSE）
│       ├── types/chat.ts        # 类型定义
│       ├── router/              # 路由
│       └── utils/storage.ts     # localStorage 工具
├── chroma_db/                   # 向量库数据
├── logs/                        # 日志文件
├── main.py                      # 命令行入口
├── pyproject.toml               # uv 项目配置
└── requirements.txt             # Python 依赖
```

---

## 🔧 核心功能详解

### 流式输出（打字机效果）

**数据流：**

```text
Agent 生成 token → astream 推送 → 前端 fetch ReadableStream
→ 逐字拆入打字机队列 → 50ms/字追加到消息气泡
```

**关键实现（executor.py）：**

```python
async def stream_agent(user_input, thread_id):
    agent = await get_async_agent_executor()
    config = RunnableConfig(configurable={"thread_id": thread_id})

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        stream_mode="messages"
    ):
        token, metadata = chunk  # astream 返回元组！
        if token.content:
            yield token.content
```

**核心踩坑：**

- `astream()` 返回 `(AIMessageChunk, dict)` 元组，不是对象
- `SummarizationMiddleware` 产生的内部 token 会混入流式输出，需通过 `metadata["langgraph_node"]` 和关键词过滤

### 模型配置

- **主模型**：`qwen3-vl-32b-thinking`（通义千问大模型）
- **总结模型**：`qwen3.6-plus`（用于 SummarizationMiddleware）
- **嵌入模型**：`text-embedding-v3`（DashScope 文本嵌入）

### RAG 检索优化（MMR）

**问题：** 问"我叫什么名字"时，普通相似度检索第一条返回的是性格描述而非名字。

**解决方案：** 使用 MMR（最大边际相关性）检索，强制引入不同主题的文档。

**实现：**

- `retrieve_docs()` 使用 MMR 检索（用于 identify_user 工具）
- `retrieve()` 使用普通相似度搜索（备用）

**核心公式：** `最终分数 = λ × 相关性 - (1-λ) × 与已选文档的相似度`

### 暂停/中止生成

前端 `AbortController` 切断连接 → 后端 `http.disconnect` 监听 → `asyncio.Task.cancel()` → Agent 捕获 `CancelledError` 优雅中止。

**重要发现：** 无需手动清理 SQLite 检查点，LangGraph 内部会自动处理中断状态。

### 编辑消息与上下文重塑

纯前端操作，后端毫不知情：

1. 找到被编辑消息的索引
2. `splice()` 截断之后的所有对话
3. 生成全新 `thread_id`
4. 迁移干净历史到新 ID 的 localStorage
5. 新 ID 在 SQLite 中无检查点，Agent 从零开始但保留截断前的完整历史

---

## 🐛 踩坑记录

### "双重回复"Bug（核心问题）

**现象：** RAG 问题出现两段回复——"冷档案"+"暖人设"。

**排查时间线（11个阶段）：**

| 阶段 | 尝试方案                         | 结果 |
| :--- | :------------------------------- | :--- |
| 1    | 关键词过滤器                     | ✗    |
| 2    | langgraph_node 节点名过滤        | ✗    |
| 3    | 过滤 tool_calls 和 ToolMessage   | ✗    |
| 4    | SummarizationMiddleware 禁用流式 | ✗    |
| 5    | 移除 SummarizationMiddleware     | ✗    |
| 6    | 修改 System Prompt               | ✗    |
| 7    | 修改 rag_tool 描述、rag.txt      | ✗    |
| 8    | 移除 chain.py 的 print           | ✗    |
| 9    | stream_mode="updates"            | ✗    |
| 10   | 模型 tags 过滤                   | ✗    |
| 11   | 改造 rag_tool.py，拆除内部 LLM   | ✅   |

**病根：** LangGraph 的 `astream` 在 `stream_mode="messages"` 模式下，会无差别拦截图中所有 LLM 调用产生的 token——包括工具内部嵌套的 LLM 调用。

**最终方案：**

```python
# 之前（触发双重回复）
from agent_core.rag.chain import run_rag_chain
result = run_rag_chain(question)  # 内部有 LLM 调用

# 之后（干净利落）
from agent_core.rag.retriever import retrieve_docs
docs = retrieve_docs(question)
return "\n\n".join(docs)  # 只返回原文，无 LLM 调用
```

### "对话记忆 vs 知识库"边界混淆

**现象：** Agent 面对"我刚才说了啥"等对话历史问题时，间歇性误调用 RAG 工具。

**核心方法论：**

> 当 LLM 在模糊边界上反复出错时，不断追加"不要做X"的软约束是低效的。最有效的方法是重新设计工具的边界，让它在根本不可能被误触发。

**最终方案：** 将工具重命名为 `identify_user`，职责窄化为仅回答"我是谁"：

```python
def identify_user(question: str) -> str:
    """仅在用户明确询问其基本身份信息时调用。
    调用示例：
    - "我是谁呀" → 调用
    - "我刚才说了啥" → 不要调用
    - "我都问过你啥" → 不要调用
    """
```

---

## 📦 依赖

### 后端

- langchain >= 1.0
- langgraph
- langchain-openai
- langchain-chroma
- langchain-community
- langgraph-checkpoint-sqlite
- fastapi
- uvicorn
- dashscope

### 前端

- Vue 3
- TypeScript
- Element Plus
- Pinia
- Axios
- Vue Router

---

## ❓ FAQ 常见问题

### Q1: DASHSCOPE_API_KEY 在哪里获取？

A: 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home)，注册账号后在「API-KEY」中创建。

### Q2: 如何添加自己的知识库？

A:

1. 将知识文档（.txt、.md 等）放入 `agent_core/knowledge/` 目录
2. 运行知识库构建命令

```bash
python -c "from agent_core.rag.builder import build_vector_store; build_vector_store()"
```

3. 重启后端即可生效

### Q3: 如何更换主模型？

A: 修改 `agent_core/agent/model_factory.py` 中的 `MAIN_MODEL` 常量。支持所有通义千问模型。

### Q4: 前端和后端连接失败怎么办？

A:

1. 确认后端是否在 8000 端口运行
2. 检查前端 `frontend/src/api/chat.ts` 中的 `BASE_URL` 是否正确
3. 检查浏览器控制台是否有 CORS 错误

### Q5: 对话历史存在哪里？

A: 双重持久化：

- 后端：SQLite 数据库 `agent_core/data/agent_checkpoints.db`
- 前端：浏览器 localStorage

---

## 🚀 部署指南

### 本地 Docker 部署（最简单）

如果你已经安装好 Docker，按照以下步骤操作：

#### 1. 配置环境变量

确保你有 `.env` 文件（如果没有，从 `.env.example` 复制）：

```bash
# Windows (PowerShell):
Copy-Item .env.example -Destination .env

# Linux/Mac:
# cp .env.example .env
```

编辑 `.env`，填入你的 API Key。

#### 2. 构建并启动（一键启动！）

```bash
# 在项目根目录执行
docker-compose up --build
```

#### 3. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000

#### 4. 停止服务

```bash
docker-compose down

# 停止并删除数据卷（慎用！会删除对话历史）
# docker-compose down -v
```

---

### Docker 部署（单独部署后端）

如果只需要部署后端：

```bash
# 构建镜像
docker build -t omniagent-backend -f Dockerfile.backend .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY=your_key \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/agent_core/data:/app/agent_core/data \
  omniagent-backend
```

---

### 前端部署

```bash
cd frontend
npm run build
# 将 dist 目录部署到 Nginx、Vercel、Netlify 等
```

### Docker 配置说明

| 文件                           | 作用                |
| ------------------------------ | ------------------- |
| `docker-compose.yml`           | 一键编排前后端      |
| `Dockerfile.backend`           | 后端镜像构建文件    |
| `frontend/Dockerfile.frontend` | 前端镜像构建文件    |
| `frontend/nginx.conf`          | Nginx 反向代理配置  |
| `.dockerignore`                | Docker 构建忽略列表 |

### 完全清理 Docker 资源

如果你想完全删除与项目相关的所有 Docker 资源（包括镜像、容器、网络等）：

```powershell
# 1. 停止并删除容器和网络（保留数据）
docker-compose down

# 2. （可选）如果你想删除所有数据（对话历史、知识库等）
docker-compose down -v

# 3. 删除项目相关的 Docker 镜像
# 先查看所有镜像
docker images

# 删除前端和后端镜像
docker rmi omniagent-frontend
docker rmi omniagent-backend

# 4. （可选）深度清理所有未使用的 Docker 资源
# 警告：这会删除所有未使用的镜像、容器、网络！
docker system prune -a
```

### Docker 命令快速参考

| 命令                            | 说明                             |
| ------------------------------- | -------------------------------- |
| `docker-compose up`             | 启动服务（如果镜像不存在会构建） |
| `docker-compose up --build`     | 重新构建并启动服务               |
| `docker-compose down`           | 停止并删除容器和网络             |
| `docker-compose down -v`        | 停止并删除容器、网络和数据卷     |
| `docker-compose logs`           | 查看所有服务日志                 |
| `docker-compose logs --tail=50` | 查看最后 50 行日志               |
| `docker-compose logs -f`        | 实时跟踪日志                     |

---

## ⚙️ 扩展指南

### 1. 添加新工具

在 `agent_core/tools/` 目录下创建新文件，例如 `calculator_tool.py`：

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """简单的计算器工具，计算数学表达式。
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
    """
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {str(e)}"
```

然后在 `agent_core/agent/executor.py` 的 `TOOLS` 列表中引入并添加。

### 2. 添加新知识库格式

修改 `agent_core/rag/builder.py` 中的 `load_documents()` 函数，添加新的文档加载器。

### 3. 自定义系统提示词

编辑 `agent_core/prompts/system.txt`，修改后无需重启，会自动加载。

---

## 🤝 贡献指南

欢迎贡献代码、报告 Issue 或提出建议！

### 提交 Pull Request

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 后端：遵循 PEP 8
- 前端：遵循 ESLint 规范
- 提交信息：使用中文或英文描述清楚变更内容

---

## 📝 许可证

MIT
