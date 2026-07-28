// chatStore.ts - 聊天消息状态管理
// 使用 Pinia Composition API 风格管理消息列表、加载状态、打字机效果等
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { sendMessageStream, fetchHistory } from '@/api/chat';
import type { Message } from '@/types/chat';
import { storage } from '@/utils/storage';

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
 * State: messages（消息数组）、loading（发送中）、abortController、typewriterQueue
 * Actions: sendMessage / abort / loadHistory / loadLocalHistory / saveLocalHistory
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
   * @param threadId 会话 ID
   * @returns 消息数组
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
   * @param threadId 会话 ID
   * @param msgs 要保存的消息数组
   */
  const saveLocalHistory = (threadId: string, msgs: Message[]) => {
    const key = STORAGE_KEY_PREFIX + threadId;
    storage.set(key, msgs);
  };

  /**
   * 加载指定会话的历史消息并显示
   * 如果没有历史消息，显示欢迎消息
   * @param threadId 会话 ID
   */
  const loadHistory = async (threadId: string) => {
    try {
      // 1. 优先从后端加载
      const backendMessages = await fetchHistory(threadId);

      if (backendMessages.length > 0) {
        // 后端有数据，转为前端 Message 格式并同步到 localStorage
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

      // 3. 都没有，显示欢迎消息
      messages.value = [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
    } catch (error) {
      console.error('从后端加载历史失败，降级使用本地存储:', error);
      // 降级：使用 localStorage
      const localMessages = loadLocalHistory(threadId);
      if (localMessages.length > 0) {
        messages.value = localMessages;
      } else {
        messages.value = [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
      }
    }
  };

  /**
   * 启动打字机效果：从打字机队列逐字符追加到指定消息
   * @param assistantIndex 助手消息在 messages 数组中的索引
   */
  const startTypewriter = (assistantIndex: number) => {
    if (typewriterTimer) return;  // 已在运行则跳过

    typewriterTimer = setInterval(() => {
      if (typewriterQueue.value.length === 0) {
        // 队列为空，停止定时器
        if (typewriterTimer) {
          clearInterval(typewriterTimer);
          typewriterTimer = null;
        }
        return;
      }

      // 取出队列第一个字符，追加到助手消息内容中
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
   * 中止当前发送：取消网络请求、停止打字机、清理空消息、保存状态
   * @param threadId 当前会话 ID（用于保存）
   */
  const abort = async (threadId: string) => {
    // 1. 中止网络请求
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    // 2. 停止打字机效果
    stopTypewriter();

    // 3. 清理空的助手占位消息（用户主动中止时可能残留）
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
        messages.value.pop();
      }
    }

    // 4. 保存当前状态
    saveLocalHistory(threadId, messages.value);
    loading.value = false;
  };

  /**
   * 发送消息：流式接收 AI 回复并通过打字机效果显示
   * @param userMessage 用户输入的消息文本
   * @param threadId 当前会话 ID
   */
  const sendMessage = async (userMessage: string, threadId: string) => {
    if (loading.value) return;  // 正在发送中则忽略

    // 前置清理：如果上一条是空的助手占位消息，先移除
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
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
    messages.value.push({ id: generateMessageId(), role: 'assistant', content: '' });

    loading.value = true;

    try {
      // 创建新的中止控制器
      abortController.value = new AbortController();

      // 3. 发起流式请求，每收到一个 token 就拆成字符加入打字机队列
      await sendMessageStream(
        userMessage,
        threadId,
        (token: string) => {
          for (const char of token) {
            typewriterQueue.value.push(char);
          }
          startTypewriter(assistantMessageIndex);
        },
        abortController.value.signal
      );
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'name' in err && err.name === 'AbortError') {
        console.log('用户主动中止了请求。');
        return;  // 用户主动中止，不显示错误
      }
      // 其他错误：显示错误提示
      console.error('流式发送失败:', err);
      stopTypewriter();
      const assistantMessage = messages.value[assistantMessageIndex];
      if (assistantMessage) {
        assistantMessage.content = '抱歉，服务暂时不可用，请稍后再试。';
        saveLocalHistory(threadId, messages.value);
      }
    } finally {
      // 请求结束后：保存完整消息到本地存储并清理状态
      saveLocalHistory(threadId, messages.value);
      abortController.value = null;
      loading.value = false;
    }
  };

  // 导出状态和方法供组件使用
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