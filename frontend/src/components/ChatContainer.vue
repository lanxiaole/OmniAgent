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
import { ref, watch, onMounted, computed } from 'vue';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import { useChatStore } from '@/stores/chatStore';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';
import { useMessageEdit } from '@/composables/useMessageEdit';

const sessionStore = useSessionStore();
const chatStore = useChatStore();

const messages = computed(() => chatStore.messages);
const loading = computed(() => chatStore.loading);

const currentThreadId = ref(sessionStore.currentThreadId);

watch(() => sessionStore.currentThreadId, (newId) => {
  currentThreadId.value = newId;
});

const loadHistory = (threadId: string) => {
  chatStore.loadHistory(threadId);
};

const handleSend = async (message: string) => {
  await chatStore.sendMessage(message, currentThreadId.value);
};

const abortStream = async () => {
  await chatStore.abort(currentThreadId.value);
};

const sendOrAbort = (message: string) => {
  if (chatStore.loading) {
    abortStream();
  } else {
    handleSend(message);
  }
};

watch(currentThreadId, (newThreadId) => {
  loadHistory(newThreadId);
}, { immediate: true });

onMounted(() => {
  loadHistory(currentThreadId.value);
});

const { editingMessageId, editingContent, startEdit, cancelEdit, saveEdit } = useMessageEdit(
  messages,
  handleSend,
  generateThreadId,
  (oldThreadId, newThreadId) => {
    sessionStore.updateSessionId(oldThreadId, newThreadId);
    currentThreadId.value = newThreadId;
  },
  () => currentThreadId.value
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