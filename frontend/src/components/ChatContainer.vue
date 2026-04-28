<template>
  <div class="chat-container">
    <div class="chat-header">
      <span>OmniAgent</span>
    </div>
    <MessageList
      :messages="messages"
      :loading="loading"
      :editing-message-id="editingMessageId"
      :editing-content="editingContent"
      @update:editing-content="editingContent = $event"
      @save-edit="saveEdit"
      @cancel-edit="cancelEdit"
      @start-edit="editMessage"
    />
    <div class="input-area">
      <ChatInput :loading="loading" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import { useChatMessages } from '@/composables/useChatMessages';
import { generateThreadId } from '@/composables/useSessionManager';

const props = defineProps<{
  threadId: string;
}>();

const emit = defineEmits<{ 'update-session-id': [oldThreadId: string, newThreadId: string] }>();

const currentThreadId = ref(props.threadId);

const { messages, loading, handleSend, abortStream, sendOrAbort } = useChatMessages(currentThreadId);

const editingMessageId = ref<string | null>(null);
const editingContent = ref('');

// 编辑消息
const editMessage = (messageId: string) => {
  // 如果 AI 正在回复，不允许编辑
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

  // 1. 截断：保留被编辑消息之前的干净历史
  const cleanHistory = messages.value.slice(0, editIndex);

  // 2. 生成全新 thread_id，彻底重置后端上下文
  const newThreadId = generateThreadId();
  const oldThreadId = props.threadId;

  // 3. 把干净历史迁移到新 thread_id 下
  localStorage.setItem(`omni_messages_${newThreadId}`, JSON.stringify(cleanHistory));

  // 4. 删除旧 thread_id 的历史
  localStorage.removeItem(`omni_messages_${oldThreadId}`);

  // 5. 更新 messages 为本地的干净历史
  messages.value = [...cleanHistory];

  // 6. 通知 App.vue 更新 thread_id
  emit('update-session-id', oldThreadId, newThreadId);

  // 7. 退出编辑模式，保存状态
  cancelEdit();

  // 8. 等待 threadId prop 更新后，用新内容重新发送
  currentThreadId.value = newThreadId;
  await new Promise(resolve => setTimeout(resolve, 0));
  await handleSend(newContent);
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  flex: 1;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #eaeef2;
  font-weight: 500;
  font-size: 18px;
}

.input-area {
  padding: 12px 16px 20px;
  background: #f5f7fa;
}
</style>
