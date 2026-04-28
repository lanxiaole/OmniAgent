import { ref, watch, onMounted, type Ref} from 'vue';
import { sendMessageStream } from '@/api/chat';
import type { Message } from '@/types/chat';
import { storage } from '@/utils/storage';

const STORAGE_KEY_PREFIX = 'omni_messages_';

const generateMessageId = () => {
  return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10);
};

export function useChatMessages(threadId: Ref<string>) {
  const messages = ref<Message[]>([]);
  const loading = ref(false);
  const abortController = ref<AbortController | null>(null);

  // 打字机队列：每个 composable 实例独立，不再是全局状态
  const typewriterQueue = ref<string[]>([]);
  let typewriterTimer: ReturnType<typeof setInterval> | null = null;

  // 打字机速度（毫秒/字），可调整此值改变速度
  const TYPING_SPEED = 20;

  /**
   * 启动打字机效果
   * @param assistantIndex 助手消息在 messages 数组中的索引
   */
  const startTypewriter = (assistantIndex: number) => {
    if (typewriterTimer) return; // 已经在运行

    typewriterTimer = setInterval(async () => {
      if (typewriterQueue.value.length === 0) {
        // 队列为空，停止定时器
        if (typewriterTimer) {
          clearInterval(typewriterTimer);
          typewriterTimer = null;
        }
        return;
      }

      // 取出队列第一个字符，追加到消息上
      const char = typewriterQueue.value.shift()!;
      const assistantMessage = messages.value[assistantIndex];
      if (assistantMessage) {
        assistantMessage.content += char;
        saveLocalHistory(threadId.value, messages.value);
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

  // 从本地存储加载历史消息
  const loadLocalHistory = (threadId: string): Message[] => {
    try {
      const key = STORAGE_KEY_PREFIX + threadId;
      return storage.get<Message[]>(key, []);
    } catch (error) {
      console.error('加载本地历史消息失败:', error);
      return [];
    }
  };

  // 保存历史消息到本地存储
  const saveLocalHistory = (threadId: string, msgs: Message[]) => {
    const key = STORAGE_KEY_PREFIX + threadId;
    storage.set(key, msgs);
  };

  const loadHistory = (currentThreadId: string) => {
    // 从本地存储加载历史消息
    const localMessages = loadLocalHistory(currentThreadId);
    if (localMessages.length > 0) {
      messages.value = localMessages;
    } else {
      // 如果没有历史消息，显示欢迎消息
      messages.value = [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
    }
  };

  const sendOrAbort = (message: string) => {
    if (loading.value) {
      abortStream();
    } else {
      handleSend(message);
    }
  };

  const abortStream = async () => {
    // 1. 中止网络请求
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    // 2. 停止打字机
    stopTypewriter();

    // 3. 清理空的助手占位消息
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
        messages.value.pop();
      }
    }

    // 4. 保存并重置状态
    saveLocalHistory(threadId.value, messages.value);
    loading.value = false;
  };

  const handleSend = async (userMessage: string) => {
    if (loading.value) return;

    // 【新增】前置清理：如果上一条消息是空的助手消息，干掉它
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
        messages.value.pop();
      }
    }

    // 中止前一个请求
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    // 1. 添加用户消息
    messages.value.push({ id: generateMessageId(), role: 'user', content: userMessage });
    saveLocalHistory(threadId.value, messages.value);

    // 2. 添加空的助手消息占位
    const assistantMessageIndex = messages.value.length;
    messages.value.push({ id: generateMessageId(), role: 'assistant', content: '' });

    loading.value = true;

    try {
      // 创建新的 AbortController
      abortController.value = new AbortController();

      // 3. 流式接收回复
      await sendMessageStream(
        userMessage,
        threadId.value,
        (token: string) => {
          // 将 token 拆成单个字符，加入打字机队列
          for (const char of token) {
            typewriterQueue.value.push(char);
          }
          // 启动打字机（如果尚未启动）
          startTypewriter(assistantMessageIndex);
        },
        abortController.value.signal
      );
    } catch (err: unknown) {
      if (typeof err === 'object' && err !== null && 'name' in err && err.name === 'AbortError') {
        console.log('用户主动中止了请求。');
        return; // 用户主动中止，不显示错误
      }
      console.error('流式发送失败:', err);
      stopTypewriter();
      const assistantMessage = messages.value[assistantMessageIndex];
      if (assistantMessage) {
        assistantMessage.content = '抱歉，服务暂时不可用，请稍后再试。';
        saveLocalHistory(threadId.value, messages.value);
      }
    } finally {
      abortController.value = null; // 请求结束后无论成功与否，清理 controller
      loading.value = false;
    }
  };

  // 当 threadId 变化时，重新加载历史消息
  watch(threadId, (newThreadId) => {
    loadHistory(newThreadId);
  }, { immediate: true });

  // 组件挂载时加载历史消息
  onMounted(() => {
    loadHistory(threadId.value);
  });

  return {
    messages,
    loading,
    handleSend,
    abortStream,
    sendOrAbort,
    loadLocalHistory,
    saveLocalHistory
  };
}
