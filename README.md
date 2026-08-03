# OmniAgent - 个人智能助手系统

基于 LangChain 1.0 + LangGraph 的全栈智能助手，具备流式对话、自动工具调用、RAG 知识检索、长期记忆、代码执行、联网搜索、文件管理等能力，提供完整的 Web 管理界面。

---

## 功能清单

| 功能 | 描述 |
| :--- | :--- |
| 全栈架构 | Vue3 + TypeScript + Element Plus + FastAPI + LangChain Agent |
| 流式打字机 | 逐字显示，打字机效果，支持暂停/中止 |
| 多轮对话 | AsyncSqliteSaver 持久化 + 前端 localStorage 双层缓存 |
| RAG 知识库 | Chroma + Embedding + MMR 多样性检索，支持 Web 端管理 |
| 长期记忆 | 基于向量检索的用户记忆模块，自动覆盖相似内容 |
| 联网搜索 | Tavily 官方 SDK，带缓存与积分优化 |
| 网页阅读 | 提取网页正文内容，支持缓存 |
| 代码执行 | 安全沙箱执行 Python，含危险调用黑名单 + 物理重试锁定 |
| 文件操作 | 读写文件、目录浏览、文件搜索，支持 `~` 用户目录展开 |
| 天气查询 | 高德 API，支持 3200+ 城市/地区 |
| 模型管理 | Web 界面管理多模型配置，支持热切换 |
| 会话管理 | 新建/切换/清空，侧边栏管理 |
| 长对话压缩 | SummarizationMiddleware，历史消息自动压缩 |
| 文件浏览器 | Web 界面浏览项目文件 |

---

## 架构设计

```text
前端 (Vue3 + TypeScript + Element Plus + Pinia)
  ├── views/          ChatView / KnowledgeView / MemoryView / FileBrowserView / SettingsView
  ├── components/     chat/ knowledge/ memory/ settings/ workspace/ layout/ common/
  ├── stores/         chatStore / layoutStore
  ├── composables/    useChatMessages / useMessageEdit / useSessionManager
  ├── api/            后端 API 封装（fetch）
  ├── router/         路由配置
  └── types/          类型定义
        │
        ▼ HTTP (SSE 流式)
后端 (FastAPI)
  ├── routers/
  │   ├── chat.py       SSE 流式对话端点
  │   ├── knowledge.py  知识库管理（上传/检索/构建）
  │   ├── memory.py     长期记忆管理（增删改查）
  │   ├── models.py     模型配置管理（CRUD + 热切换）
  │   ├── settings.py   env 通用配置读写
  │   └── workspace.py  工作区文件浏览
  ├── schemas/         Pydantic 数据模型
  └── main.py          应用入口
        │
        ▼
Agent 核心层 (LangChain 1.0 + LangGraph)
  ├── agent/
  │   ├── factory.py          Agent 工厂（支持依赖注入）
  │   ├── executor.py         同步/异步调用 + 流式输出
  │   ├── model_factory.py    模型工厂（LLM + 总结模型）
  │   ├── checkpointer.py     AsyncSqliteSaver 对话持久化
  │   ├── middleware.py       SummarizationMiddleware 长对话压缩
  │   └── config.py           SYSTEM_PROMPT 加载
  ├── tools/
  │   ├── time_tool.py        时间查询
  │   ├── weather_tool.py     天气查询（高德 API + 缓存）
  │   ├── rag_tool.py         知识库检索
  │   ├── memory_tool.py      长期记忆（save/recall/list/delete/clear）
  │   ├── file_tool.py        文件操作（read/write/list/search）
  │   ├── executor_tool.py    Python 代码执行（重试锁定）
  │   └── search_tool.py      联网搜索 + 网页阅读（Tavily）
  ├── rag/                     RAG 模块
  │   ├── retriever.py         MMR 检索
  │   ├── builder.py           向量库构建（MD5 增量）
  │   ├── loaders.py           多格式文档加载
  │   └── config.py            RAG 配置
  ├── memory/memory_manager.py  长期记忆向量存储
  ├── search/                   联网搜索模块
  │   ├── tavily_engine.py      Tavily 引擎封装
  │   └── cache.py              搜索/网页内容缓存
  ├── config/
  │   ├── settings.py           全局配置（模型、路径、API Key）
  │   └── prompt_loader.py      提示词加载
  ├── logger/setup.py           会话日志
  ├── executor/python_executor.py  代码执行引擎
  ├── prompts/system.txt        系统提示词模板
  ├── resources/                资源文件（城市编码等）
  └── errors.py                 统一异常分类
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js ^20.19.0 \|\| >=22.12.0
- 包管理器：uv（推荐）或 pip

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd OmniAgent
```

