# OmniAgent 项目开发总结

## 项目背景

OmniAgent 是一个基于 LangChain 框架开发的智能助手项目，旨在实现自动工具调用和知识检索功能。

## 开发过程

### 1. 项目初始化

- 创建项目目录结构
- 初始化 Git 仓库
- 创建 .env 文件存储 API Key
- 创建 .gitignore 文件
- 创建 requirements.txt 文件

### 2. 模块开发

#### 2.1 模型模块

- 创建 model/client.py 文件，实现与大模型的交互
- 使用 ChatOpenAI 模型实例，设置为 qwen3-max
- 实现 chat() 函数，用于与模型对话

#### 2.2 记忆模块

- 创建 memory/manager.py 文件，实现对话历史管理
- 实现 add_user_message()、add_ai_message()、get_messages() 等函数

#### 2.3 工具模块

- 创建 tools/time_tool.py 文件，实现时间工具
- 使用 @tool 装饰器定义 get_current_time() 函数
- 实现 maybe_use_tool() 函数，用于关键词匹配触发工具

#### 2.4 RAG 模块

- 创建 rag/builder.py 文件，实现向量库构建功能
- 创建 rag/retriever.py 文件，实现知识检索功能
- 实现 load_documents()、build_vector_store()、retrieve() 等函数
- 添加基于 MD5 的自动增量构建功能

#### 2.5 日志模块

- 创建 logger/setup.py 文件，实现统一的日志系统
- 配置控制台和文件日志处理器

### 3. 主程序开发

- 创建 main.py 文件，实现主对话循环
- 实现 build_enhanced_message() 函数，用于构建增强消息
- 集成模型、记忆、工具和 RAG 模块

### 4. 测试模块

- 创建 tests/test_all.py 文件，实现单元测试
- 测试模型调用、记忆模块、工具触发、RAG 检索和集成流程

## 重构为 LangChain 1.0

### 1. 工具模块重构

