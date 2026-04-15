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
- 修改 tools/__init__.py，只导出 TOOLS = [get_current_time]

### 2. Agent 执行器重构

- 创建 agent/executor.py 文件，实现基于 create_agent 的 Agent 执行器
- 使用 create_agent(model=model, tools=TOOLS, system_prompt=...) 创建 Agent
- 更新 run_agent() 函数，使用正确的参数格式调用 Agent
- 移除手动的对话历史管理，使用 LangChain 内置的记忆功能

### 3. 主程序简化

- 删除 build_enhanced_message 函数
- 直接调用 run_agent(user_input, thread_id)
- 删除所有手动的 memory.add_* 调用

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
