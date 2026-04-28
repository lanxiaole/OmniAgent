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
      @start-edit="startEdit"
    />
    <div class="input-area">
      <ChatInput :loading="loading" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import { useChatMessages } from '@/composables/useChatMessages';
import { useMessageEdit } from '@/composables/useMessageEdit';
import { generateThreadId } from '@/composables/useSessionManager';

const props = defineProps<{
  threadId: string;
}>();

const emit = defineEmits<{ 'update-session-id': [oldThreadId: string, newThreadId: string] }>();

const currentThreadId = ref(props.threadId);

// 监听 props.threadId 的变化，同步更新 currentThreadId
watch(() => props.threadId, (newThreadId) => {
  currentThreadId.value = newThreadId;
});

const { messages, loading, handleSend, abortStream, sendOrAbort } = useChatMessages(currentThreadId);

// 使用 useMessageEdit composable
const { editingMessageId, editingContent, startEdit, cancelEdit, saveEdit } = useMessageEdit(
  messages,
  handleSend,
  generateThreadId,
  (oldThreadId, newThreadId) => {
    emit('update-session-id', oldThreadId, newThreadId);
    currentThreadId.value = newThreadId;
  },
  () => props.threadId
);
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