- 删除 maybe_use_tool() 函数和 TIME_TOOL_KEYWORDS
- 只保留 @tool 装饰的 get_current_time 函数
- 修改 tools/**init**.py，只导出 TOOLS = [get_current_time]

### 2. Agent 执行器重构

- 创建 agent/executor.py 文件，实现基于 create_agent 的 Agent 执行器
- 使用 create_agent(model=model, tools=TOOLS, system_prompt=...) 创建 Agent
- 更新 run_agent() 函数，使用正确的参数格式调用 Agent
- 移除手动的对话历史管理，使用 LangChain 内置的记忆功能

### 3. 主程序简化

- 删除 build_enhanced_message 函数
- 直接调用 run_agent(user_input, thread_id)
- 删除所有手动的 memory.add\_\* 调用

### 4. 测试模块更新

- 更新测试函数以适应新的 LangChain 1.0 结构
- 移除对 model 和 memory 模块的测试
- 更新 test_tools 函数，测试工具的结构是否正确
- 更新 test_integration 函数，使用新的 run_agent 函数

## 遇到的问题及解决方法

### 1. 依赖缺失

- 问题：ModuleNotFoundError: No module named 'langchain_community'
- 解决方法：在 requirements.txt 中添加 langchain-community 依赖

### 2. 日志编码错误

- 问题：UnicodeEncodeError: 'gbk' codec can't encode character
- 解决方法：在 logger.py 的 RotatingFileHandler 中添加 encoding="utf-8" 参数

### 3. 工具调用方式不匹配

- 问题：从手动关键词匹配切换到 LangChain 自动工具调用时，代码结构不匹配
- 解决方法：重构工具模块和 Agent 执行器，使用 LangChain 1.0 的标准写法

### 4. 测试函数不兼容

- 问题：旧的测试函数不适应新的 LangChain 1.0 结构
- 解决方法：更新测试函数，移除对旧模块的依赖，使用新的 Agent 执行器

## 最终成果

### 项目结构

```
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

### 功能实现

- ✅ 自动工具调用：模型会根据用户输入自动决定是否调用工具
- ✅ 知识检索：使用 RAG 技术从知识库中检索相关信息
- ✅ 对话记忆：使用 LangChain 内置的记忆功能，保存对话历史
- ✅ 日志系统：统一的日志系统，便于调试和监控
- ✅ 测试覆盖：单元测试覆盖工具、RAG 和集成流程

## 后续改进

1. 将 RAG 检索功能包装成 @tool，以便 Agent 可以自动使用它
2. 进一步优化 Agent 的系统提示和工具使用策略
3. 测试更复杂的对话场景，确保 Agent 能够正确处理各种情况
4. 添加更多工具，扩展 Agent 的功能
5. 优化性能，提高响应速度

一、先回忆一下之前的问题
你问“我叫什么名字”时，普通相似度检索（similarity_search）返回的第一个文档是：

“我性格内向但情商高，能一眼看穿别人。我有孤独的能力，但也渴望被接住。”

而不是：

“我叫隗迦勒，哈尔滨人，现在在昆明读书...”

为什么？
因为向量检索计算的是语义相似度。“我叫什么名字”这个问句，在向量空间里，可能和“性格内向、能看穿别人”这种自我描述的句子距离更近（都是关于“我”的抽象特征），而和“我叫隗迦勒”这种具体事实句子的距离反而稍远。模型觉得“描述性格”比“报名字”更贴近“我叫什么”的意图——这其实是 Embedding 模型的一个常见偏差。

二、MMR 做了什么？
MMR = Maximum Marginal Relevance（最大边际相关性）
它的核心思想是：在保证相关性的前提下，让选出来的文档彼此尽可能不同。

公式简化理解：

text
最终分数 = λ × 相关性 - (1-λ) × 与已选文档的相似度
λ 控制“相关性”和“多样性”的权重（通常 0.5~0.7）。

第一次选最相关的文档（可能还是“性格内向”那条）。

第二次选的时候，会惩罚那些和“性格内向”太像的文档，于是“名字”那条因为和它不相似，反而得分上升。

第三次继续惩罚重复内容。

所以即使“性格内向”那条相关性略高，MMR 也会强制引入不同主题的文档，最终你看到的排序可能是：

名字（因为独特）

性格

感冒流程

而普通相似度检索只会傻傻地按相似度排序，不会主动去“挖掘”不同信息。

三、为什么之前 top_k=1 时完全没救？
因为只取第一条，MMR 也救不了——它只能在 k>1 时发挥作用。你把 top_k 从 1 改成 3，给了 MMR 选择空间。
然后 MMR 在三条里挑了一条最相关且不重复的，最终把“名字”那条排到了第一。

四、你现在可以做的进一步优化
保持 MMR + top_k=3~5，这是非常稳健的配置。

可以调整 λ 值（在 as_retriever 中加 lambda_mult 参数，默认 0.5）：

如果你更看重相关性（不怕重复），设 lambda_mult=0.7

如果你更看重多样性（想覆盖不同方面），设 lambda_mult=0.3

如果某些问题仍然检索不准，可以尝试把知识库每行前面加上类型标签，比如：

text
[名字] 我叫隗迦勒，哈尔滨人...
[性格] 我性格内向但情商高...
[技术] 我学过 LangChain 1.0...
这样检索时标签本身会帮助区分。

总结：你之前困扰了几个小时的问题，本质是普通相似度检索的“趋同”缺陷，MMR 通过强制多样性解决了它。这不是玄学，是经典的检索技术。

### 二、完成的主要内容

1. 安装依赖 ：
   - 安装了 langgraph-checkpoint-sqlite 和 deepagents 两个依赖包
   - 用于实现对话状态持久化和自动上下文总结

2. 重构 Agent 核心代码 ：
   - 将 agent_core/agent/executor.py 拆分为多个职责单一的文件
   - 创建了 config.py 、 checkpointer.py 、 model_factory.py 、 middleware.py 等模块
   - 实现了模块化的代码结构，提高了代码的可维护性

3. 实现对话状态持久化 ：
   - 使用 SqliteSaver 实现对话状态的持久化存储
   - 数据库文件存储在 agent_core/data/agent_checkpoints.db
   - 自动创建数据目录（如果不存在）
   - 调用 checkpointer.setup() 初始化数据库

4. 实现自动上下文总结 ：
   - 使用 SummarizationMiddleware 实现自动上下文总结
   - 配置 trigger=("messages", 10) （当消息数达到10条时触发总结）
   - 配置 keep=("messages", 5) （保留最近5条消息）
   - 使用与主模型相同的模型进行总结

5. 更新后端 API ：
   - 更新了 schemas/chat.py ，确保包含 thread_id 字段
   - 更新了 services/agent_service.py ，实现了 get_agent_reply 和 clear_session 函数
   - 更新了 controllers/chat_controller.py ，处理聊天请求并返回回复
   - 更新了 routers/chat.py ，添加了清空会话的接口

6. 更新 .gitignore ：
   - 添加了 agent_core/data/\*.db 忽略规则
   - 避免将数据库文件提交到 Git 仓库

### 三、遇到的困难及解决方法

1. Checkpointer 初始化错误 ：
   - 问题 ：最初使用 SqliteSaver.from_conn_string 初始化 Checkpointer 时，出现了类型错误
   - 解决方法 ：改为使用 sqlite3.connect 创建连接，传递 check_same_thread=False 参数，然后创建 SqliteSaver 实例并调用 setup() 方法

2. 模型提供者识别错误 ：
   - 问题 ：在创建 SummarizationMiddleware 时，直接使用模型名称 qwen3-max 导致 LangChain 无法识别模型提供者
   - 解决方法 ：改为使用 get_summarizer_model 函数获取总结模型实例，避免了直接使用模型名称的问题

3. 函数名冲突 ：
   - 问题 ：在 services/agent_service.py 中， clear_session 函数名与导入的 clear_session 函数名冲突
   - 解决方法 ：将导入的 clear_session 重命名为 agent_clear_session ，避免了函数名冲突

4. 会话管理问题 ：
   - 问题 ：最初使用手动管理 \_sessions 字典的方式，代码冗余且容易出错
   - 解决方法 ：改为使用 LangChain 官方推荐的 RunnableConfig 方式，通过 thread_id 实现会话隔离和持久化

### 四、具体实现步骤

1. 配置 Checkpointer ：

   ```
   # 创建 SQLite 连接
   conn = sqlite3.connect(str
   (DB_PATH), 
   check_same_thread=False)

   # 创建 SqliteSaver 实例
   checkpointer = SqliteSaver(conn)
   checkpointer.setup()
   ```

2. 配置 Middleware ：

   ```
   # 获取总结模型
   summarizer_model = 
   get_summarizer_model()

   # 创建 SummarizationMiddleware 实
   例
   summarization_middleware = 
   SummarizationMiddleware(
       model=summarizer_model,
       trigger=("messages", 10),  # 
       当消息数达到10条时触发总结
       keep=("messages", 5),      # 
       保留最近5条消息
   )
   ```

3. 创建 Agent ：

   ```
   # 创建 Agent
   agent = create_agent(
       model=model,
       tools=TOOLS,
       system_prompt=SYSTEM_PROMPT,
       checkpointer=checkpointer,
       middleware=middlewares,
   )
   ```

4. 调用 Agent ：

   ```
   # 构造 RunnableConfig
   config = RunnableConfig
   (configurable={"thread_id": 
   thread_id})

   # 调用 Agent
   result = global_agent_executor.
   invoke(
       {"messages": [{"role": 
       "user", "content": 
       user_input}]},
       config=config
   )
   ```

5. 清空会话 ：

   ```
   # 清空指定会话的 checkpoint
   checkpointer.delete_thread
   (thread_id)
   ```

OmniAgent 流式输出功能完整实现总结
一、背景与目标
问题：用户发送消息后，需要等待 Agent 完整生成全部回复内容，前端才能一次性渲染，等待时间长、体验差（“白屏等待”）。

目标：实现类似 ChatGPT 的“打字机效果”——Agent 每生成一个字/词（token），前端即时显示，让用户感知到“AI 正在实时思考并回复”。

核心挑战：

LangChain 1.0 Agent（底层是 LangGraph）的流式输出格式与同步调用完全不同。

框架内部的“中间件”（如 SummarizationMiddleware）会产生干扰流。

异步流式链路需要全栈打通：Agent → Service → Router → 前端。

技术栈：

后端框架: FastAPI

AI 框架: LangChain 1.0 (LangGraph)

LLM: Qwen3-Max (via DashScope API)

会话持久化: SQLite (AsyncSqliteSaver)

前端: Vue 3 + TypeScript

二、架构总览
text
用户浏览器 (Vue3)
│
▼ fetch (SSE 流)
FastAPI Router (/api/chat/stream)
│
▼ StreamingResponse
Service 层 (agent_service.py)
│
▼ 解包 (token, metadata)
Agent 核心层 (executor.py)
│
▼ agent.astream(stream_mode="messages")
LangGraph Agent (create_agent)
├── ChatOpenAI (qwen3-max)
├── AsyncSqliteSaver (多轮记忆)
├── SummarizationMiddleware (长对话压缩)
└── Tools (时间/天气/RAG)
关键决策：

为什么用 fetch 而不是 EventSource：EventSource 仅支持 GET 请求，无法发送请求体；我们需要 POST 来传递 message 和 thread_id，所以选择 fetch + ReadableStream 方案。

为什么 AsyncSqliteSaver 而不是 SqliteSaver：同步版本不支持异步流式调用，会导致 await agent.astream() 报错或阻塞事件循环。

三、各层实现详解

1. Agent 核心层 (agent_core/agent/executor.py)
   改动点：新增 stream_agent 异步生成器函数，替代原有的同步 run_agent。

python
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

核心技术点：

stream_mode="messages": LangGraph 提供了三种流式模式，这个模式专门用于输出 LLM 生成的 token 流。

返回值是元组 (token, metadata): 这是我们踩的第一个大坑。同步 invoke() 返回完整消息对象，但 astream() 每次产出的是一个 (AIMessageChunk, dict) 元组，其中第一个元素才是包含 .content 的消息块。

2. 内部干扰过滤（关键踩坑）
   问题：流式输出中混入了 SummarizationMiddleware 调用模型生成对话摘要时产生的 token（如 "## SESSION INTENT"、"## SUMMARY" 等）。

解决方案：在 stream_agent 中添加过滤逻辑：

python
async def filtered_stream():
async for chunk in raw_stream:
token, metadata = chunk
if not isinstance(token, AIMessageChunk): # 只处理 AIMessageChunk
continue
if not token.content: # 跳过空 token
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

核心思路：通过检查 metadata["langgraph_node"] 判断 token 来源，再结合关键词匹配，精准拦截中间件产生的内部输出。

3. Checkpointer 异步改造 (agent_core/agent/checkpointer.py)
   python
   from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def get_async_checkpointer():
conn = await aiosqlite.connect(str(DB_PATH))
checkpointer = AsyncSqliteSaver(conn)
await checkpointer.setup()
return checkpointer
为什么必须改：

同步 SqliteSaver 的 invoke() 可用，但其内部某些操作（如 get_tuple、put）在异步上下文中会阻塞事件循环。

LangGraph 官方提供了 AsyncSqliteSaver，与 astream 完全兼容。

4. 服务层 (backend/services/agent_service.py)
   职责：极简转发，只做调用传递。

python
async def stream_agent_reply(message: str, thread_id: str) -> AsyncGenerator[str, None]:
from agent_core.agent.executor import stream_agent
async for token in stream_agent(message, thread_id):
yield token
设计原则：保持薄层。核心过滤逻辑已经在 Agent 层处理完成，Service 层不需要重复处理。

5. 路由层 (backend/routers/chat.py)
   职责：使用 FastAPI 的 StreamingResponse 将 token 封装为 SSE 格式。

python
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

SSE 格式要求：

每条消息以 data: 开头

每条消息以 \n\n 结尾

[DONE] 是流结束的约定标记

6. 前端 API 层 (frontend/src/api/chat.ts)
   关键决策：放弃 axios，使用原生 fetch + ReadableStream。

typescript
export const sendMessageStream = async (
message: string, threadId: string,
onToken: (token: string) => void
): Promise<void> => {
const response = await fetch('/api/chat/stream', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ message, thread_id: threadId }),
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
const { done, value } = await reader.read();
if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        const token = JSON.parse(data);
        if (token === '[DONE]') return;
        onToken(token);
      }
    }

}
};
为什么 axios 不行？: axios 的 responseType: 'stream' 在某些版本/环境下不完全支持 ReadableStream，且 API 不够底层，无法精确控制流式处理。

7. 前端组件层 (ChatContainer.vue)
   typescript
   const handleSend = async (userMessage: string) => {
   // 1. 立即显示用户消息
   messages.value.push({ role: 'user', content: userMessage });

// 2. 添加空的助手消息占位
const assistantIndex = messages.value.length;
messages.value.push({ role: 'assistant', content: '' });

// 3. 流式接收，逐字追加
await sendMessageStream(userMessage, props.threadId, (token: string) => {
messages.value[assistantIndex].content += token;
saveLocalHistory(props.threadId, messages.value);
scrollToBottom();
});
};
核心技巧：先插入一个 content: '' 的空消息占位，然后不断 += token，Vue 响应式系统自动驱动视图更新，实现打字机效果。

四、踩坑全集
序号 问题现象 根本原因 解决方案
1 Runnable object has no attribute 'astream' 全局 Agent 实例类型不对 确保使用 create_agent 返回的 LangGraph 图对象
2 流式输出混杂 "## SESSION INTENT" 等 SummarizationMiddleware 的 token 被捕获 通过 metadata["langgraph_node"] 过滤
3 Agent 层正常，但 curl 收不到流 Service 层解包元组有误 将 token, metadata = chunk 解包逻辑移到 Service 层或保证 Agent 层正确 yield
4 前端 fetch 报错 "body.getReader is not a function" 使用了 axios，不支持 ReadableStream 改用原生 fetch
5 切换会话后消息混乱 前端 threadId 未正确传递 检查 sendMessageStream 的 threadId 参数来源
