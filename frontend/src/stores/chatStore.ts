// chatStore.ts - 聊天消息状态管理
// 使用 Pinia Composition API 风格管理消息列表、加载状态、打字机效果等
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { sendMessageStream, fetchHistory } from '@/api/chat';
import type { HistoryMessage, ApprovalRequest } from '@/api/chat';
import type { Message, ReasoningStep, ToolCall } from '@/types/chat';
import { storage, STORAGE_KEYS } from '@/utils/storage';
import { useSessionStore } from '@/stores/sessionStore';
// 打字机速度：每个字符之间的间隔毫秒数
const TYPING_SPEED = 20;

/**
 * 生成唯一的消息 ID
 * 格式：msg_时间戳_随机字符串
 */
const generateMessageId = () => {
  return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10);
};

/**
 * 聊天 Store：管理消息列表、流式发送、打字机效果、历史保存
 */
export const useChatStore = defineStore('chat', () => {
  // 当前会话的消息列表
  const messages = ref<Message[]>([]);
  // 是否正在发送消息（用于禁用输入框和显示加载状态）
  const loading = ref(false);
  // 中止控制器，用于取消正在进行的流式请求
  const abortController = ref<AbortController | null>(null);
  // 当前待审批的请求（为 null 时表示无待审批项）
  const pendingApproval = ref<ApprovalRequest | null>(null);
  // 上下文压缩状态：'idle' | 'compressing' | 'done'
  const compressingStatus = ref<'idle' | 'compressing' | 'done'>('idle');
  // 压缩状态最小展示时长：避免压缩太快导致提示"一闪而过"看不到
  const MIN_COMPRESSING_MS = 800;  // "正在压缩上下文..." 至少展示时长
  const MIN_DONE_MS = 800;         // "压缩完毕" 至少展示时长
  // 记录压缩开始时间，用于补齐最小展示时长
  let compressingStartTime = 0;

  // 当前会话是否有消息（用于启动页/对话页切换判断）
  const hasMessages = computed(() => messages.value.length > 0);

  // 打字机队列：存放待显示的字符
  const typewriterQueue = ref<string[]>([]);
  // 打字机定时器引用
  let typewriterTimer: ReturnType<typeof setInterval> | null = null;

  /**
   * 从本地存储加载指定会话的历史消息
   */
  const loadLocalHistory = (threadId: string): Message[] => {
    try {
      const key = STORAGE_KEYS.MESSAGES(threadId);
      return storage.get<Message[]>(key, []);
    } catch (error) {
      console.error('加载本地历史消息失败:', error);
      return [];
    }
  };

  /**
   * 将当前消息列表保存到本地存储
   */
  const saveLocalHistory = (threadId: string, msgs: Message[]) => {
    const key = STORAGE_KEYS.MESSAGES(threadId);
    storage.set(key, msgs);
  };

  /**
   * 加载指定会话的历史消息并显示
   * 优先级：后端（权威数据源） > localStorage（本地缓存降级） > 保持空状态
   *
   * 注意：调用方应确保在切换会话时先保存当前消息并清空，
   * 避免 loadHistory 覆盖正在流式传输的内容。
   * loadHistory 只负责加载指定 threadId 的历史消息。
   */
  const loadHistory = async (threadId: string) => {
    const msgCountBefore = messages.value.length;

    try {
      // 1. 优先从后端加载（权威数据源，现在返回完整 reasoning + toolCalls）
      const backendMessages: HistoryMessage[] = await fetchHistory(threadId);

      // 双重检查：在 fetch 期间已有新消息加入，跳过覆盖
      if (messages.value.length !== msgCountBefore) return;

      if (backendMessages.length > 0) {
        const msgs: Message[] = backendMessages.map(m => ({
          id: generateMessageId(),
          role: m.role as 'user' | 'assistant' | 'system',
          content: m.content,
          isSummaryNotice: m.isSummaryNotice,
          summaryData: m.summaryData,
          reasoning: m.reasoning,
          toolCalls: m.toolCalls?.map(tc => ({
            id: tc.id,
            name: tc.name,
            args: tc.args,
            result: tc.result,
            // 规范化 status：后端使用 "success"/"running"，兼容旧数据 "done"
            status: (tc.status === 'done' ? 'success' : tc.status) as ToolCall['status'],
            // 以下字段后端不返回，由前端流式过程动态生成
            // displayName / category / startedAt / finishedAt / durationMs
          })),
        }));
        messages.value = msgs;
        // 同步到 localStorage，保持本地缓存最新
        saveLocalHistory(threadId, msgs);
        return;
      }

      // 2. 后端无数据，降级使用 localStorage
      if (messages.value.length !== msgCountBefore) return;
      const localMessages = loadLocalHistory(threadId);
      if (localMessages.length > 0) {
        messages.value = localMessages;
        return;
      }

      // 3. 都没有，保持空状态（由 StartPage 展示）
      // 不执行 messages.value = []，因为已经是空的了
    } catch (error) {
      console.error('从后端加载历史失败，降级使用本地存储:', error);
      if (messages.value.length !== msgCountBefore) return;
      const localMessages = loadLocalHistory(threadId);
      if (localMessages.length > 0) {
        messages.value = localMessages;
      }
      // 都没有就保持原样，不覆盖
    }
  };

  /**
   * 启动打字机效果：从打字机队列逐字符追加到指定消息
   * 仅用于文本 token，工具调用和思考过程直接写入不走打字机
   */
  const startTypewriter = (assistantIndex: number) => {
    if (typewriterTimer) return;  // 已在运行则跳过

    typewriterTimer = setInterval(() => {
      if (typewriterQueue.value.length === 0) {
        if (typewriterTimer) {
          clearInterval(typewriterTimer);
          typewriterTimer = null;
        }
        return;
      }

      const char = typewriterQueue.value.shift()!;
      const assistantMessage = messages.value[assistantIndex];
      if (assistantMessage) {
        assistantMessage.content += char;
      }
    }, TYPING_SPEED);
  };

  /**
   * 停止打字机效果并清空队列
   */
  const stopTypewriter = () => {
    if (typewriterTimer) {
      clearInterval(typewriterTimer);
      typewriterTimer = null;
    }
    typewriterQueue.value = [];
  };

  /**
   * 判断助手消息是否"完全空白"（无内容、无思考、无工具调用）
   * 用于 abort / 前置清理时决定是否移除占位消息
   */
  const isAssistantMessageEmpty = (msg: Message): boolean => {
    const hasContent = msg.content.trim() !== '';
    const hasReasoning = Array.isArray(msg.reasoning)
      ? msg.reasoning.some(step => step.text && step.text.trim() !== '')
      : !!msg.reasoning && msg.reasoning.trim() !== '';
    const hasToolCalls = !!msg.toolCalls?.length;
    return !hasContent && !hasReasoning && !hasToolCalls;
  };

  /**
   * 中止当前发送：取消网络请求、停止打字机、清理空消息、保存状态
   */
  const abort = async (threadId: string) => {
    // 1. 中止网络请求
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    // 2. 停止打字机效果
    stopTypewriter();

    // 3. 清理完全空白的助手占位消息（保留有思考/工具调用的消息）
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && isAssistantMessageEmpty(lastMsg)) {
        messages.value.pop();
      }
    }

    // 4. 保存当前状态
    saveLocalHistory(threadId, messages.value);
    loading.value = false;
  };

  /**
   * 发送消息：流式接收 AI 回复，支持文本/思考过程/工具调用三类事件
   */
  const sendMessage = async (userMessage: string, threadId: string) => {
    if (loading.value) return;  // 正在发送中则忽略

    // 刷新会话活跃时间，确保真正有活动的会话排在前面
    const sessionStore = useSessionStore();
    const activeSession = sessionStore.sessions.find(s => s.id === threadId);
    if (activeSession) {
      activeSession.updatedAt = Date.now();
    }

    // 前置清理：如果上一条是完全空白的助手占位消息，先移除
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && isAssistantMessageEmpty(lastMsg)) {
        messages.value.pop();
      }
    }

    // 中止可能存在的上一个请求
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    // 1. 添加用户消息到列表
    messages.value.push({ id: generateMessageId(), role: 'user', content: userMessage });
    saveLocalHistory(threadId, messages.value);

    // 2. 添加空的助手消息占位（等待流式填充）
    const assistantMessageIndex = messages.value.length;
    messages.value.push({
      id: generateMessageId(),
      role: 'assistant',
      content: '',
      // reasoning 和 toolCalls 不在此初始化，仅在实际收到事件时才创建
      // 这样 ReasoningBlock / ToolCallCard 的 v-if 判断不会因为空数组而误显示
    });

    loading.value = true;

    try {
      abortController.value = new AbortController();

      // 3. 发起流式请求，通过回调处理不同类型的事件
      await sendMessageStream(
        userMessage,
        threadId,
        {
          // ---- 文本 token → 走打字机队列（保持逐字显示的 UX） ----
          onToken: (content: string) => {
            for (const char of content) {
              typewriterQueue.value.push(char);
            }
            startTypewriter(assistantMessageIndex);
          },

          // ---- 思考过程 → 直接写入 reasoning 字段，不走打字机 ----
          onReasoning: (content: string) => {
            const msg = messages.value[assistantMessageIndex];
            if (!msg) return;
            // 惰性初始化 reasoning 数组
            if (!msg.reasoning || typeof msg.reasoning === 'string') {
              msg.reasoning = [];
            }
            const steps = msg.reasoning as ReasoningStep[];
            if (steps.length === 0) {
              steps.push({ id: 'rs_1', text: content, ts: Date.now() });
            } else {
              // 追加到最后一个 step（流式推理是连续的）
              const lastStep = steps[steps.length - 1];
              if (lastStep) {
                lastStep.text += content;
              } else {
                steps.push({ id: 'rs_1', text: content, ts: Date.now() });
              }
            }
          },

          // ---- 工具调用 → 添加到 toolCalls 数组，状态标记为 running ----
          onToolCall: ({ id, name, args }) => {
            const msg = messages.value[assistantMessageIndex];
            if (!msg) return;
            if (!msg.toolCalls) msg.toolCalls = [];
            const newToolCall: ToolCall = {
              id,
              name,
              args,
              status: 'running',
              startedAt: Date.now(),
            };
            msg.toolCalls.push(newToolCall);
          },

          // ---- 工具结果 → 更新对应 toolCall 的 result 和状态 ----
          onToolResult: ({ id, result }) => {
            const msg = messages.value[assistantMessageIndex];
            if (!msg?.toolCalls) return;
            const tc = msg.toolCalls.find(t => t.id === id);
            if (tc) {
              tc.result = result;
              tc.status = 'success';
              tc.finishedAt = Date.now();
              tc.durationMs = tc.startedAt ? Date.now() - tc.startedAt : undefined;
            }
          },

          // ---- 需要审批 → 设置 pendingApproval，暂停流式输出 ----
          onRequireApproval: (approval) => {
            stopTypewriter();
            pendingApproval.value = approval;
          },

          // ---- 上下文压缩开始 → 显示"正在压缩上下文..." ----
          onCompressing: () => {
            compressingStartTime = Date.now();
            compressingStatus.value = 'compressing';
          },

          // ---- 上下文压缩完成 → 先确保压缩提示展示足量时长，再显示"压缩完毕" ----
          onCompressDone: () => {
            // 若压缩太快，补足"正在压缩..."的最小展示时长，避免一闪而过
            const elapsed = compressingStartTime ? Date.now() - compressingStartTime : 0;
            const remaining = Math.max(0, MIN_COMPRESSING_MS - elapsed);
            setTimeout(() => {
              compressingStatus.value = 'done';
              // "压缩完毕" 也展示足量时长后自动隐藏
              setTimeout(() => {
                compressingStatus.value = 'idle';
              }, MIN_DONE_MS);
            }, remaining);
          },

          // ---- 上下文总结通知 → 插入总结通知消息到消息列表 ----
          onSummaryNotice: (data) => {
            const noticeMsg: Message = {
              id: generateMessageId(),
              role: 'system',
              content: '',
              isSummaryNotice: true,
              summaryData: {
                summarized_count: data.summarized_count,
                preserved_count: data.preserved_count,
                triggered_at: data.triggered_at,
                content: data.summary_content,
              },
            };
            messages.value.push(noticeMsg);
            saveLocalHistory(threadId, messages.value);
          },

          // ---- 错误 → 停止打字机，显示错误信息 ----
          onError: (message: string) => {
            stopTypewriter();
            const msg = messages.value[assistantMessageIndex];
            if (msg) {
              msg.content = `抱歉，出错了：${message}`;
            }
          },
        },
        abortController.value.signal
      );
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'name' in err && err.name === 'AbortError') {
        console.log('用户主动中止了请求。');
        return;
      }
      console.error('流式发送失败:', err);
      stopTypewriter();
      const assistantMessage = messages.value[assistantMessageIndex];
      if (assistantMessage) {
        assistantMessage.content = '抱歉，服务暂时不可用，请稍后再试。';
        saveLocalHistory(threadId, messages.value);
      }
    } finally {
      saveLocalHistory(threadId, messages.value);
      abortController.value = null;
      loading.value = false;
      compressingStatus.value = 'idle';
    }
  };

  /**
   * 清除当前待审批请求（用户已做出决定后调用）
   */
  const clearApproval = () => {
    pendingApproval.value = null;
  };

  /**
   * 清空当前消息列表（用于切换会话前重置状态）
   */
  const clearMessages = () => {
    messages.value = [];
    compressingStatus.value = 'idle';
  };

  /**
   * 页面关闭前清理定时器，防止内存泄漏
   */
  const handleBeforeUnload = () => {
    if (typewriterTimer) {
      clearInterval(typewriterTimer);
      typewriterTimer = null;
    }
    typewriterQueue.value = [];
  };

  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', handleBeforeUnload);
  }

  return {
    messages,
    loading,
    hasMessages,
    pendingApproval,
    compressingStatus,
    sendMessage,
    abort,
    loadHistory,
    loadLocalHistory,
    saveLocalHistory,
    clearApproval,
    clearMessages
  };
});
