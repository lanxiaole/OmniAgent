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
| 📜 长对话压缩 | SummarizationMiddleware，10条触发，保留5条      |
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
- Node.js 18+
- SQLite 3

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd OmniAgent
```

### 2. 后端配置

```bash
# 安装依赖（使用 uv 包管理器）
uv pip install -r requirements.txt

# 或使用 pip
# pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key：
# DASHSCOPE_API_KEY=your_key
# AMAP_API_KEY=your_key
```

### 3. 构建知识库

```bash
cd agent_core/rag
python builder.py
```

### 4. 启动后端

```bash
cd backend
uvicorn main:app --reload --port 8000
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
│   ├── config/settings.py       # 全局配置（模型、路径、API Key）
│   ├── prompts/                 # Prompt 模板
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
│       └── utils/storage.ts     # localStorage 工具
├── resources/                   # 资源文件（城市编码）
└── logs/                        # 日志文件
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

### RAG 检索优化（MMR）

**问题：** 问"我叫什么名字"时，普通相似度检索第一条返回的是性格描述而非名字。

**解决方案：** 使用 MMR（最大边际相关性）检索，强制引入不同主题的文档：

```python
return vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": top_k, "fetch_k": 20}
)
```

**核心公式：** `最终分数 = λ × 相关性 - (1-λ) × 与已选文档的相似度`

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
from agent_core.rag.retriever import retrieve
docs = retrieve(question)
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

---

## 📝 许可证

MIT
