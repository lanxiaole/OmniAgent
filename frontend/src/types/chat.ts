// chat.ts - 聊天相关类型定义
// 定义消息结构、工具调用、思考过程等核心数据模型

export interface ChatRequest {
  message: string;
  thread_id: string;
}

export interface ChatResponse {
  reply: string;
}

// =============== 工具调用相关 ===============

/** 工具调用状态 */
export type ToolCallStatus = 'pending' | 'running' | 'success' | 'error';

/** 工具分类（用于显示图标和主题色） */
export type ToolCategory =
  | 'web' // 联网搜索 / 浏览器
  | 'file' // 文件系统
  | 'code' // 代码执行
  | 'knowledge' // 知识库 / 检索
  | 'memory' // 记忆 / 长期记忆
  | 'system' // 系统 / 天气等
  | 'other';

/** 工具执行错误对象（结构化错误信息，比纯字符串更清晰） */
export interface ToolCallError {
  /** 错误类型，如 ZeroDivisionError / TimeoutError */
  type?: string;
  /** 用户可读的错误摘要 */
  message: string;
  /** 完整堆栈（可选） */
  stack?: string;
}

/** 工具调用信息
 *  - 所有字段都以"前端展示友好"为第一原则设计
 *  - args / result 保留 unknown 类型：真实对接后端时可能是 JSON 字符串，
 *    也可能是已解析对象，由 ToolCallCard 组件内部统一归一化。
 */
export interface ToolCall {
  /** 工具调用唯一 ID */
  id: string;
  /** 工具内部名（如 search_web / get_weather） */
  name: string;
  /** 工具展示名（用户可读，如「联网搜索」「查询天气」），可选，缺省时用 name */
  displayName?: string;
  /** 工具分类（用于主题色 + 图标） */
  category?: ToolCategory;
  /** 工具调用参数：字符串或结构化对象均可 */
  args: unknown;
  /** 工具执行结果：字符串或结构化对象均可 */
  result?: unknown;
  /** 执行状态 */
  status: ToolCallStatus;
  /** 错误详情（status=error 时使用） */
  error?: ToolCallError;
  /** 兼容旧字段：纯字符串错误信息 */
  errorMsg?: string;
  /** 开始执行时间戳（ms） */
  startedAt?: number;
  /** 结束执行时间戳（ms） */
  finishedAt?: number;
  /** 耗时 ms（缺省时可由 started/finished 推导） */
  durationMs?: number;
}

// =============== 思考过程相关 ===============

/** 单个思考步骤
 *  - 一条助手消息可能对应多步思考（推理 → 选工具 → 读结果 → 组织语言 …）
 */
export interface ReasoningStep {
  /** 步骤 ID（缺省时可用数组索引作为 key） */
  id?: string;
  /** 思考文本（纯文本 / Markdown） */
  text: string;
  /** 本步思考耗时（毫秒） */
  thinkingMs?: number;
  /** 思考发生时间戳（用于调试/排序） */
  ts?: number;
}

// =============== 消息相关 ===============

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system';

/** 消息主体
 *  所有新增字段都标记为可选：保证与旧代码 / 旧存储数据的兼容性。
 */
export interface Message {
  id: string;
  role: MessageRole;
  /** 消息正文（助手回复可能是 Markdown） */
  content: string;

  /** 思考过程 / 思维链（多步），也兼容过去的字符串形式 */
  reasoning?: ReasoningStep[] | string;
  /** 思考过程是否默认展开（控制 ReasoningBlock 初始状态） */
  reasoningOpen?: boolean;

  /** 本轮助手调用的工具列表（按调用顺序） */
  toolCalls?: ToolCall[];

  /** 消息创建时间戳（ms） */
  createdAt?: number;
}

export interface HistoryResponse {
  messages: Message[];
}
