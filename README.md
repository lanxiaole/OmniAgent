# OmniAgent - 个人智能助手系统

基于 LangChain 1.0 + LangGraph 的全栈智能助手，具备流式对话、自动工具调用、RAG 知识检索、多轮记忆、会话管理、代码执行、联网搜索等能力。

---

## 🎨 界面预览

![77770985824](assets/1777709858241.png)

---

## ✨ 功能清单

| 功能 | 描述 |
| :--- | :--- |
| 🏗️ 全栈架构 | Vue3 + FastAPI + LangChain Agent 核心 |
| 💬 流式打字机 | 逐字显示，50ms/字，打字机效果 |
| ⏸️ 暂停/中止 | 前后端协同，随时中断 Agent 回复 |
| 🧠 多轮记忆 | AsyncSqliteSaver + 前端 localStorage 双层持久化 |
| 📚 RAG 知识库 | Chroma + OpenAI 兼容 Embedding + MMR 多样性检索 |
| 🧾 长期记忆 | 基于向量检索的"用户记忆"模块，自动覆盖相似内容 |
| 🌐 联网搜索 | Tavily 官方 SDK，搜索结果 7 天缓存，积分优化 |
| 📄 网页阅读 | Tavily 抽取网页内容，30 天缓存 |
| 🐍 代码执行 | 安全沙箱执行 Python，含危险调用黑名单 + 物理重试锁定 |
| 📁 文件操作 | 读写文件、列目录、搜索文件，支持 `~` 用户目录展开 |
| 🌤️ 天气查询 | 高德 API，600s 缓存，支持 3202 个城市/地区 |
| 🕐 时间查询 | 实时获取当前日期时间 |
| 📝 编辑消息 | 截断对话 + 新 thread_id + 重塑上下文 |
| 💬 会话管理 | 新建/切换/清空，侧边栏管理 |
| 📜 长对话压缩 | SummarizationMiddleware，长对话自动压缩 |
| 📊 统一日志 | 控制台 + 文件，按大小滚动，UTF-8 编码 |
| 🛡️ Harness 工程 | 物理堵死危险操作、缓存防重、内容清洗、智能参数推断 |

---

## ✨ 功能演示



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
  ├── factory.py（Agent 工厂，支持依赖注入、可测试性）
  ├── executor.py（同步/异步调用 + 流式输出 + 内部 token 过滤）
  ├── model_factory.py（模型工厂：get_llm_model + get_summarizer_model）
  ├── checkpointer.py（AsyncSqliteSaver，对话状态持久化）
  ├── middleware.py（SummarizationMiddleware：100 条触发，保留 10 条）
  ├── config.py（SYSTEM_PROMPT，从 prompts/system.txt 加载）
  └── tools/
        ├── time_tool.py            # 时间查询
        ├── weather_tool.py         # 天气查询（高德 API + 10 分钟缓存）
        ├── rag_tool.py             # 知识库检索（search_personal_knowledge）
        ├── memory_tool.py          # 长期记忆（save/recall/list/delete/clear）
        ├── file_tool.py            # 文件读写、目录浏览（~ 展开 + 系统目录保护）
        ├── executor_tool.py        # Python 代码执行（物理重试锁定 + 黑名单）
        └── search_tool.py          # 联网搜索 + 网页阅读（Tavily）
        │
        ├─→ RAG 模块
        │    ├── retriever.py（MMR 检索，k=3，向量存储缓存）
        │    ├── builder.py（文档加载、MD5 增量构建）
        │    ├── loaders.py（多格式文档加载）
        │    └── config.py（RAG 配置）
        │
        ├─→ Memory 模块（长期记忆）
        │    └── memory_manager.py（用户记忆向量存储，独立集合 user_memory）
        │
        ├─→ Search 模块（联网搜索）
        │    ├── tavily_engine.py（TavilyClient 封装，积分监控 + 智能降级）
        │    └── cache.py（搜索/网页内容两层缓存）
        │
        └─→ 基础设施
             ├── config/settings.py   # 全局配置（模型、路径、API Key）
             ├── config/prompt_loader.py  # 提示词加载
             ├── logger/setup.py     # 会话日志初始化
             ├── errors.py           # 统一异常分类（OpenAI / httpx / 业务）
             └── executor/python_executor.py  # 代码执行引擎
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
# 方式 1：使用 uv 包管理器（推荐，稳定，启动脚本也使用uv环境）
uv sync  # 自动安装 pyproject.toml 中定义的所有依赖，同时创建 .venv 虚拟环境
#请注意先确定电脑中有uv，否则会报错。若没有，请下载：
pip install uv
# 方式 2：使用 pip
# pip install -r requirements.txt
```

### 3. 检验 uv 虚拟环境

`uv sync` 会自动在项目根目录创建 `.venv` 虚拟环境。使用项目前，请确保激活正确的环境：

```bash
# Windows (PowerShell)：激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 激活后，命令行提示符会显示 (omniagent) 前缀，表示已进入项目环境

