import { watch, onMounted, type Ref } from 'vue';
import { useChatStore } from '@/stores/chatStore';

export function useChatMessages(threadId: Ref<string>) {
  const store = useChatStore();

  const loadHistory = (currentThreadId: string) => {
    store.loadHistory(currentThreadId);
  };

  const loadLocalHistory = (tid: string) => {
    return store.loadLocalHistory(tid);
  };

  const saveLocalHistory = (tid: string, msgs: import('@/types/chat').Message[]) => {
    store.saveLocalHistory(tid, msgs);
  };

  const handleSend = async (message: string) => {
    await store.sendMessage(message, threadId.value);
  };

  const abortStream = async () => {
    await store.abort(threadId.value);
  };

  const sendOrAbort = (message: string) => {
    if (store.loading) {
      abortStream();
    } else {
      handleSend(message);
    }
  };

  watch(threadId, (newThreadId) => {
    loadHistory(newThreadId);
  }, { immediate: true });

  onMounted(() => {
    loadHistory(threadId.value);
  });

  return {
    messages: store.messages,
    loading: store.loading,
    handleSend,
    abortStream,
    sendOrAbort,
    loadLocalHistory,
    saveLocalHistory
  };
}