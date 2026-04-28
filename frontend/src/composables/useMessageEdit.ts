import { ref, type Ref } from 'vue';
import type { Message } from '@/types/chat';

export function useMessageEdit(
  messages: Ref<Message[]>,
  handleSend: (message: string) => Promise<void>,
  generateThreadId: () => string,
  onUpdateSessionId: (oldThreadId: string, newThreadId: string) => void,
  getCurrentThreadId: () => string
) {
  const editingMessageId = ref<string | null>(null);
  const editingContent = ref('');
  const loading = ref(false);

  // 开始编辑消息
  const startEdit = (messageId: string) => {
    // 如果正在发送消息，不允许编辑
    if (loading.value) return;

    // 找到要编辑的消息
    const msg = messages.value.find(m => m.id === messageId);
    if (!msg || msg.role !== 'user') return;

    // 设置编辑状态
    editingMessageId.value = messageId;
    editingContent.value = msg.content;
  };

  // 取消编辑
  const cancelEdit = () => {
    editingMessageId.value = null;
    editingContent.value = '';
  };

  // 保存编辑
  const saveEdit = async (messageId: string) => {
    if (loading.value) return;

    const newContent = editingContent.value.trim();
    if (!newContent) return;

    const editIndex = messages.value.findIndex(m => m.id === messageId);
    if (editIndex === -1) return;

    const editedMessage = messages.value[editIndex];
    if (!editedMessage) return;

    const oldContent = editedMessage.content;
    if (oldContent === newContent) {
      cancelEdit();
      return;
    }

    // 获取当前线程ID
    const currentThreadId = getCurrentThreadId();

    // 1. 截断：保留被编辑消息之前的干净历史
    const cleanHistory = messages.value.slice(0, editIndex);

    // 2. 生成全新 thread_id，彻底重置后端上下文
    const newThreadId = generateThreadId();
    const oldThreadId = currentThreadId;

    // 3. 把干净历史迁移到新 thread_id 下
    localStorage.setItem(`omni_messages_${newThreadId}`, JSON.stringify(cleanHistory));

    // 4. 删除旧 thread_id 的历史
    localStorage.removeItem(`omni_messages_${oldThreadId}`);

    // 5. 更新 messages 为本地的干净历史
    messages.value = [...cleanHistory];

    // 6. 通知父组件更新 thread_id
    onUpdateSessionId(oldThreadId, newThreadId);

    // 7. 退出编辑模式，保存状态
    cancelEdit();

    // 8. 等待 threadId 更新后，用新内容重新发送
    await new Promise(resolve => setTimeout(resolve, 0));
    await handleSend(newContent);
  };

  return {
    editingMessageId,
    editingContent,
    startEdit,
    cancelEdit,
    saveEdit
  };
}
