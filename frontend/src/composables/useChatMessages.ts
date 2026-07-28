// useChatMessages.ts - 聊天消息管理组合式函数
// 封装聊天 Store 的调用逻辑，处理消息加载、发送、流式中止等业务
import { watch, type Ref } from 'vue';
import { useChatStore } from '@/stores/chatStore';

/**
 * 聊天消息 Composable
 * 负责监听 threadId 变化自动加载历史、发送消息、中止流式响应
 * 实际消息状态和流式处理委托给 useChatStore
 * @param threadId 当前会话 ID 的响应式引用
 */
export function useChatMessages(threadId: Ref<string>) {
  const store = useChatStore();

  /**
   * 加载指定会话的历史消息
   * @param currentThreadId 会话 ID
   */
  const loadHistory = async (currentThreadId: string) => {
    await store.loadHistory(currentThreadId);
  };

  /**
   * 从本地存储加载历史消息（供外部直接查询）
   * @param tid 会话 ID
   * @returns 消息数组
   */
  const loadLocalHistory = (tid: string) => {
    return store.loadLocalHistory(tid);
  };

  /**
   * 保存消息到本地存储
   * @param tid 会话 ID
   * @param msgs 要保存的消息数组
   */
  const saveLocalHistory = (tid: string, msgs: import('@/types/chat').Message[]) => {
    store.saveLocalHistory(tid, msgs);
  };

  /**
   * 发送消息：调用 Store 的 sendMessage 方法进行流式请求
   * @param message 用户输入文本
   */
  const handleSend = async (message: string) => {
    await store.sendMessage(message, threadId.value);
  };

  /**
   * 中止当前流式响应
   */
  const abortStream = async () => {
    await store.abort(threadId.value);
  };

  /**
   * 智能发送/中止：
   * - 如果正在加载（流式响应中），点击视为中止
   * - 否则视为发送新消息
   * @param message 用户输入文本
   */
  const sendOrAbort = (message: string) => {
    if (store.loading) {
      abortStream();
    } else {
      handleSend(message);
    }
  };

  // 监听 threadId 变化，仅在获得有效 ID 后加载对应会话历史
  watch(
    threadId,
    (newThreadId, oldThreadId) => {
      if (newThreadId && newThreadId !== oldThreadId) {
        loadHistory(newThreadId);
      }
    },
    { immediate: true }
  );

  // 对外暴露消息状态和操作方法
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