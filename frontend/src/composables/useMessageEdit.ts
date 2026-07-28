import { ref, type Ref } from 'vue';
import type { Message } from '@/types/chat';
import { storage } from '@/utils/storage';

const STORAGE_KEY_PREFIX = 'messages_';

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

  const startEdit = (messageId: string) => {
    if (loading.value) return;

    const msg = messages.value.find(m => m.id === messageId);
    if (!msg || msg.role !== 'user') return;

    editingMessageId.value = messageId;
    editingContent.value = msg.content;
  };

  const cancelEdit = () => {
    editingMessageId.value = null;
    editingContent.value = '';
  };

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

    const currentThreadId = getCurrentThreadId();
    const cleanHistory = messages.value.slice(0, editIndex);
    const newThreadId = generateThreadId();
    const oldThreadId = currentThreadId;

    storage.set(STORAGE_KEY_PREFIX + newThreadId, cleanHistory);
    storage.remove(STORAGE_KEY_PREFIX + oldThreadId);

    messages.value = [...cleanHistory];

    onUpdateSessionId(oldThreadId, newThreadId);
    cancelEdit();

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