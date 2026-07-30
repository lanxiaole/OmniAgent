// chatStore.ts - 聊天消息状态管理
// 使用 Pinia Composition API 风格管理消息列表、加载状态、打字机效果等
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { sendMessageStream, fetchHistory } from '@/api/chat';
import type { Message, ReasoningStep, ToolCall } from '@/types/chat';
import { storage } from '@/utils/storage';
import { buildMockWelcomeMessages } from '@/utils/chat/mockMessages';

// 本地存储键名前缀，与 storage 工具组合形成完整键名
const STORAGE_KEY_PREFIX = 'messages_';
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

  // 打字机队列：存放待显示的字符
  const typewriterQueue = ref<string[]>([]);
  // 打字机定时器引用
  let typewriterTimer: ReturnType<typeof setInterval> | null = null;

  /**
   * 从本地存储加载指定会话的历史消息
   */
  const loadLocalHistory = (threadId: string): Message[] => {
    try {
      const key = STORAGE_KEY_PREFIX + threadId;
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
    const key = STORAGE_KEY_PREFIX + threadId;
    storage.set(key, msgs);
  };

  /**
   * 加载指定会话的历史消息并显示
   * 优先级：后端 > localStorage > 欢迎消息
   */
  const loadHistory = async (threadId: string) => {
    try {
      // 1. 优先从后端加载
      const backendMessages = await fetchHistory(threadId);

      if (backendMessages.length > 0) {
        const msgs: Message[] = backendMessages.map(m => ({
          id: generateMessageId(),
          role: m.role as 'user' | 'assistant',
          content: m.content
        }));
        messages.value = msgs;
        saveLocalHistory(threadId, msgs);
        return;
      }

      // 2. 后端无数据，尝试 localStorage
      const localMessages = loadLocalHistory(threadId);
      if (localMessages.length > 0) {
        messages.value = localMessages;
        return;
      }

      // 3. 都没有，显示欢迎消息（开发阶段注入演示消息以便 UI 联调）
      messages.value = import.meta.env.DEV
        ? buildMockWelcomeMessages()
        : [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
    } catch (error) {
      console.error('从后端加载历史失败，降级使用本地存储:', error);
      const localMessages = loadLocalHistory(threadId);
      if (localMessages.length > 0) {
        messages.value = localMessages;
      } else {
        messages.value = import.meta.env.DEV
          ? buildMockWelcomeMessages()
          : [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
      }
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
      ? msg.reasoning.length > 0
      : !!msg.reasoning;
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
    }
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
    sendMessage,
    abort,
    loadHistory,
    loadLocalHistory,
    saveLocalHistory
  };
});
