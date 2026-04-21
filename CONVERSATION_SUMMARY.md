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
