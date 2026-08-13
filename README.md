# OmniAgent

一个开箱即用的**个人智能桌面助手**。基于 LangChain + LangGraph 构建，拥有流式对话、知识库检索、长期记忆、代码执行、联网搜索、文件管理等能力，并以桌面应用的形式交付——普通用户下载安装包即可使用，无需搭建任何环境。

---

## 面向普通用户

### 它是什么

OmniAgent 是一个装在电脑里的 AI 助手，能够：

- **自然对话**：流式输出，像打字机一样逐字呈现，可随时暂停或中止
- **管理知识库**：上传你的文档（`.txt` / `.md`），Agent 能基于这些内容回答你的问题
- **记住关于你的事**：自动记住你的偏好、习惯、身份信息，跨会话持久化
- **读写你的文件**：帮你读文件、写文件、浏览目录、搜索文件
- **执行代码**：编写并运行 Python 代码，做计算、处理数据、生成图表
- **联网搜索**：搜索互联网、阅读网页，回答实时问题
- **查天气**：查询全国 3200+ 城市/地区的天气

### 下载安装

前往 [GitHub Releases](https://github.com/lanxiaole/OmniAgent/releases) 下载对应平台的安装包。

**Windows**（当前支持）：

| 安装包 | 说明 |
| :--- | :--- |
| `OmniAgent Setup 1.0.0.exe` | 安装版，可自定义安装目录，创建桌面与开始菜单快捷方式 |
| `OmniAgent 1.0.0.exe` | 便携版，免安装，双击即用 |

> macOS（`.dmg`）与 Linux（`.AppImage`）安装包暂未提供，如需要可通过源码自行构建（见下文「面向开发者」）。

### 首次启动

1. 双击运行 OmniAgent。
2. 打开左侧「设置」页面，配置你的大模型（这是必须的一步，否则无法对话）。
3. 配置完成后即可开始使用。

> 数据默认保存在系统标准用户目录（Windows 为 `%APPDATA%\OmniAgent`，macOS 为 `~/Library/Application Support/OmniAgent`），无需手动管理。

### 配置模型（API Key）

OmniAgent 支持任何 OpenAI 兼容接口的模型服务。打开「设置 → 模型管理」，点击添加模型，填入：

- **Base URL**：模型服务地址
- **API Key**：你的密钥
- **模型名**：要使用的模型名称

常用服务商的获取地址：

| 服务商 | 获取地址 |
| :--- | :--- |
| 阿里云百炼 | [bailian.console.aliyun.com](https://bailian.console.aliyun.com/cn-beijing#/home) |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) |
| 高德地图（天气用） | [lbs.amap.com](https://lbs.amap.com/) |
| Tavily（联网搜索用） | [app.tavily.com](https://app.tavily.com/)（每月 1000 免费积分） |

> 除了模型外，其他都是可选的。不配置天气、搜索，就只是少了对应能力，不影响基础对话。

### 页面说明

项目提供 5 个页面，通过顶部导航访问：

| 页面 | 路径 | 功能 |
| :--- | :--- | :--- |
| 对话 | `/` | 与 Agent 对话，支持流式输出、工具调用、操作审批 |
| 知识库 | `/knowledge` | 上传/编辑/删除文档、检索测试、重建索引 |
| 记忆 | `/memory` | 查看/搜索/添加/编辑/删除长期记忆 |
| 文件 | `/files` | 浏览数据目录文件树、预览文件内容 |
| 设置 | `/settings` | 模型管理、API 配置、工作区管理、服务状态 |

---

## 面向开发者

### 技术栈

| 层 | 技术 |
| :--- | :--- |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| 后端 | Python + FastAPI + uvicorn |
| Agent | LangChain 1.0 + LangGraph |
| 存储 | Chroma（知识库/记忆向量检索）+ SQLite（对话持久化） |
| 桌面 | Electron + PyInstaller + electron-builder |

### 环境要求

- Python `>= 3.10`
- Node.js `^20.19.0 || >=22.12.0`
- 包管理器：`uv`（推荐）或 `pip`

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/lanxiaole/OmniAgent.git
cd OmniAgent

# 2. 安装后端依赖（推荐 uv）
uv sync
# 或 pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install
```

### 启动方式

**方式一：一键启动脚本**

```bash
# Windows (PowerShell)
.\start.ps1

# Windows (CMD)
start.bat

# Linux / macOS
chmod +x start.sh
./start.sh
```

脚本会自动检测并清理 8000 / 5173 端口残留进程，然后分别启动后端（`http://localhost:8000`）和前端（`http://localhost:5173`）。

**方式二：手动启动**

```bash
# 后端（项目根目录）
uvicorn backend.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm run dev
```

**方式三：命令行模式**

```bash
python main.py
```

输入 `quit` / `exit` / `q` 退出。

### 桌面应用开发模式

```bash
cd desktop
npm run dev
```

Electron 主进程会自动启动后端并加载前端 dev server。支持 `npm run dev:backend` 单独启动后端。

### 配置说明

无需手动创建 `.env`，启动后在「设置」页面完成所有配置，保存即时生效。

如需手动配置，复制 `.env.example` 为 `.env` 后编辑。LLM 与 Embedding 是两套独立配置，各自对应 OpenAI 兼容接口的 `base_url` / `api_key` / `model` 三个字段。示例参考 `.env.example`。

### 项目结构

```text
OmniAgent/
├── agent_core/                 # Agent 核心层
│   ├── agent/                  # 工厂、执行器、模型工厂、检查点、审批中间件
│   ├── tools/                  # 15 个 Agent 工具（7 个文件）
│   ├── rag/                    # RAG 知识库（检索/构建/加载器/配置）
│   ├── memory/                 # 长期记忆向量存储
│   ├── search/                 # 联网搜索（Tavily + 缓存）
│   ├── executor/               # Python 代码执行引擎
│   ├── config/                 # 全局配置、Embedding、提示词加载
│   ├── prompts/system.txt      # 系统提示词
│   └── resources/              # 城市编码等资源
├── backend/                    # FastAPI 后端
│   ├── routers/                # 7 个路由（chat/approval/knowledge/memory/models/settings/workspace）
│   ├── schemas/                # Pydantic 数据模型
│   └── main.py                 # 应用入口（含前端静态托管）
├── frontend/                   # Vue 3 前端
│   └── src/                    # 5 个页面 + 组件 + 状态 + API 封装
├── desktop/                    # Electron 桌面端
│   ├── main/                   # 主进程（后端启动/进程管理）
│   ├── preload/                # 预加载脚本
│   ├── scripts/                # 打包辅助脚本
│   └── electron-builder.yml    # 桌面打包配置
├── docker/                     # Docker 部署
├── main.py                     # 命令行入口
├── start.ps1 / start.bat / start.sh   # 一键启动脚本
├── docker-compose.yml          # Docker 编排
├── pyproject.toml / requirements.txt  # Python 依赖
└── .env.example                # 环境变量模板
```

### Agent 工具清单（15 个）

| 工具 | 分类 | 用途 |
| :--- | :--- | :--- |
| `get_current_time` | 系统 | 获取当前日期时间 |
| `get_weather` | 系统 | 查询天气（高德 API，10 分钟缓存） |
| `search_knowledge` | 知识库 | 检索知识库文档内容 |
| `save_user_memory` | 记忆 | 保存长期记忆（自动覆盖相似内容） |
| `recall_user_memory` | 记忆 | 检索用户记忆 |
| `list_user_memories` | 记忆 | 列出所有记忆 |
| `delete_user_memory` | 记忆 | 删除指定记忆 |
| `clear_user_memories` | 记忆 | 清空所有记忆 |
| `read_file` | 文件 | 读取文本文件（支持分页） |
| `write_file` | 文件 | 写入文件（需审批） |
| `list_directory` | 文件 | 浏览目录结构 |
| `search_files` | 文件 | 按通配符搜索文件名 |
| `execute_python` | 代码 | 执行 Python（需审批，含失败锁定） |
| `search_web` | 联网 | Tavily 搜索（7 天缓存） |
| `read_webpage` | 联网 | 提取网页内容（30 天缓存） |

### 打包发布

```bash
cd desktop
npm run dist
```

`dist` 命令依次执行：PyInstaller 打包后端 → 构建前端 → electron-builder 打包桌面应用。产物输出到 `desktop/release/`（Windows 下为 nsis 安装版 + portable 便携版）。

### Docker 部署

```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 2. 构建并启动
docker-compose up --build

# 3. 访问
# 前端: http://localhost:5173
# 后端 API: http://localhost:8000

# 4. 停止
docker-compose down
```

| 命令 | 说明 |
| :--- | :--- |
| `docker-compose up` | 启动服务 |
| `docker-compose up --build` | 重新构建并启动 |
| `docker-compose down` | 停止并删除容器和网络 |
| `docker-compose logs -f` | 实时跟踪日志 |

### 扩展指南

- **添加新工具**：在 `agent_core/tools/` 下创建新文件，用 `@tool` 装饰实现，然后在 `agent_core/tools/__init__.py` 的 `TOOLS` 列表中注册。
- **添加新知识库格式**：修改 `agent_core/rag/loaders.py`，注册新的文档加载器。
- **自定义系统提示词**：编辑 `agent_core/prompts/system.txt`，保存后即时生效。

---

## 核心机制

### 操作审批

`write_file` 与 `execute_python` 等敏感操作会触发人工审批——Agent 在写入 workspace 之外的文件、执行超长或危险代码前，会先征求你的同意，避免误操作。

### 代码执行安全

- **危险调用黑名单**：子进程启动前拦截 `os.system`、`subprocess.run`、`requests`、`eval` 等危险调用。
- **失败重试锁定**：连续失败 3 次后进入物理锁定，相似代码（相似度 ≥ 0.4）直接拒绝执行，只有全新任务才会解锁。

### 知识库与记忆

- **知识库**：存放文档类知识（项目文档、技术方案、笔记等），由用户上传管理，使用向量检索（语义搜索）。
- **长期记忆**：存放用户个人信息（偏好、习惯、身份等），由 Agent 在对话中自动收集，也可手动添加。两者各司其职、互不干扰。

### 长对话压缩

当会话历史超过 100 条消息时，自动触发摘要压缩，保留最近消息 + 历史摘要，避免上下文溢出。

---

## 常见问题

**Q: 为什么对话没有反应？**
确认已在「设置」页面配置了可用的模型（Base URL、API Key、模型名三者缺一不可）。

**Q: 知识库上传后检索不到？**
上传后需重建向量库（知识库页面点击「重建」），且当前支持 `.txt` 与 `.md` 格式。

**Q: 知识库和记忆有什么区别？**
知识库存文档、参考资料；记忆存你个人的偏好、习惯、身份信息。前者手动上传，后者 Agent 自动收集。

**Q: 对话历史存在哪里？**
SQLite 数据库，位于用户数据目录下的 `workspace/checkpoints/`。

**Q: 如何备份数据？**
直接复制用户数据目录即可（Windows 为 `%APPDATA%\OmniAgent`），包含知识库、记忆、对话记录、日志等全部数据。

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

代码规范：后端遵循 PEP 8，前端遵循 ESLint；新增依赖请同步更新 `pyproject.toml` 与 `requirements.txt`。

---

## 许可证

MIT
