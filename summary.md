# 一.项目背景

OmniAgent 是一个基于 LangChain 1.0 框架开发的智能助手系统，采用 Vue3 前端 + FastAPI 后端 + LangChain Agent 核心 的全栈架构，具备流式对话、自动工具调用、知识检索（RAG）、多轮记忆、会话管理等能力。

# 二.项目架构

```text
前端 (Vue3 + TypeScript + Element Plus)
  ├── 会话侧边栏（新建/切换/清空会话）
  ├── 聊天界面（流式打字机效果、思考中动画）
  ├── 编辑已发送消息（重塑上下文）
  ├── 暂停/中止回复
  └── localStorage 管理会话和消息历史
        │
        ▼ HTTP (SSE 流式)
后端 (FastAPI)
  ├── /api/chat（非流式）
  ├── /api/chat/stream（SSE 流式，带断连检测和任务取消）
  ├── /api/chat/history（GET + DELETE）
  └── services/agent_service.py（调用 Agent 核心层）
        │
        ▼
Agent 核心层 (LangChain 1.0 + LangGraph)
  ├── create_agent（ReAct 模式）
  ├── AsyncSqliteSaver（多轮对话持久化）
  ├── SummarizationMiddleware（长对话压缩）
  └── 工具：时间、天气、RAG 知识库查询
```

# 三.开发过程

## 项目初始化

创建项目目录结构

初始化 Git 仓库

创建 .env 文件存储 API Key

创建 .gitignore 文件

创建 requirements.txt 文件

## 模块开发

### 模型模块

创建 model/client.py 文件，实现与大模型的交互

使用 ChatOpenAI 模型实例，设置为 qwen3-max

实现 chat() 函数，用于与模型对话

### 记忆模块

创建 memory/manager.py 文件，实现对话历史管理

实现 add_user_message()、add_ai_message()、get_messages() 等函数

### 工具模块

创建 tools/time_tool.py 文件，实现时间工具

使用 @tool 装饰器定义 get_current_time() 函数

实现 maybe_use_tool() 函数，用于关键词匹配触发工具

### RAG 模块

创建 rag/builder.py 文件，实现向量库构建功能

创建 rag/retriever.py 文件，实现知识检索功能

实现 load_documents()、build_vector_store()、retrieve() 等函数

添加基于 MD5 的自动增量构建功能

### 日志模块

创建 logger/setup.py 文件，实现统一的日志系统

配置控制台和文件日志处理器

## 主程序开发

创建 main.py 文件，实现主对话循环

实现 build_enhanced_message() 函数，用于构建增强消息

集成模型、记忆、工具和 RAG 模块

## 测试模块

创建 tests/test_all.py 文件，实现单元测试

测试模型调用、记忆模块、工具触发、RAG 检索和集成流程

# 四.重构为 LangChain 1.0

## 工具模块重构

删除 maybe_use_tool() 函数和 TIME_TOOL_KEYWORDS

只保留 @tool 装饰的 get_current_time 函数