### 2. 安装后端依赖

```bash
# 方式 1：使用 uv 包管理器（推荐）
uv sync

# 如果电脑没有 uv，先安装：
pip install uv

# 方式 2：使用 pip
# pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动项目，在设置页面配置

无需手动编辑 `.env` 文件，启动项目后通过 Web 设置页面完成所有配置：

> 启动后访问 `http://localhost:5173/settings`，在设置页面中配置：
> - **模型管理**：添加 LLM 模型（Base URL、API Key、模型名）
> - **API 配置**：配置 Embedding、Tavily 搜索、高德地图等
>
> 所有配置保存后即时生效，配置会自动写入 `.env` 文件，无需手动创建。

**获取 API Key：**

- 阿里云百炼: [百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home)
- DeepSeek: [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
- OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)
- 高德地图: [高德开放平台](https://lbs.amap.com/)
- Tavily: [Tavily 控制台](https://app.tavily.com/)（每月 1000 免费积分）

### 5. 一键启动

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
- 检测并清理 8000 / 5173 端口上的残留进程
- 启动后端服务（http://localhost:8000）
- 启动前端开发服务器（http://localhost:5173）

### 6. 手动启动（可选）

```bash
# 后端（从项目根目录）
uvicorn backend.main:app --reload --port 8000

# 前端（新开终端）
cd frontend
npm run dev
```

访问 http://localhost:5173 开始使用。

### 7. 命令行模式（可选）

```bash
python main.py
```

输入 `quit` / `exit` / `q` 退出。

---

## 项目结构

```text
OmniAgent/
├── agent_core/                      # Agent 核心
│   ├── agent/                       # Agent 层
│   │   ├── factory.py               # Agent 工厂
│   │   ├── executor.py              # 执行器（同步/异步/流式）
│   │   ├── model_factory.py         # 模型工厂
│   │   ├── checkpointer.py          # 对话持久化
│   │   ├── middleware.py            # 长对话压缩
│   │   └── config.py                # 系统提示词
│   ├── tools/                       # Agent 工具（7 个）
│   ├── rag/                         # RAG 知识库
│   ├── memory/                      # 长期记忆
│   ├── search/                      # 联网搜索
│   ├── config/                      # 配置
│   ├── logger/                      # 日志
│   ├── executor/                    # 代码执行引擎
│   ├── prompts/                     # 提示词模板
│   ├── resources/                   # 资源文件
│   └── errors.py                    # 统一异常分类
├── backend/                         # FastAPI 后端
│   ├── routers/                     # API 路由（6 个）
│   ├── schemas/                     # 数据模型
│   └── main.py                      # 应用入口
├── frontend/                        # Vue3 前端
│   ├── src/
│   │   ├── views/                   # 页面（5 个）
│   │   ├── components/              # UI 组件
│   │   ├── stores/                  # 状态管理
│   │   ├── api/                     # API 封装
│   │   ├── router/                  # 路由
│   │   ├── composables/             # 组合式函数
│   │   └── types/                   # 类型定义
│   ├── package.json
│   └── vite.config.ts
├── docker/                          # Docker 部署
│   ├── backend/Dockerfile
│   ├── frontend/Dockerfile
│   ├── frontend/nginx.conf
│   └── .dockerignore
├── workspace/                       # 运行时数据（自动生成）
│   ├── vector_stores/               # 知识库向量存储
│   ├── memory/                      # 长期记忆向量存储
│   ├── checkpoints/                 # 对话检查点
│   ├── logs/                        # 日志文件
│   ├── cache/                       # 搜索缓存
│   ├── knowledge/                   # 知识文档
│   ├── uploads/                     # 上传文件
│   └── temp/                        # 临时文件
├── main.py                          # 命令行入口
├── start.ps1 / start.bat / start.sh # 一键启动脚本
├── docker-compose.yml               # Docker 一键编排
├── pyproject.toml                   # uv 项目配置
├── requirements.txt                 # pip 依赖
├── .env.example                     # 环境变量模板
└── .env                             # 环境变量（自动生成）
```

---

## 管理页面

项目提供 5 个管理页面，通过侧边栏导航访问：

| 页面 | 路径 | 功能 |
| :--- | :--- | :--- |
| 对话 | `/` | 与 Agent 对话，支持流式输出、暂停/中止 |
| 知识库 | `/knowledge` | 管理知识文档、检索测试、重建向量库 |
| 记忆 | `/memory` | 查看/搜索/添加/编辑/删除长期记忆 |
| 文件 | `/files` | 浏览项目文件目录树 |
| 设置 | `/settings` | 模型管理、API 配置、工作区管理、服务状态 |

### 设置页面功能

- **服务状态**：查看各服务（LLM、搜索、地图、向量库）的配置状态
- **模型管理**：添加/编辑/删除/切换 LLM 模型配置，支持热切换
- **API 配置**：管理 Embedding、Tavily 搜索、高德地图等 API Key
- **工作区管理**：查看工作区目录大小，清理缓存/日志等临时数据
- **关于信息**：版本号、运行时间、Python 版本

---

## 核心功能详解

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
| `read_file` | 文件操作 | 读取文本文件（支持分页） |
| `write_file` | 文件操作 | 写入文件（支持 `~` 展开 + 系统目录保护） |
| `list_directory` | 文件操作 | 浏览目录结构（支持递归、深度控制） |
| `search_files` | 文件操作 | 按通配符搜索文件名（支持分页） |
| `execute_python` | 代码执行 | 安全沙箱执行 Python（重试锁定 + 黑名单） |
| `search_web` | 联网搜索 | Tavily 搜索（7 天缓存，智能参数推断） |
| `read_webpage` | 联网搜索 | 提取网页内容（30 天缓存） |

### 流式输出（打字机效果）

**数据流：**

```text
Agent 生成 token → astream 推送 → 前端 fetch ReadableStream
→ 逐字拆入打字机队列 → 50ms/字追加到消息气泡
```

### 模型配置管理

通过 Web 设置页面管理多模型配置，支持热切换：

- 每个模型独立存储：名称、提供商、Base URL、API Key、模型名
- 设置默认模型后自动同步到运行时环境变量
- 切换模型无需重启服务

### 长对话压缩（SummarizationMiddleware）

当会话历史超过 100 条消息时，自动触发压缩，保留最近 10 条消息 + 一段摘要。

### RAG 检索优化（MMR）

使用 MMR（最大边际相关性）检索，强制引入不同主题的文档，避免检索结果单一。

### 长期记忆与知识库

- **RAG 知识库**：静态文档，需手动上传构建，存储在 `workspace/vector_stores/`
- **长期记忆**：Agent 在对话过程中自动保存的用户偏好/事实，存储在 `workspace/memory/`

---

## Harness 工程（核心经验）

### 物理堵死：代码执行重试锁定

连续失败达到 3 次后，工具进入**物理锁定**状态，相似代码（相似度 ≥ 0.4）直接拒绝执行，只有全新任务才会自动解锁。

### 物理堵死：危险代码黑名单

在子进程启动前拦截 `os.system`、`subprocess.run`、`requests`、`httpx`、`eval` 等危险调用。

### 智能参数推断

`search_web` 工具根据查询词自动推断 `topic` 和 `time_range`，如"今日热点新闻"→ `topic=news, time_range=day`。

### 内容安全清洗

去除 Unicode 控制字符、不可打印 ASCII 字符，截断过长内容，避免触发 LLM 服务商的内容安全检测。

### 缓存前置

- 搜索结果缓存 7 天
- 网页内容缓存 30 天
- 命中缓存不消耗 Tavily 积分

### 路径自动展开

`_safe_path()` 中调用 `os.path.expanduser()` 展开 `~` 为用户主目录。

---

## 部署指南

### 本地 Docker 部署

#### 1. 配置环境变量

```bash
Copy-Item .env.example -Destination .env  # Windows
# cp .env.example .env                      # Linux/Mac
```

编辑 `.env`，填入你的 API Key。

#### 2. 构建并启动

```bash
docker-compose up --build
```

#### 3. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000

#### 4. 停止服务

```bash
docker-compose down
# 停止并删除数据卷（会删除对话历史等数据）
# docker-compose down -v
```

### 单独部署后端

```bash
# 构建镜像
docker build -t omniagent-backend -f docker/backend/Dockerfile .

# 运行容器
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/workspace:/app/workspace \
  omniagent-backend
```

### 单独部署前端

```bash
cd frontend
npm run build
# 将 dist 目录部署到 Nginx、Vercel、Netlify 等
```

### Docker 配置说明

| 文件 | 作用 |
| :--- | :--- |
| `docker-compose.yml` | 一键编排前后端 |
| `docker/backend/Dockerfile` | 后端镜像构建 |
| `docker/frontend/Dockerfile` | 前端镜像构建（多阶段构建） |
| `docker/frontend/nginx.conf` | Nginx 反向代理配置（支持 SSE） |
| `docker/.dockerignore` | Docker 构建忽略列表 |

### Docker 命令快速参考

| 命令 | 说明 |
| :--- | :--- |
| `docker-compose up` | 启动服务 |
| `docker-compose up --build` | 重新构建并启动 |
| `docker-compose down` | 停止并删除容器和网络 |
| `docker-compose down -v` | 停止并删除容器、网络和数据卷 |
| `docker-compose logs -f` | 实时跟踪日志 |
| `docker system prune -a` | 深度清理所有未使用的 Docker 资源 |

---

## FAQ 常见问题

### Q1: API Key 在哪里获取？

- 阿里云百炼: [百炼控制台](https://bailian.console.aliyun.com/cn-beijing#/home)
- DeepSeek: [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
- OpenAI: [OpenAI Platform](https://platform.openai.com/api-keys)
- 高德地图: [高德开放平台](https://lbs.amap.com/)
- Tavily: [Tavily 控制台](https://app.tavily.com/)

### Q2: 如何添加自己的知识库？

通过 Web 页面操作：进入知识库页面 → 上传文档 → 点击"重建向量库"。支持 `.txt`、`.md` 格式。

### Q3: 如何更换主模型？

两种方式：
1. 修改 `.env` 中的 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`
2. 进入设置页面 → 模型管理 → 添加/切换模型（推荐，支持热切换）

### Q4: 前端报 502 / 连接失败怎么办？

1. 确认后端是否在 8000 端口运行：浏览器访问 `http://localhost:8000/`
2. 重新运行启动脚本：`.\start.ps1`
3. 检查浏览器控制台是否有 CORS 错误

### Q5: 对话历史存在哪里？

双重持久化：
- 后端：SQLite 数据库 `workspace/checkpoints/agent_checkpoints.db`
- 前端：浏览器 localStorage

### Q6: 长期记忆和 RAG 知识库有什么区别？

- **RAG 知识库**：静态文档，通过 Web 页面上传管理，存储在 `workspace/vector_stores/`
- **长期记忆**：Agent 自动保存的用户偏好/事实，存储在 `workspace/memory/`，使用独立的 Chroma 集合

### Q7: 代码执行失败 3 次后还会继续吗？

不会。`execute_python` 工具在连续失败 3 次后进入物理锁定状态，相似代码直接拒绝执行。需提交全新任务（相似度 < 0.4）才会自动解锁。

---

## 扩展指南

### 1. 添加新工具

在 `agent_core/tools/` 下创建新文件，实现 `@tool` 装饰的函数，然后在 `agent_core/tools/__init__.py` 的 `TOOLS` 列表中注册。

### 2. 添加新知识库格式

修改 `agent_core/rag/loaders.py` 中的 `load_documents()` 函数，添加新的文档加载器。

### 3. 自定义系统提示词

编辑 `agent_core/prompts/system.txt`，修改后保存即可生效（无需重启）。

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 后端：遵循 PEP 8
- 前端：遵循 ESLint 规范
- 新加依赖请同步更新 `pyproject.toml` 和 `requirements.txt`

---

## 许可证

MIT