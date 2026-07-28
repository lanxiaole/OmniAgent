import { defineStore } from 'pinia';
import { ref } from 'vue';
import { sendMessageStream } from '@/api/chat';
import type { Message } from '@/types/chat';
import { storage } from '@/utils/storage';

const STORAGE_KEY_PREFIX = 'messages_';
const TYPING_SPEED = 20;

const generateMessageId = () => {
  return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10);
};

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([]);
  const loading = ref(false);
  const abortController = ref<AbortController | null>(null);

  const typewriterQueue = ref<string[]>([]);
  let typewriterTimer: ReturnType<typeof setInterval> | null = null;

  const loadLocalHistory = (threadId: string): Message[] => {
    try {
      const key = STORAGE_KEY_PREFIX + threadId;
      return storage.get<Message[]>(key, []);
    } catch (error) {
      console.error('加载本地历史消息失败:', error);
      return [];
    }
  };

  const saveLocalHistory = (threadId: string, msgs: Message[]) => {
    const key = STORAGE_KEY_PREFIX + threadId;
    storage.set(key, msgs);
  };

  const loadHistory = (threadId: string) => {
    const localMessages = loadLocalHistory(threadId);
    if (localMessages.length > 0) {
      messages.value = localMessages;
    } else {
      messages.value = [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
    }
  };

  const startTypewriter = (assistantIndex: number) => {
    if (typewriterTimer) return;

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

  const stopTypewriter = () => {
    if (typewriterTimer) {
      clearInterval(typewriterTimer);
      typewriterTimer = null;
    }
    typewriterQueue.value = [];
  };

  const abort = async (threadId: string) => {
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    stopTypewriter();

    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
        messages.value.pop();
      }
    }

    saveLocalHistory(threadId, messages.value);
    loading.value = false;
  };

  const sendMessage = async (userMessage: string, threadId: string) => {
    if (loading.value) return;

    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
        messages.value.pop();
      }
    }

    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }

    messages.value.push({ id: generateMessageId(), role: 'user', content: userMessage });
    saveLocalHistory(threadId, messages.value);

    const assistantMessageIndex = messages.value.length;
    messages.value.push({ id: generateMessageId(), role: 'assistant', content: '' });

    loading.value = true;

    try {
      abortController.value = new AbortController();

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
      abortController.value = null;
      loading.value = false;
    }
  };

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