修改 tools/**init**.py，只导出 TOOLS = [get_current_time]

## Agent 执行器重构

创建 agent/executor.py 文件，实现基于 create_agent 的 Agent 执行器

使用 create_agent(model=model, tools=TOOLS, system_prompt=...) 创建 Agent

更新 run_agent() 函数，使用正确的参数格式调用 Agent

移除手动的对话历史管理，使用 LangChain 内置的记忆功能

## 主程序简化

删除 build_enhanced_message 函数

直接调用 run_agent(user_input, thread_id)

删除所有手动的 memory.add\_\* 调用

## 测试模块更新

更新测试函数以适应新的 LangChain 1.0 结构

移除对 model 和 memory 模块的测试

更新 test_tools 函数，测试工具的结构是否正确

更新 test_integration 函数，使用新的 run_agent 函数

# 五.遇到的问题及解决方法

## 依赖缺失

问题：ModuleNotFoundError: No module named 'langchain_community'

解决方法：在 requirements.txt 中添加 langchain-community 依赖

## 日志编码错误

问题：UnicodeEncodeError: 'gbk' codec can't encode character

解决方法：在 logger.py 的 RotatingFileHandler 中添加 encoding="utf-8" 参数

## 工具调用方式不匹配

问题：从手动关键词匹配切换到 LangChain 自动工具调用时，代码结构不匹配

解决方法：重构工具模块和 Agent 执行器，使用 LangChain 1.0 的标准写法

## 测试函数不兼容

问题：旧的测试函数不适应新的 LangChain 1.0 结构

解决方法：更新测试函数，移除对旧模块的依赖，使用新的 Agent 执行器

# 六.早期项目结构

```text
OmniAgent/
├── agent/
│   ├── __init__.py
│   └── executor.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── knowledge/
│   ├── AI.txt
│   └── my_knowledge.txt
├── logger/
│   ├── __init__.py
│   └── setup.py
├── memory/
│   ├── __init__.py
│   └── manager.py
├── model/
│   ├── __init__.py
│   └── client.py
├── rag/
│   ├── __init__.py
│   ├── builder.py
│   ├── config.py
│   └── retriever.py
├── tests/
│   ├── __init__.py
│   └── test_all.py
├── tools/
│   ├── __init__.py
│   └── time_tool.py
├── .gitignore
├── main.py
└── requirements.txt
```

# 七.RAG 检索优化：MMR 解决相似度检索偏差

## 问题回顾

用户问"我叫什么名字"时，普通相似度检索（similarity_search）返回的第一个文档是：

"我性格内向但情商高，能一眼看穿别人。我有孤独的能力，但也渴望被接住。"

而不是：

"我叫隗迦勒，哈尔滨人，现在在昆明读书..."

为什么？

向量检索计算的是语义相似度。"我叫什么名字"这个问句，在向量空间里，可能和"性格内向、能看穿别人"这种自我描述的句子距离更近（都是关于"我"的抽象特征），而和"我叫隗迦勒"这种具体事实句子的距离反而稍远。这是 Embedding 模型的一个常见偏差。

## MMR 做了什么

MMR = Maximum Marginal Relevance（最大边际相关性）

核心思想：在保证相关性的前提下，让选出来的文档彼此尽可能不同。

公式简化理解：

```text
最终分数 = λ × 相关性 - (1-λ) × 与已选文档的相似度
λ 控制"相关性"和"多样性"的权重（通常 0.5~0.7）
```

第一次选最相关的文档（可能还是"性格内向"那条）

第二次选的时候，会惩罚那些和"性格内向"太像的文档，于是"名字"那条因为和它不相似，反而得分上升

第三次继续惩罚重复内容

所以即使"性格内向"那条相关性略高，MMR 也会强制引入不同主题的文档。

## 为什么之前 top_k=1 时完全没救？

只取第一条时，MMR 也救不了——它只能在 k>1 时发挥作用。把 top_k 从 1 改成 3，给了 MMR 选择空间。然后 MMR 在三条里挑最相关且不重复的，最终把"名字"那条排到了第一。

## 后续优化建议

保持 MMR + top_k=3~5，这是非常稳健的配置

可以调整 λ 值（在 as_retriever 中加 lambda_mult 参数，默认 0.5）：

更看重相关性（不怕重复）：lambda_mult=0.7

更看重多样性（想覆盖不同方面）：lambda_mult=0.3

如果某些问题仍然检索不准，可以尝试把知识库每行前面加上类型标签：

```text
[名字] 我叫隗迦勒，哈尔滨人...
[性格] 我性格内向但情商高...
[技术] 我学过 LangChain 1.0...
```

总结： 之前困扰了几个小时的问题，本质是普通相似度检索的"趋同"缺陷，MMR 通过强制多样性解决了它，是经典的检索技术。

# 八.Checkpointer 与 Middleware 集成

## 安装依赖

```text
pip install langgraph-checkpoint-sqlite deepagents
```

## 重构 Agent 核心代码

将 agent_core/agent/executor.py 拆分为多个职责单一的文件：

创建了 config.py、checkpointer.py、model_factory.py、middleware.py 等模块

实现了模块化的代码结构，提高了代码的可维护性

## 实现对话状态持久化

```python
# 创建 SQLite 连接
conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)

# 创建 SqliteSaver 实例
checkpointer = SqliteSaver(conn)
checkpointer.setup()
```

使用 SqliteSaver 实现对话状态的持久化存储

数据库文件存储在 agent_core/data/agent_checkpoints.db

自动创建数据目录（如果不存在）

## 实现自动上下文总结

```python
summarization_middleware = SummarizationMiddleware(
    model=summarizer_model,
    trigger=("messages", 10),  # 当消息数达到10条时触发总结
    keep=("messages", 5),      # 保留最近5条消息
)
```

## 创建 Agent

```python
agent = create_agent(
    model=model,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
    middleware=middlewares,
)
```

## 调用 Agent

```python
config = RunnableConfig(configurable={"thread_id": thread_id})
result = global_agent_executor.invoke(
    {"messages": [{"role": "user", "content": user_input}]},
    config=config
)
```

## 更新后端 API

更新了 schemas/chat.py，确保包含 thread_id 字段

更新了 services/agent_service.py，实现了 get_agent_reply 和 clear_session 函数

更新了 routers/chat.py，添加了清空会话的接口

## 遇到的困难

| 问题                         | 解决方法                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| Checkpointer 初始化类型错误  | 使用 sqlite3.connect 创建连接，传递 check_same_thread=False，然后创建实例并调用 setup() |
| 模型提供者识别错误           | 使用 get_summarizer_model 函数获取总结模型实例                                          |
| 函数名冲突                   | 将导入的 clear_session 重命名为 agent_clear_session                                     |
| 手动管理 \_sessions 字典冗余 | 改为使用 LangChain 官方 RunnableConfig 方式，通过 thread_id 实现会话隔离                |

# 九.流式输出功能实现

## 背景与目标

问题：用户发送消息后，需要等待 Agent 完整生成全部回复内容，前端才能一次性渲染，等待时间长、体验差（"白屏等待"）。

目标：实现类似 ChatGPT 的"打字机效果"——Agent 每生成一个字/词（token），前端即时显示。

核心挑战：

LangChain 1.0 Agent（底层是 LangGraph）的流式输出格式与同步调用完全不同

框架内部的"中间件"（如 SummarizationMiddleware）会产生干扰流

异步流式链路需要全栈打通：Agent → Service → Router → 前端

技术栈：

后端框架: FastAPI

AI 框架: LangChain 1.0 (LangGraph)

LLM: Qwen3-Max (via DashScope API)

会话持久化: SQLite (AsyncSqliteSaver)

前端: Vue 3 + TypeScript

## 架构总览

```text
用户浏览器 (Vue3)
       │
       ▼  fetch (SSE 流)
FastAPI Router (/api/chat/stream)
       │
       ▼  StreamingResponse
Service 层 (agent_service.py)
       │
       ▼  解包 (token, metadata)
Agent 核心层 (executor.py)
       │
       ▼  agent.astream(stream_mode="messages")
LangGraph Agent (create_agent)
  ├── ChatOpenAI (qwen3-max)
  ├── AsyncSqliteSaver (多轮记忆)
  ├── SummarizationMiddleware (长对话压缩)
  └── Tools (时间/天气/RAG)
```

关键决策：

为什么用 fetch 而不是 EventSource：EventSource 仅支持 GET 请求，无法发送请求体；我们需要 POST 来传递 message 和 thread_id，所以选择 fetch + ReadableStream 方案。

为什么 AsyncSqliteSaver 而不是 SqliteSaver：同步版本不支持异步流式调用，会导致 await agent.astream() 报错或阻塞事件循环。

## 各层实现详解

### Agent 核心层 (agent_core/agent/executor.py)

```python
async def stream_agent(user_input: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    agent = await get_async_agent_executor()
    config = RunnableConfig(configurable={"thread_id": thread_id})

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        stream_mode="messages"    # 👈 关键参数
    ):
        token, metadata = chunk   # 👈 chunk 是元组，不是对象！
        if token.content:
            yield token.content
```

核心技术点：

stream_mode="messages": LangGraph 提供了三种流式模式，这个模式专门用于输出 LLM 生成的 token 流。

返回值是元组 (token, metadata): 同步 invoke() 返回完整消息对象，但 astream() 每次产出的是一个 (AIMessageChunk, dict) 元组。

### 内部干扰过滤（关键踩坑）

```python
async def filtered_stream():
    async for chunk in raw_stream:
        token, metadata = chunk
        if not isinstance(token, AIMessageChunk):
            continue
        if not token.content:
            continue

        # 关键词过滤
        summarization_keywords = ["## SESSION INTENT", "## SUMMARY", ...]
        if any(keyword in token.content for keyword in summarization_keywords):
            continue

        # 来源节点过滤
        node_name = metadata.get("langgraph_node", "")
        if "summar" in node_name.lower():
            continue

        yield token
```

### Checkpointer 异步改造

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def get_async_checkpointer():
    conn = await aiosqlite.connect(str(DB_PATH))
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    return checkpointer
```

### 服务层 (backend/services/agent_service.py)

```python
async def stream_agent_reply(message: str, thread_id: str) -> AsyncGenerator[str, None]:
    from agent_core.agent.executor import stream_agent
    async for token in stream_agent(message, thread_id):
        yield token
```

### 路由层 (backend/routers/chat.py)

```python
@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    async def event_generator():
        async for token in stream_agent_reply(request.message, request.thread_id):
            yield f"data: {json.dumps(token, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps('[DONE]')}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

SSE 格式要求：

每条消息以 data: 开头

每条消息以 \n\n 结尾

[DONE] 是流结束的约定标记

### 前端 API 层 (frontend/src/api/chat.ts)

```typescript
export const sendMessageStream = async (
  message: string,
  threadId: string,
  onToken: (token: string) => void,
): Promise<void> => {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        const token = JSON.parse(data);
        if (token === "[DONE]") return;
        onToken(token);
      }
    }
  }
};
```

### 前端组件层 (ChatContainer.vue)

```typescript
const handleSend = async (userMessage: string) => {
  // 1. 立即显示用户消息
  messages.value.push({ role: "user", content: userMessage });

  // 2. 添加空的助手消息占位
  const assistantIndex = messages.value.length;
  messages.value.push({ role: "assistant", content: "" });

  // 3. 流式接收，逐字追加
  await sendMessageStream(userMessage, props.threadId, (token: string) => {
    messages.value[assistantIndex].content += token;
    saveLocalHistory(props.threadId, messages.value);
    scrollToBottom();
  });
};
```

## 流式输出踩坑全集

| 序号 | 问题现象                                   | 根本原因                                | 解决方案                                      |
| ---- | ------------------------------------------ | --------------------------------------- | --------------------------------------------- |
| 1    | Runnable object has no attribute 'astream' | 全局 Agent 实例类型不对                 | 确保使用 create_agent 返回的 LangGraph 图对象 |
| 2    | 流式输出混杂 "## SESSION INTENT" 等        | SummarizationMiddleware 的 token 被捕获 | 通过 metadata["langgraph_node"] 过滤          |
| 3    | Agent 层正常，但 curl 收不到流             | Service 层解包元组有误                  | 将 token, metadata = chunk 解包逻辑正确实现   |
| 4    | 前端 fetch 报错                            | 使用了 axios，不支持 ReadableStream     | 改用原生 fetch                                |
| 5    | 切换会话后消息混乱                         | 前端 threadId 未正确传递                | 检查 sendMessageStream 的 threadId 参数来源   |

## 前端流式输出优化：逐字打字机效果

```text
后端 SSE 推送 token
        │
        ▼
前端收到 token: "你好，我是"
        │
        ▼
拆成单字: ["你", "好", "，", "我", "是"]
        │
        ▼
推入 typewriterQueue
        │
        ▼
定时器每 50ms 从队列头部取一个字
        │
        ▼
追加到 messages[i].content
        │
        ▼
Vue 响应式更新视图 → 用户看到逐字出现
```

# 十."暂停/中止生成"功能实现

## 功能定义

允许用户在 Agent 思考或回复过程中，随时点击"暂停"按钮：

前端立刻断开流式连接，停止接收数据

后端感知到断开后，取消正在执行的 Agent 任务

界面不留残留空消息，可立即发送新消息

## 整体架构与数据流

```text
用户点击"暂停"
      │
      ▼
前端 abortController.abort()  →  fetch 连接断开
      │
      ▼
服务器 http.disconnect 消息  →  后端检测到断开
      │
      ▼
asyncio.create_task(agent_worker)  →  agent_task.cancel()
      │
      ▼
stream_agent_reply 中 asyncio.CancelledError  →  优雅中止
      │
      ▼
LangGraph 内部自动处理中断状态 → 下次对话正常启动
```

## 前端三步走

### 第 1 步：消息唯一 ID — 根治动画污染和幽灵气泡

通俗讲：原来每条消息都是用"队伍里的位置"（索引）当名字的。一旦有人插队或者离队，名字就全乱了。现在我们给每条消息发了一个全球唯一的身份证号。

```typescript
const generateMessageId = () => {
  return (
    "msg_" + Date.now() + "_" + Math.random().toString(36).substring(2, 10)
  );
};
messages.value.push({
  id: generateMessageId(),
  role: "user",
  content: userMessage,
});
messages.value.push({
  id: generateMessageId(),
  role: "assistant",
  content: "",
});
```

### 第 2 步：API 层引入 AbortSignal — 让 fetch 可被中断

通俗讲：fetch 就像一个快递员，你叫他去取东西，他一定会送到。我们给快递员一个"传呼机"（signal），你只要按暂停，就通过传呼机喊他："别送了！回来！"

```typescript
export const sendMessageStream = async (
  message: string,
  threadId: string,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<void> => {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId }),
    signal: signal,
  });
  // ...
};
```

### 第 3 步：组件状态管理 — 串联暂停逻辑，防止崩溃

通俗讲：这一步是给"暂停"按钮装上一个聪明的大脑。每次发新消息都会买一个新的"传呼机"（new AbortController()），因为旧的已经用过了会失效。

```typescript
const abortStream = () => {
  if (abortController.value) {
    abortController.value.abort();
    abortController.value = null;
  }
  stopTypewriter();
  if (messages.value.length > 0) {
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg.role === "assistant" && lastMsg.content.trim() === "") {
      messages.value.pop();
    }
  }
  saveLocalHistory(props.threadId, messages.value);
  loading.value = false;
};
```

## 后端真中断

### 困难 1：request.is_disconnected() 不可靠

通俗讲：我们原本想让服务器自己去问："客户端还在吗？"，但中间隔着一个 CORS 中间件，服务器根本看不清。于是我们派一个"监听员"专门守在门口。

```python
async def disconnect_listener():
    while True:
        message = await http_request.receive()
        if message['type'] == 'http.disconnect':
            await result_queue.put(('disconnect', None))
            break
```

### 困难 2：让 Agent 任务可以被取消

通俗讲：服务器通知 Agent "别干了"，但 Agent 得自己会"听指令"才行。我们在 Agent 代码里放了一个"中断开关"。

```python
async def stream_agent_reply(message, thread_id):
    try:
        async for token in stream_agent(message, thread_id):
            yield token
    except asyncio.CancelledError:
        logger.info(f"Agent 流式任务被取消")
```

### 关于检查点清理的重大发现（来自实践验证）

原方案曾建议在暂停后手动删除 SQLite 中的检查点记录。小家伙在测试中发现：删掉所有检查点清理代码后，不仅没有卡死，反而反应更快。

原因：agent_task.cancel() 触发的 CancelledError 已经被 LangGraph 内部机制正确处理，它会自动将任务状态标记为"中断"，下次请求可直接从干净状态开始。

最终结论：检查点清理代码是过度设计，已安全移除。

## 实验验证的边界行为

| 暂停时机                 | 结果                                 | 原因                                 |
| ------------------------ | ------------------------------------ | ------------------------------------ |
| Agent 还没开始思考时暂停 | 对话彻底消失，不留痕迹               | 检查点尚未保存任何状态               |
| 工具调用期间暂停         | 工具结果被保留，下次对话会"接着"回答 | 工具调用是原子操作，一旦发出就会完成 |
| LLM 已生成文字时暂停     | 已生成的文字被保留在对话历史中       | 检查点机制会保存已生成的 token       |

## 暂停功能踩坑全集

| 序号 | 问题现象                       | 根本原因                              | 解决方案                                                  |
| ---- | ------------------------------ | ------------------------------------- | --------------------------------------------------------- |
| 1    | 所有 AI 气泡都有闪烁光标       | v-for 用 index 做 key，DOM 被错误复用 | 用 generateMessageId() 生成唯一 ID 做 key，删除了光标动画 |
| 2    | 暂停后残留幽灵气泡             | 空助手占位消息未被清理                | abortStream 中 pop() 空消息                               |
| 3    | 暂停后发新消息卡在"思考中"     | AbortController 一次性使用后未更新    | 每次请求 new AbortController()，请求结束清理              |
| 4    | is_disconnected() 检测不到断开 | CORS 中间件干扰                       | 改用 http_request.receive() 监听 http.disconnect          |
| 5    | 一度以为需要手动清理检查点     | 对 LangGraph 中断机制理解不足         | 经实践验证，删除手动清理，完全无问题且更快                |

# 十一、"编辑已发送消息并重塑上下文"功能实现

## 功能定义

允许用户编辑任意一条历史消息，保存后：

该消息及其之后的所有对话被截断删除

截断前的对话历史完整保留

Agent 基于干净的上下文重新回复

## 整体架构与数据流

```text
编辑前：thread_id: "old_123"
      前端: [msg1, AI1, msg2, AI2, msg3, AI3]
      SQLite: 完整检查点

点击编辑 msg2 → 修改为 msg2' → 保存
                ↓
      截断: [msg1, AI1]  ← 保留
            [msg2, AI2, msg3, AI3]  ← 删除
                ↓
      新 thread_id: "new_789"
                ↓
      前端 localStorage["new_789"] = [msg1, AI1]
                ↓
      handleSend(msg2') → 使用新 thread_id
                ↓
      Agent 查 SQLite → "new_789" 不存在 → 从零开始
      Agent 回复: 基于干净上下文的回答
```

## 核心技术原理：thread_id 就是记忆钥匙

| 存储位置           | 存什么                   | 编辑后如何处理         |
| ------------------ | ------------------------ | ---------------------- |
| 前端 localStorage  | 界面上展示的消息列表     | 截断并迁移到新 ID      |
| 后端 SQLite 检查点 | LangGraph 的完整执行状态 | 不处理（新 ID 下为空） |

## 分步实现详解

### 第 1 步：给用户消息添加编辑按钮（UI 改造）

```html
<el-button
  v-if="msg.role === 'user' && editingMessageId !== msg.id"
  class="edit-action-btn"
  size="small"
  :icon="Edit"
  @click.stop="editMessage(msg.id)"
>
  编辑
</el-button>
```

### 第 2 步：实现编辑弹窗逻辑

```typescript
const editMessage = (messageId: string) => {
  if (loading.value) return;
  const msg = messages.value.find((m) => m.id === messageId);
  if (!msg || msg.role !== "user") return;
  editingMessageId.value = messageId;
  editingContent.value = msg.content;
};
```

### 第 3 步：实现 saveEdit — 截断 + 重发（核心逻辑）

```typescript
const saveEdit = async (messageId: string) => {
  // 找到被编辑消息在 messages 数组中的索引
  const editIndex = messages.value.findIndex((m) => m.id === messageId);

  // 截断消息列表
  const cleanHistory = messages.value.slice(0, editIndex);
  messages.value.splice(editIndex, messages.value.length - editIndex);

  // 生成全新 thread_id
  const newThreadId = generateThreadId();
  const oldThreadId = props.threadId;

  // 迁移历史 + 通知父组件
  localStorage.setItem(
    `omni_messages_${newThreadId}`,
    JSON.stringify(cleanHistory),
  );
  localStorage.removeItem(`omni_messages_${oldThreadId}`);
  emit("update-session-id", oldThreadId, newThreadId);

  await handleSend(newContent);
};
```

### 第 4 步：修改 App.vue 支持线程 ID 更新

```typescript
const updateSessionId = (oldThreadId: string, newThreadId: string) => {
  const session = sessions.value.find((s) => s.id === oldThreadId);
  if (session) {
    session.id = newThreadId;
  }
  currentThreadId.value = newThreadId;
  saveToLocalStorage();
};
```

## 编辑后 Agent 的记忆边界

| 记忆状态    | 内容                                              |
| ----------- | ------------------------------------------------- |
| ✅ 记住的   | 截断点之前的所有对话历史                          |
| ❌ 忘记的   | 被编辑的那条旧消息，以及它之后的所有对话          |
| 🆕 新添加的 | 编辑后的新消息 + Agent 基于干净上下文产生的新回复 |

## 为什么后端和 Agent 不需要改动？

截断对话 → 前端删除数组元素（splice）

清除记忆 → 前端更换 thread_id（新 ID 在 SQLite 中无记录）

重启对话 → 复用已有的 handleSend 函数

## 编辑功能踩坑记录

| 序号 | 问题现象                    | 根本原因                                 | 解决方案                                       |
| ---- | --------------------------- | ---------------------------------------- | ---------------------------------------------- |
| 1    | 编辑按钮太丑、没辨识度      | 初始方案只有光秃秃图标                   | 参照 DeepSeek 风格，改为带文字和图标的悬浮按钮 |
| 2    | 编辑后 Agent 仍然记得旧消息 | thread_id 未更新，后端检查点仍保留旧状态 | 编辑后生成全新 thread_id，彻底换钥匙           |
| 3    | 侧边栏会话 ID 未更新        | 子组件换了 thread_id 但未通知父组件      | 通过 emit 通知 App.vue 调用 updateSessionId    |

## 与"暂停/中止"功能的对比

| 对比维度     | 暂停/中止                               | 编辑并重塑上下文                   |
| ------------ | --------------------------------------- | ---------------------------------- |
| 触发的操作   | 停止正在执行的 Agent 任务               | 截断历史、更换 thread_id、重发消息 |
| 对后端的影响 | 需要检测断连、取消 Agent 协程           | 完全不需要修改后端代码             |
| 核心实现位置 | 前后端都需修改                          | 仅前端修改                         |
| 关键机制     | AbortController + asyncio.Task.cancel() | splice() + generateThreadId()      |
| 难度         | 中高                                    | 中低                               |

# 十二、"双重回复" Bug 完整排查报告（核心问题）

## 问题现象

当用户提问涉及 RAG 知识库（如"我是谁呀"）时，流式输出会出现两段风格迥异的回复：

冷档案："你叫隗迦勒，哈尔滨人，在昆明读书..." —— 像在念档案

暖人设："你是隗迦勒呀！来自哈尔滨..." —— 带语气词和表情

非 RAG 问题（天气、普通聊天）完全正常。

## 完整排查时间线

| 阶段 | 尝试方案                                             | 失败原因                                              | 收获                                   |
| ---- | ---------------------------------------------------- | ----------------------------------------------------- | -------------------------------------- |
| 1    | executor.py 添加关键词过滤器                         | 摘要格式不固定，LLM 可能用自然语言输出                | 不是字符串过滤能解决的                 |
| 2    | 按 langgraph_node 节点名过滤                         | 节点名是框架内部动态生成的，冷文字的节点也是 "agent"  | 无法按节点区分                         |
| 3    | 过滤 tool_calls 和 ToolMessage                       | 冷文字不是以 ToolMessage 形式流出的                   | 定位更精准：是 LLM token，不是工具消息 |
| 4    | 给 SummarizationMiddleware 用 disable_streaming=True | 中间件本身不是问题根源                                | 排除中间件嫌疑                         |
| 5    | middleware.py 的 trigger 改为极大值 / 临时移除中间件 | 问题依然存在                                          | 彻底排除 SummarizationMiddleware       |
| 6    | 修改 System Prompt                                   | 约束的是 LLM 输出内容，但冷文字不是 LLM "故意"输出的  | 问题不在 Prompt 层                     |
| 7    | 修改 rag_tool 描述、rag.txt                          | 同上                                                  | 加固了排除结论                         |
| 8    | 移除 chain.py 的 print                               | print 不会混入 SSE 流                                 | 澄清了一个干扰项                       |
| 9    | 使用 stream_mode="updates" + subgraphs=True          | 前端完全无法输出 / 数据结构不匹配                     | updates 模式不适用当前架构             |
| 10   | 给模型打 tags=["internal-rag"] 并过滤                | 所有回复空白——标签无法区分"工具内部LLM"和"Agent主LLM" | 标签继承机制导致误伤                   |
| 11   | 最终方案：改造 rag_tool.py                           | —                                                     | ✅ 彻底解决                            |

## 病根：LangGraph 流式管道的"无差别拦截"

LangGraph 的 astream 在 stream_mode="messages" 模式下，会拦截整个图中所有 LLM 调用产生的 token。当 query_knowledge 工具内部通过 rag_chain 调用了一个 LLM 时，这个内部 LLM 生成的 token 就被流式管道强制推送到了前端。

这不是 Bug，而是 LangGraph 框架的设计特性。 冷文字的 langgraph_node 也是 "agent"，因为它在框架看来，就是 Agent 在"思考"过程中产生的中间输出。

## 最终解决方案

修改文件：agent_core/tools/rag_tool.py

核心改动：让 query_knowledge 工具不再调用 run_rag_chain（内部含 LLM），改为直接调用 retrieve，只返回检索到的文档原文。

```python
# 之前（会触发双重回复）
from agent_core.rag.chain import run_rag_chain
result = run_rag_chain(question)  # 内部有 LLM 调用
return result

# 之后（干净利落）
from agent_core.rag.retriever import retrieve
docs = retrieve(question)
return "\n\n".join(docs)  # 只返回原文，无 LLM 调用
```

工具返回纯文档文本后，Agent 会基于这些文档自己组织温暖回复，整个过程只有一个 LLM 调用，流式输出自然干净。

## 排查路线图

```text
问题表象（双重回复）
│
├── 表现层排查（无效）
│   ├── 关键词过滤 ✗
│   ├── System Prompt 约束 ✗
│   └── rag.txt / 工具描述修改 ✗
│
├── 中间件层排查（排除嫌疑）
│   ├── disable_streaming ✗
│   ├── trigger 极大值 ✗
│   └── 完全移除中间件 ✗
│
├── 代码层排查（排除干扰项）
│   ├── 移除 print → 澄清 print 不是病根
│   └── log_docs 改造 → 引出 logger 作用域问题，修复后问题依旧
│
├── 框架层排查（接近真相）
│   ├── stream_mode="updates" → 数据格式不兼容 ✗
│   ├── ToolMessage 过滤 → 冷文字不是 ToolMessage ✗
│   ├── tags 标签过滤 → 标签继承导致误伤 ✗
│   └── langgraph_node 过滤 → 节点名与 Agent 相同 ✗
│
└── ★ 病根确认 & 解决
    └── 改造 rag_tool.py，拆除内部 LLM 调用
          工具只返回检索文档原文 → ✅ 彻底解决
```

# 十三、“对话记忆 vs 知识库”边界混淆问题完整复盘

## 问题现象

当用户问及涉及自身的话题时，Agent 表现出三种错误行为：

| 用户输入           | 期望行为                  | 错误行为                        | 错误类型              |
| ------------------ | ------------------------- | ------------------------------- | --------------------- |
| “我是谁呀”         | 查知识库 → 用第三人称回答 | 用第一人称回答：“我是隗迦勒...” | 身份混淆              |
| “我刚才说了啥”     | 查对话记忆 → 直接回答     | 查知识库 → 返回静态个人信息     | 工具误调用            |
| “我都问了啥”       | 查对话记忆 → 总结         | 查知识库 → 返回不相关内容       | 工具误调用            |
| “我一共都说了些啥” | 查对话记忆 → 总结         | 查知识库 → 响应极慢（几十秒）   | 工具误调用 + 性能问题 |

最诡异的是：同一个问题（如“我刚才说了啥”），有时能正确回答，有时却调了 RAG。表现出间歇性失灵。

## 病根分析

### 核心矛盾

Agent 有两个信息来源：

- **对话记忆**（Checkpointer 持久化）→ 记住当前会话中发生了什么
- **知识库**（RAG 检索）→ 存储用户的静态个人信息

LLM 在决策“该用哪个”时，面对模糊的提问（如“我都跟你说了什么”），会倾向于调用工具——因为工具描述里有“当用户询问关于他/她自己的信息时”这句话。LLM 的推理是：“说了什么”可能也是在问“关于自己的信息”，所以查一下知识库更保险。

这就是 LLM 的工具调用偏好：宁可错杀，不可放过。

### 为什么会间歇性失灵？

LLM 的决策本质上是概率性的。同一个输入，不同时刻的推理路径可能不同：

- 有时 LLM 正确判断为“对话历史问题” → 不调工具 ✅
- 有时 LLM 误判为“个人信息问题” → 调了 RAG ❌

一旦在某一轮对话中调了 RAG，后续所有类似问题都会惯性走这条路（因为对话上下文里已经有了工具调用记录）

### 伴生问题：第一人称混淆

RAG 知识库里的文档是以“我”开头写的（如“我叫隗迦勒”）。Agent 拿到这些文档后，在生成回答时直接复述了第一人称，把自己当成了用户。

## 排查时间线

| 阶段 | 尝试方案                                               | 结果                   | 收获                         |
| ---- | ------------------------------------------------------ | ---------------------- | ---------------------------- |
| 1    | 修改 SYSTEM_PROMPT，增加“对话历史问题不要调工具”       | 部分有效，但间歇性失灵 | 软约束对 LLM 不可靠          |
| 2    | 修改 query_knowledge 工具描述，增加“不要调用的场景”    | 依然间歇性失灵         | 工具描述越长，LLM 越可能忽略 |
| 3    | 将工具重命名为 identify_user，职责收窄为仅回答“我是谁” | 基本解决               | 硬约束比软约束可靠           |
| 4    | 修改 SYSTEM_PROMPT 增加“身份归属”和“记忆忠实度”规则    | 改善第一人称问题       | Prompt 分层治理是有效手段    |
| 5    | 优化 RAG 检索性能（缓存 vector_store）                 | 解决响应慢             | 向量存储复用是性能关键       |

## 最终解决方案

### 工具职责窄化（治本）

核心思想：把模糊宽泛的工具定义，改造为精确狭窄的硬边界。

```python
# 之前（边界模糊，容易被误触发）
def query_knowledge(question: str) -> str:
    """当用户询问关于他/她自己的个人信息时，使用此工具..."""

# 之后（边界明确，只在特定场景触发）
def identify_user(question: str) -> str:
    """仅在用户明确询问关于其自身的基本身份信息时调用。
    调用示例：
    - "我是谁呀" → 调用
    - "你是谁" → 调用
    - "我刚才说了啥" → 不要调用
    - "我都问过你啥" → 不要调用
    """
```

### SYSTEM_PROMPT 分层治理（辅助）

在 SYSTEM_PROMPT 中增加了三层规则：

- **工具选择规则**：明确各工具的适用场景
- **身份归属规则**：用“你是XXX”而非“我是XXX”
- **记忆忠实度规则**：回忆时还原用户原话，不自行翻译

### RAG 性能优化（辅修）

将 vector_store 缓存为模块级变量，避免每次检索都重新加载 Chroma 索引。

## 核心方法论：提示词工程的“软硬边界”原则

这次排查最大的收获，是总结出一条提示词工程的核心原则：

当 LLM 在模糊边界上反复出错时，不断追加“不要做X”的软约束是低效的。最有效的方法是重新设计工具的边界，让它在根本不可能被误触发。

| 方法     | 描述                           | 可靠性                       |
| -------- | ------------------------------ | ---------------------------- |
| 软约束   | 在 Prompt 中说“不要做X”        | 低（LLM 可能忽略）           |
| 硬边界   | 重新定义工具职责，缩小适用范围 | 高（LLM 没有机会犯错）       |
| 示例锚定 | 在工具描述中给出正面和反面示例 | 中高（通过具体例子引导决策） |

## 本次修复涉及的文件

| 文件                         | 改动内容                                               |
| ---------------------------- | ------------------------------------------------------ |
| agent_core/tools/rag_tool.py | 重命名 query_knowledge → identify_user，窄化 docstring |
| agent_core/tools/**init**.py | 更新导出名称                                           |
| agent_core/agent/config.py   | 更新 SYSTEM_PROMPT 中的工具名和规则                    |
| agent_core/rag/retriever.py  | 缓存 vector_store 实例（性能优化）                     |

## 遗留的小瑕疵（属于 LLM 天然局限，不值得修）

Agent 在回忆“用户总共说过啥”时，偶尔会把自己生成的回复内容也列入用户说过的话。这是因为 LLM 在长对话记忆中存在模糊性，无法精确区分“这句话是谁说的”。这个问题无法通过 Prompt 根治，而且在实际使用场景中不常见，建议接受。

# 十四、项目功能总览

| 功能           | 状态 | 说明                                          |
| -------------- | ---- | --------------------------------------------- |
| 自动工具调用   | ✅   | 模型根据用户输入自动决定是否调用工具          |
| 知识检索 (RAG) | ✅   | Chroma + DashScope Embedding + MMR 多样性检索 |
| 流式打字机输出 | ✅   | 逐字显示，50ms/字                             |
| 暂停/中止回复  | ✅   | 前后端协同，双重保险                          |
| 多轮对话记忆   | ✅   | AsyncSqliteSaver + 前端本地存储               |
| 会话管理       | ✅   | 新建/切换/清空，侧边栏管理                    |
| 编辑已发送消息 | ✅   | 截断历史 + 新 thread_id + 重塑上下文          |
| 时间工具       | ✅   | get_current_time                              |
| 天气工具       | ✅   | 高德 API，带缓存，支持多城市                  |

# 十五、后续改进方向

进一步优化 Agent 的系统提示和工具使用策略

测试更复杂的对话场景，确保 Agent 能够正确处理各种情况

添加更多工具，扩展 Agent 的功能（如邮件、待办事项、新闻等）

优化性能，提高响应速度

部署到云服务器

优化移动端适配