# 验证当前环境（可选）
python --version  # 应显示 .venv 中的 Python 版本
where python      # 应指向 .venv\Scripts\python.exe

# 使用环境中的命令（在项目根目录执行）
uvicorn backend.main:app --reload --port 8000  # 启动后端

# 退出虚拟环境（可选）
deactivate
```

**常见问题：**

- **PowerShell 执行策略限制：** 如果激活脚本无法运行，执行以下命令：
  ```powershell
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  然后重新打开 PowerShell。

- **如何确认当前环境？** 激活后命令行提示符会显示 `(omniagent)` 前缀。

  ### 4.配置环境变量

```bash
# 配置环境变量
# Windows (PowerShell):
Copy-Item .env.example -Destination .env

# Linux/Mac:
# cp .env.example .env
```

编辑 `.env`，填入 API Key。配置方式完全遵循 OpenAI SDK 的字段命名：

| 配置项 | 说明 | 必填 |
| :-- | :-- | :-- |
| `LLM_BASE_URL` | LLM 接口地址 | 是 |
| `LLM_API_KEY` | LLM API Key | 是 |
| `LLM_MODEL` | LLM 模型名 | 是 |
| `LLM_SUMMARIZER_MODEL` | 总结模型（用于压缩历史消息），不填则与 LLM_MODEL 相同 | 否 |
| `LLM_TEMPERATURE` | LLM 采样温度，默认 0.7 | 否 |
| `EMBEDDING_BASE_URL` | Embedding 接口地址 | 是 |
| `EMBEDDING_API_KEY` | Embedding API Key | 是 |
| `EMBEDDING_MODEL` | Embedding 模型名 | 是 |
| `EMBEDDING_DIMENSIONS` | 向量维度，默认 1024（text-embedding-v3/v4 支持自定义） | 否 |
| `AMAP_API_KEY` | 高德地图 API Key（天气查询） | 否 |
| `TAVILY_API_KEY` | Tavily API Key（联网搜索） | 否 |
| `TAVILY_SEARCH_DEPTH` | 搜索深度 basic/advanced，默认 basic | 否 |
| `TAVILY_EXTRACT_DEPTH` | 提取深度 basic/advanced，默认 basic | 否 |
| `TAVILY_MAX_RESULTS` | 每次搜索返回的最大结果数，默认 5 | 否 |
| `EXECUTION_TIMEOUT` | 代码执行超时（秒），默认 30 | 否 |
| `EXECUTION_MAX_RETRIES` | 代码执行最大重试次数，默认 3 | 否 |
| `EXECUTION_WORK_DIR` | 代码执行工作目录，默认 temp_exec | 否 |
| `SYSTEM_DIRS` | 系统目录黑名单（逗号分隔），用于路径安全警告 | 否 |

**常用平台配置参考：**

| 平台 | LLM_BASE_URL | EMBEDDING_BASE_URL |
| :-- | :-- | :-- |
| 阿里云百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| DeepSeek | `https://api.deepseek.com` | 不提供，需单独配置 Embedding 平台 |
| OpenAI | `https://api.openai.com/v1` | `https://api.openai.com/v1` |

> DeepSeek 不提供 Embedding API，推荐 LLM 用 DeepSeek，Embedding 用阿里云百炼。

