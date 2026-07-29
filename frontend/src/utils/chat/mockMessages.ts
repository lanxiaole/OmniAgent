// chat/mockMessages.ts
// —— Phase 2-A UI 演示用模拟消息 ——
// 仅用于前端 UI 联调阶段：当会话没有任何历史消息时，
// 注入一组包含 Markdown、思考过程、工具调用的演示消息，
// 方便视觉校验 MessageItem / ReasoningBlock / ToolCallCard 的呈现。
// 接入真实数据后本文件可移除（亦可保留作为回归样例）。

import type { Message, ToolCall, ToolCallStatus } from '@/types/chat';

const ID = (prefix = 'mock_') =>
  `${prefix}${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

/** 模拟工具调用结果 —— get_weather 示例 */
const mockWeatherTool: ToolCall = {
  id: ID('tc_'),
  name: 'get_weather',
  displayName: '查询天气',
  category: 'system',
  status: 'success' as ToolCallStatus,
  args: { city: '北京', date: '今天' },
  result: {
    ok: true,
    city: '北京市',
    condition: '多云转晴',
    temperatureC: 22,
    humidity: '45%',
    wind: '东北风 3 级',
    aqi: 62,
    aqiLevel: '良',
  },
  startedAt: Date.now() - 1000 * 60 * 8,
  finishedAt: Date.now() - 1000 * 60 * 7,
  durationMs: 520,
};

/** 模拟工具调用 —— search_web 示例 */
const mockSearchTool: ToolCall = {
  id: ID('tc_'),
  name: 'search_web',
  displayName: '联网搜索',
  category: 'web',
  status: 'success' as ToolCallStatus,
  args: { query: 'Vue 3.5 新特性', max_results: 5 },
  result: {
    results: [
      {
        title: 'Vue 3.5 正式发布',
        url: 'https://blog.vuejs.org/posts/vue-3-5',
        snippet: 'Vue 3.5 "Hoa Sen" 带来了响应式系统的性能改进：defer、useTemplateRef、改进的 Provide/Inject 类型等新能力…',
      },
      {
        title: 'Vue 3.5 迁移指南',
        url: 'https://vuejs.org/guide/migration.html',
        snippet: 'Vue 3.5 中一些新的组合式 API 让我们可以在模板中直接使用顶层 ref，而无需 .value…',
      },
    ],
  },
  startedAt: Date.now() - 1000 * 60 * 6,
  finishedAt: Date.now() - 1000 * 60 * 5,
  durationMs: 1380,
};

/** 模拟工具调用 —— execute_python 示例（带错误） */
const mockCodeToolError: ToolCall = {
  id: ID('tc_'),
  name: 'execute_python',
  displayName: '执行 Python 代码',
  category: 'code',
  status: 'error' as ToolCallStatus,
  args: {
    code: 'print("Hello, OmniAgent!")\nprint(1/0)',
    timeout: 30,
  },
  error: {
    type: 'ZeroDivisionError',
    message: 'division by zero',
    stack:
      'Traceback (most recent call last):\n  File "<string>", line 2, in <module>\n    print(1/0)\nZeroDivisionError: division by zero',
  },
  startedAt: Date.now() - 1000 * 60 * 4,
  finishedAt: Date.now() - 1000 * 60 * 3.5,
  durationMs: 340,
};

/** 思考过程示例 */
const mockReasoning = [
  {
    id: ID('rs_'),
    text: '用户想了解「Vue 3.5 新特性」以及今天北京的天气。我先拆解一下需求：\n1. Vue 3.5 是框架知识，虽然我有训练数据，但为了保证最新，我应该先联网搜索官方博客。\n2. 天气属于实时数据，必须调用 get_weather 工具，而不能凭记忆回答。\n3. 为了并行效率，我会先同时触发两个工具，拿到结果后再组织语言。',
    thinkingMs: 1600,
  },
  {
    id: ID('rs_'),
    text: '搜索结果已经拿到：Vue 3.5 带来了响应式性能优化、useTemplateRef、Provide/Inject 类型增强。天气数据也正常，北京今天多云转晴 22°C。\n\n接下来我需要把这些信息整理成自然语言，顺带给一份 Vue 3.5 的代码示例。不过我想写个小代码片段演示效果 —— 先执行一个 Python 打印看看。',
    thinkingMs: 2300,
  },
  {
    id: ID('rs_'),
    text: '哎呀，Python 代码报了 ZeroDivisionError。这个是故意的演示错误：我需要告诉用户哪里错了，并且给出修正后的代码，让用户对"Agent 也会犯错并自我修正"有直观感知。',
    thinkingMs: 1200,
  },
];

/** Markdown 示例回复（带代码块） */
const demoReplyMd = `
### 🌤️ 北京今日天气（实时数据）

> 数据来源：实时天气接口 · 更新于 ${new Date().toLocaleTimeString('zh-CN', { hour12: false })}

| 项目 | 数值 |
| --- | --- |
| 天气现象 | **多云转晴** |
| 温度 | 22 °C |
| 湿度 | 45% |
| 风力 | 东北风 3 级 |
| 空气质量 | AQI 62（**良**） |

---

### 🚀 Vue 3.5 "Hoa Sen" 新特性速递

根据刚刚的联网搜索结果，Vue 3.5 有几个值得关注的变化：

1. **响应式性能优化** — 深层响应式开销降低了约 **56%**（官方数据）
2. **\`useTemplateRef()\`** — 新的组合式 API，替代模板 ref 的类型安全访问
3. **Provide / Inject 类型增强** — 端到端的类型推断，无需手动泛型
4. **\`defineModel()\` 稳定版** — 双向绑定更简洁

下面是一个使用 \`useTemplateRef\` 的小例子：

\`\`\`vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue';

// Vue 3.5+：不再需要 .value 判断 null 的繁琐写法
const inputRef = useTemplateRef<HTMLInputElement>('myInput');

onMounted(() => {
  // 类型安全：inputRef.value 自动是 HTMLInputElement | null
  inputRef.value?.focus();
});
</script>

<template>
  <input ref="myInput" placeholder="组件挂载后自动聚焦" />
</template>
\`\`\`

### ⚠️ 顺便汇报一次小插曲

我刚才尝试用一段 Python 演示代码时触发了一个**除零错误**：

\`\`\`python
# 修正后的代码
print("Hello, OmniAgent!")
# print(1 / 0)  # 除零，错误
print("All good 🎉")
\`\`\`

如果还有其他想了解的，随时告诉我 👋
`.trim();

/** 生成一段欢迎 + 演示对话（用于 UI 联调） */
export function buildMockWelcomeMessages(): Message[] {
  const now = Date.now();
  const t = (offsetMin: number) => now - offsetMin * 60 * 1000;

  return [
    // 欢迎消息（简洁、无思考/工具，普通文本）
    {
      id: ID('msg_'),
      role: 'assistant',
      content:
        '你好！我是 **OmniAgent**，一个具备工具调用能力、思考过程透明的智能助手。👇 下面是一条演示对话，你可以直观看到新的 UI：',
      createdAt: t(12),
    },

    // 用户提问
    {
      id: ID('msg_'),
      role: 'user',
      content: '帮我看看 Vue 3.5 有什么新特性，顺便查查北京今天天气怎么样？',
      createdAt: t(10),
    },

    // 助手回答：带思考过程 + 多个工具调用 + Markdown 代码块
    {
      id: ID('msg_'),
      role: 'assistant',
      content: demoReplyMd,
      reasoning: mockReasoning,
      toolCalls: [mockWeatherTool, mockSearchTool, mockCodeToolError],
      createdAt: t(5),
    },
  ];
}