**获取 API Key：**

- 阿里云百炼: [阿里云百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home)
- DeepSeek: [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
- OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)
- 高德地图: [高德开放平台](https://lbs.amap.com/)（每月免费学习额度）
- Tavily: [Tavily 控制台](https://app.tavily.com/)（每月 1000 免费积分）

### 4. 构建知识库

```bash
# 方式 1：直接运行（推荐）
python -c "from agent_core.rag.builder import build_vector_store; build_vector_store()"

# 方式 2：如果 PYTHONPATH 设置正确
python -m agent_core.rag.builder
```

### 5. 一键启动（推荐）

项目提供了启动脚本，自动启动前后端服务：

```bash
# Windows (PowerShell)
.\start.ps1

# Windows (CMD)
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

启动脚本会自动：
- 检测并清理 8000 / 5173 端口上的残留进程（避免端口冲突）
- 启动后端服务（http://localhost:8000）
- 启动前端开发服务器（http://localhost:5173）

### 6. 手动启动（可选）

```bash
# 后端（从项目根目录）
uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 开始使用。

### 7. 命令行模式（可选）

如果不想启动 Web 界面，可以直接用命令行与 Agent 对话：

```bash
# 在项目根目录执行
python main.py
```

进入交互式 REPL，输入内容即可与 Agent 对话，输入 `quit` / `exit` / `q` 退出。

---

## 📁 项目结构

```text
OmniAgent/
├── agent_core/                      # Agent 核心
│   ├── agent/                       # Agent 层
│   │   ├── factory.py               # Agent 工厂（支持依赖注入、可测试性）
│   │   ├── executor.py              # 执行器（同步/异步/流式）
│   │   ├── model_factory.py         # 模型工厂
│   │   ├── checkpointer.py          # 对话持久化
│   │   ├── middleware.py            # 中间件配置
│   │   └── config.py                # 系统提示词
│   ├── tools/                       # Agent 工具
│   │   ├── time_tool.py             # 时间工具
│   │   ├── weather_tool.py          # 天气工具（高德 API + 缓存）
│   │   ├── rag_tool.py              # 知识库检索
│   │   ├── memory_tool.py           # 长期记忆（5 个工具）
│   │   ├── file_tool.py             # 文件操作（read/write/list/search）
│   │   ├── executor_tool.py         # Python 代码执行（带重试锁定）
│   │   └── search_tool.py           # 联网搜索 + 网页阅读
│   ├── executor/                    # 代码执行引擎
│   │   └── python_executor.py       # 独立子进程 + 危险调用黑名单
│   ├── rag/                         # RAG 模块
│   │   ├── retriever.py             # MMR 检索
│   │   ├── builder.py               # 向量库构建（MD5 增量）
│   │   ├── loaders.py               # 多格式文档加载
│   │   └── config.py                # RAG 配置
│   ├── memory/                      # 长期记忆模块
│   │   └── memory_manager.py        # 用户记忆向量存储
│   ├── search/                      # 联网搜索模块
│   │   ├── tavily_engine.py         # Tavily 引擎封装
│   │   └── cache.py                 # 搜索/网页内容缓存
│   ├── config/                      # 配置
│   │   ├── settings.py              # 全局配置（模型、路径、API Key）
│   │   └── prompt_loader.py         # 提示词加载
│   ├── logger/                      # 日志
│   │   └── setup.py                 # 日志配置
│   ├── prompts/
│   │   └── system.txt               # Prompt 模板
│   ├── resources/                   # 资源文件
│   │   ├── city_codes.json          # 城市编码
│   │   └── AMap_adcode_citycode.xlsx
│   ├── scripts/                     # 工具脚本
│   ├── tests/                       # 测试模块
│   ├── knowledge/                   # 知识文档
│   │   └── my_knowledge.txt
│    ── errors.py                    # 统一异常分类
├── backend/                         # FastAPI 后端
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py                  # 路由（SSE 流式端点）
│   ├── services/
│   │   ├── __init__.py
│   │   └── agent_service.py         # 服务层
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat.py                  # Pydantic 模型
│   └── main.py                      # 应用入口
├── frontend/                        # Vue3 前端
│   ├── public/
│   ├── src/
│   │   ├── composables/             # 状态管理
│   │   ├── components/              # UI 组件
│   │   ├── api/chat.ts              # API 层（fetch + SSE）
│   │   ├── types/                   # 类型定义
│   │   ├── router/                  # 路由
│   │   ├── utils/storage.ts         # localStorage 工具
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── docker/                          # Docker 部署
│   ├── backend/Dockerfile
│   ├── frontend/Dockerfile
│   ├── frontend/nginx.conf
│   └── .dockerignore
├── chroma_db/                       # 向量库数据（自动生成）
├── agent_core/data/                 # SQLite 检查点（自动生成）
├── logs/                            # 日志文件（自动生成）
├── temp_exec/                       # 代码执行临时目录（自动生成）
├── web_cache/                       # 联网搜索缓存（自动生成）
│   ├── search/                      #   搜索结果缓存（7 天有效）
│   └── pages/                       #   网页内容缓存（30 天有效）
├── main.py                          # 命令行入口（交互式 REPL）
├── start.ps1 / start.bat / start.sh # 一键启动脚本（带端口清理）
├── pyproject.toml                   # uv 项目配置
├── requirements.txt                 # Python 依赖
├── docker-compose.yml               # Docker 一键编排
├── .env.example                     # 环境变量模板
└── README.md                        # 项目文档
```

---

## 🔧 核心功能详解

### 工具一览（共 15 个）

| 工具名 | 分类 | 用途 |
| :--- | :--- | :--- |
| `get_current_time` | 工具类 | 获取当前日期时间 |
| `search_personal_knowledge` | 知识库 | 检索用户存储在 RAG 中的个人信息 |
| `get_weather` | 工具类 | 查询城市天气（高德 API，10 分钟缓存） |
| `save_user_memory` | 长期记忆 | 保存用户偏好、习惯等（自动覆盖相似内容） |
| `recall_user_memory` | 长期记忆 | 检索长期记忆 |
| `list_user_memories` | 长期记忆 | 列出所有记忆 |
| `delete_user_memory` | 长期记忆 | 删除指定记忆 |
| `clear_user_memories` | 长期记忆 | 清空所有记忆 |
| `read_file` | 文件操作 | 读取文本文件（支持分页，默认前 500 行） |
| `write_file` | 文件操作 | 写入文件（支持 `~` 用户目录展开 + 系统目录保护） |
| `list_directory` | 文件操作 | 浏览目录结构（支持递归、深度控制） |
| `search_files` | 文件操作 | 按通配符搜索文件名（支持分页） |
| `execute_python` | 代码执行 | 安全沙箱执行 Python（物理重试锁定 + 危险调用黑名单） |
| `search_web` | 联网搜索 | Tavily 搜索（7 天缓存，智能推断 topic/time_range） |
| `read_webpage` | 联网搜索 | 提取网页内容（30 天缓存） |

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

所有模型通过 `.env` 环境变量配置，无需修改代码：

| 用途 | 配置项 | 说明 |
| :--- | :--- | :--- |
| **主模型** | `LLM_MODEL` | 在 `.env` 中填写，如 `qwen-plus`、`deepseek-v4-flash` |
| **总结模型** | `LLM_SUMMARIZER_MODEL` | 可选，默认与主模型相同，可单独指定更便宜的模型（温度固定 0.3，更稳定） |
| **采样温度** | `LLM_TEMPERATURE` | 主模型温度，默认 0.7 |
| **嵌入模型** | `EMBEDDING_MODEL` | 在 `.env` 中填写，如 `text-embedding-v3` |

- LLM 和 Embedding 完全独立，可用不同平台
- 项目统一使用 OpenAI 兼容接口（`ChatOpenAI` / `OpenAIEmbeddings`），支持任何 OpenAI SDK 兼容的服务商
- 阿里云百炼（DashScope）会自动切换到 `DashScopeEmbeddings` 客户端以兼容新版模型

### 长对话压缩（SummarizationMiddleware）

当会话历史过长时（默认 100 条消息），`SummarizationMiddleware` 会自动触发压缩，保留最近 10 条消息 + 一段摘要，使用更便宜/更稳的 `LLM_SUMMARIZER_MODEL`（默认与主模型相同，可单独配置）。

- 触发阈值：`trigger=("messages", 100)`
- 保留消息：`keep=("messages", 10)`
- 总结模型温度：0.3（更稳定）

### RAG 检索优化（MMR）

**问题：** 问"我叫什么名字"时，普通相似度检索第一条返回的是性格描述而非名字。

**解决方案：** 使用 MMR（最大边际相关性）检索，强制引入不同主题的文档。

**实现：**

- `retrieve_docs()` 使用 MMR 检索（用于 `search_personal_knowledge` 工具，`k=3`，`fetch_k=20`）
- `retrieve()` 使用普通相似度搜索（备用）

**核心公式：** `最终分数 = λ × 相关性 - (1-λ) × 与已选文档的相似度`

### 支持的文件格式

`read_file` 工具只支持纯文本格式（基于扩展名判断），二进制文件会被拒绝：

| 支持的扩展名 | 类型 |
| :-- | :-- |
| `.txt` `.md` `.csv` `.log` | 文本与日志 |
| `.py` `.js` `.ts` `.jsx` `.tsx` `.go` `.java` `.cpp` `.h` `.sql` | 源代码 |
| `.json` `.yaml` `.yml` `.xml` | 配置与数据 |
| `.html` `.css` | 前端 |

> `list_directory` 与 `search_files` 不做格式过滤，会扫描所有非隐藏文件。

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

## 🛡️ Harness 工程（核心经验）

本项目在多个关键路径上采用 **Harness Engineering** —— 用代码约束替 Agent 做决策，把"我应该这样做"变成"我无法不这样做"。

### 物理堵死：代码执行重试锁定

**问题：** 原版靠 prompt 提示 Agent "最多重试 3 次"，但 Agent 不会遵守，会继续尝试改代码执行，烧钱。

**解决方案：** 在 [`executor_tool.py`](agent_core/tools/executor_tool.py) 中实现物理锁定：

1. 连续失败达到 3 次后，工具进入**物理锁定**状态
2. 锁定状态下，与上次失败代码相似度 ≥ 0.4 的新代码**直接拒绝执行**（不调用 subprocess）
3. 只有**全新任务**（相似度 < 0.4）才会自动解锁
4. 执行成功后失败计数归零

**核心思想：** 不是"告诉 Agent 不要做"，而是"做了也没用"。

### 物理堵死：危险代码黑名单

**问题：** Agent 倾向于用 `requests`/`urllib` 自写爬虫，既烧 token 又不稳定。

**解决方案：** 在 [`python_executor.py`](agent_core/executor/python_executor.py) 中维护黑名单，在子进程启动前拦截：

```python
DANGEROUS_PATTERNS = [
    # 系统命令执行
    r'\bos\.system\s*\(',
    r'\bsubprocess\.run\s*\(',
    r'\beval\s*\(',
    # ... 动态执行、文件危险操作
    # 网络操作（禁止自写爬虫，应使用 search_web / read_webpage 工具）
    r'\brequests\.(get|post|put|delete)\s*\(',
    r'\bimport\s+requests\b',
    r'\bhttpx\.(get|post|put|delete|Client)\s*\(',
    r'\bimport\s+httpx\b',
    r'\baiohttp\.(ClientSession|get|post|request)\s*\(',
    r'\burllib\.request\.urlopen\s*\(',
    # ...
]
```

### 智能参数推断

**问题：** Agent 调用 `search_web` 时不会主动传 `topic="news"` 和 `time_range="day"`，导致搜索结果时间不准。

**解决方案：** 在 [`search_tool.py`](agent_core/tools/search_tool.py) 中根据查询词自动推断：

```python
def _infer_search_params(query: str) -> dict:
    """根据查询内容智能推断 topic 和 time_range"""
    # "今日热点新闻" → topic=news, time_range=day
    # "股票行情"     → topic=finance, time_range=day
    # "Python教程"   → topic=general, time_range=None
```

### 内容安全清洗

**问题：** 阿里云百炼的 LLM API 会对输入做内容安全检测，新闻摘要中某些关键词会触发 `DataInspectionFailed` 400 错误。

**解决方案：** 工具内部自动清洗：

1. 去除 Unicode 控制字符（零宽空格、方向控制符等）
2. 去除不可打印 ASCII 字符
3. 截断过长内容到 500 字符

### 缓存前置

**问题：** Tavily 每月 1000 积分被快速消耗。

**解决方案：** 在 [`cache.py`](agent_core/search/cache.py) 实现两层缓存：

- 搜索结果缓存 7 天
- 网页内容缓存 30 天
- 命中缓存不消耗积分，**完全不发 API 请求**

### 路径自动展开

**问题：** Agent 传 `~\Desktop\...` 时，`os.path.abspath()` 不会展开 `~`，导致写入到项目根目录 `项目根目录\~\Desktop\...`。

**解决方案：** 在 [`file_tool.py`](agent_core/tools/file_tool.py) 的 `_safe_path()` 中加 `os.path.expanduser()`：

```python
expanded = os.path.expanduser(path)
abs_path = os.path.abspath(expanded)
```

### 友好的错误提示

**问题：** Agent 看到模糊的"请求参数错误 (400)"不知道发生了什么。

**解决方案：** 在 [`errors.py`](agent_core/errors.py) 中识别 `DataInspectionFailed` 错误码，给出针对性建议：

```
⚠️ 搜索结果中包含的内容触发了 LLM 服务商的内容安全检测，无法继续处理。
建议：1. 尝试使用更具体、更中性的关键词重新搜索
     2. 缩小搜索范围，只关注特定技术/学术话题
```

### 启动脚本端口清理

**问题：** 上次启动残留的进程占用 8000 / 5173 端口，新启动直接失败报"Address already in use"。

**解决方案：** 在 [`start.ps1`](start.ps1) / [`start.bat`](start.bat) / [`start.sh`](start.sh) 中，**启动前**先用 `netstat` / `lsof` 扫描端口并 `taskkill` / `kill -9` 杀掉残留进程。

**核心代码（start.ps1 摘录）：**

```powershell
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String -Pattern ":$port\s+.*LISTENING" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique

    foreach ($procId in $connections) {
        Stop-Process -Id $procId -Force -ErrorAction Stop
    }
}
```

**核心思想：** 把"启动失败排查"提前到"启动之前就清理掉"。

---

## 🐛 踩坑记录

### "双重回复" Bug（核心问题）

**现象：** RAG 问题出现两段回复——"冷档案"+"暖人设"。

**排查时间线（11个阶段）：**

| 阶段 | 尝试方案 | 结果 |
| :--- | :--- | :--- |
| 1 | 关键词过滤器 | ✗ |
| 2 | langgraph_node 节点名过滤 | ✗ |
| 3 | 过滤 tool_calls 和 ToolMessage | ✗ |
| 4 | SummarizationMiddleware 禁用流式 | ✗ |
| 5 | 移除 SummarizationMiddleware | ✗ |
| 6 | 修改 System Prompt | ✗ |
| 7 | 修改 rag_tool 描述、rag.txt | ✗ |
| 8 | 移除 chain.py 的 print | ✗ |
| 9 | stream_mode="updates" | ✗ |
| 10 | 模型 tags 过滤 | ✗ |
| 11 | 改造 rag_tool.py，拆除内部 LLM | ✅ |

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

**最终方案：** 将工具职责窄化为仅回答"我是谁"的事实性问题：

```python
def search_personal_knowledge(question: str) -> str:
    """检索用户存储在知识库中的个人信息、偏好、项目、经历等。

    调用示例：
    - "我是谁呀" -> 调用
    - "我刚才说了啥" -> 不要调用（这是对话历史问题）
    - "我都问过你啥" -> 不要调用（这是对话历史问题）
    """
```

### Agent 自写爬虫烧 token

**现象：** Agent 倾向用 `requests`/`urllib` 自写爬虫，单次任务消耗数千 token 还不稳定。

**解决思路：** Harness 工程 —— 物理堵死

1. 在危险代码黑名单中拦截 `requests.get`/`urllib.request.urlopen`/`import httpx`/`import aiohttp` 等所有常见网络库
2. system.txt 明确说明"自写爬虫会触发安全拒绝"
3. 同时提供 `search_web` 和 `read_webpage` 工具（带缓存与积分监控）

**效果：** Agent 尝试一次失败后，会自觉切换到专用工具。

### 代码无限重试烧钱

**现象：** Agent 看到错误提示后会"贴心"地继续修改重试，违反 prompt 中"最多 3 次"的约束。

**解决思路：** 物理锁定，相似度判定

```python
# 连续失败 3 次后，新代码与上次失败代码相似度 ≥ 0.4 时
# 直接 return 错误，不调用 subprocess
# 全新任务（相似度 < 0.4）才会解锁
```

**关键洞察：** 约束写在代码里比写在 prompt 里可靠一万倍。

### 联网搜索触发内容安全检测

**现象：** 阿里云百炼 LLM API 报错 `DataInspectionFailed: Input text data may contain inappropriate content`（HTTP 400）。

**根因：** Tavily 返回的新闻摘要中含敏感关键词，作为 tool_result 传给 LLM 时被内容安全检测拦截。

**解决思路：** 三层防护

1. 工具层内容清洗（去除控制字符）+ 截断（500 字符）
2. 智能参数推断（新闻类查询自动加 `topic=news` + `time_range=day`，结果更精准）
3. errors.py 识别 `DataInspectionFailed` 给出友好提示

### `~` 路径未展开

**现象：** Agent 写 `~\Desktop\test.md` 时，文件被写入 `项目根目录\~\Desktop\test.md`，不是真实桌面。

**根因：** `os.path.abspath()` 不会展开 `~` 为用户主目录。

**解决方案：** `_safe_path()` 中加 `os.path.expanduser(path)`。

### 启动残留进程占端口

**现象：** 上次启动的服务没正常关闭，再次启动时 uvicorn 报 `Address already in use`，手动 netstat + taskkill 才能恢复。

**解决方案：** 在 `start.ps1` / `start.bat` / `start.sh` 中加入端口扫描 + 进程清理逻辑，启动前先杀掉占用 8000 / 5173 端口的进程。

### 联网搜索结果时间不准（2025 年内容）

**现象：** 用 `search_web` 搜"今日热点新闻"，返回的却是 2025 年的旧内容。

**根因：** Tavily `topic="general"` 通用搜索时效性不足，Agent 又不会主动传 `time_range` 和 `topic`。

**解决方案：** 在 `search_tool.py` 中加 `_infer_search_params()`，检测到"新闻/热点/今日"等关键词时自动加 `topic="news"` + `time_range="day"`。

---

## 📦 依赖

### 后端

- langchain >= 1.0
- langgraph
- langchain-openai
- langchain-core
- langchain-community
- langchain-chroma
- langgraph-checkpoint-sqlite
- chromadb
- python-dotenv
- fastapi
- uvicorn
- python-multipart
- pydantic
- pydantic-settings
- python-dateutil
- dashscope
- tavily-python
- requests

> 所有依赖通过 `pyproject.toml`（uv 管理）和 `requirements.txt`（pip 兼容）双重声明，新加包请同步更新两个文件。

### 前端

- Vue 3
- TypeScript
- Element Plus
- Pinia
- Axios
- Vue Router

---

## ❓ FAQ 常见问题

### Q1: API Key 在哪里获取？

A:

- 阿里云百炼: [百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home) → API-KEY
- DeepSeek: [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
- OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)
- 高德地图: [高德开放平台](https://lbs.amap.com/)
- Tavily: [Tavily 控制台](https://app.tavily.com/)

### Q2: 如何添加自己的知识库？

A:

1. 将知识文档（.txt、.md 等）放入 `agent_core/knowledge/` 目录
2. 运行知识库构建命令

```bash
python -c "from agent_core.rag.builder import build_vector_store; build_vector_store()"
```

3. 重启后端即可生效

### Q3: 如何更换主模型？

A: 直接修改 `.env` 中的 `LLM_MODEL` 和 `LLM_BASE_URL` 即可，无需修改代码。例如切换到 DeepSeek：

```bash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-key
LLM_MODEL=deepseek-v4-flash
```

### Q4: 前端报 502 / 连接失败怎么办？

A:

1. **确认后端是否在 8000 端口运行**：浏览器访问 http://localhost:8000/ 应返回 JSON
2. **确认启动命令正确**：
   - 从项目根目录启动：`uvicorn backend.main:app --reload --port 8000`
   - 或从 backend 目录启动：`cd backend && python main.py`
3. **检查前端 `frontend/vite.config.ts` 中的代理配置**：默认指向 `http://localhost:8000`
4. **检查浏览器控制台是否有 CORS 错误**：后端 `main.py` 中 `allow_origins` 需包含前端地址

### Q5: 对话历史存在哪里？

A: 双重持久化：

- 后端：SQLite 数据库 `agent_core/data/agent_checkpoints.db`
- 前端：浏览器 localStorage

### Q6: 长期记忆和 RAG 知识库有什么区别？

A:

- **RAG 知识库**（`search_personal_knowledge`）：静态文档，放在 `agent_core/knowledge/`，需要手动构建
- **长期记忆**（`save_user_memory` 等）：Agent 在对话过程中自动保存的"用户偏好/事实"，使用独立的 Chroma 集合 `user_memory`

### Q7: 联网搜索为什么有时返回 2025 年的内容？

A: 这是 Tavily `topic="general"` 通用搜索的时效性限制。本项目已通过 `search_web` 工具的智能参数推断自动处理：

- 检测到 "今日/新闻/热点" 等关键词时，自动加上 `topic="news"` + `time_range="day"`
- 无需 Agent 手动指定参数

### Q8: 为什么搜索新闻时偶发 400 错误？

A: 阿里云百炼的 LLM API 有内容安全检测，新闻摘要中偶发敏感关键词会触发拦截。本项目已通过三层防护处理：

1. 工具层内容清洗 + 截断
2. 友好错误提示（`errors.py` 识别 `DataInspectionFailed`）
3. 建议换更具体的关键词重试

### Q9: 代码执行失败 3 次后还会继续吗？

A: 不会。`execute_python` 工具在连续失败 3 次后进入**物理锁定**状态，相似代码直接拒绝执行。需提交全新任务（相似度 < 0.4）才会自动解锁。

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

- 前端: http://localhost:5173（容器内 Nginx 监听 80 端口，由 `5173:80` 映射暴露）
- 后端 API: http://localhost:8000

> Docker 内部，前端 Nginx 通过 `http://backend:8000` 转发 `/api/` 路径到后端容器（见 `docker/frontend/nginx.conf`），无需在前端代码里再配代理。

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
docker build -t omniagent-backend -f docker/backend/Dockerfile .

# 运行容器（通过 .env 文件注入环境变量）
docker run -d \
  -p 8000:8000 \
  --env-file .env \
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

| 文件 | 作用 |
| ---------------------------- | ------------------- |
| `docker-compose.yml` | 一键编排前后端 |
| `docker/backend/Dockerfile` | 后端镜像构建文件 |
| `docker/frontend/Dockerfile` | 前端镜像构建文件 |
| `docker/frontend/nginx.conf` | Nginx 反向代理配置 |
| `docker/.dockerignore` | Docker 构建忽略列表 |

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

| 命令 | 说明 |
| ------------------------------- | -------------------------------- |
| `docker-compose up` | 启动服务（如果镜像不存在会构建） |
| `docker-compose up --build` | 重新构建并启动服务 |
| `docker-compose down` | 停止并删除容器和网络 |
| `docker-compose down -v` | 停止并删除容器、网络和数据卷 |
| `docker-compose logs` | 查看所有服务日志 |
| `docker-compose logs --tail=50` | 查看最后 50 行日志 |
| `docker-compose logs -f` | 实时跟踪日志 |

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

然后在 `agent_core/tools/__init__.py` 的 `TOOLS` 列表中引入并添加。

### 2. 添加新知识库格式

修改 `agent_core/rag/loaders.py` 中的 `load_documents()` 函数，添加新的文档加载器。

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
