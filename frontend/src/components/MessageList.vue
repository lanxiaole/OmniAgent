<template>
  <div class="message-list" ref="listRef">
    <MessageItem
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
      :loading="loading"
      :editing="editingMessageId === msg.id"
      :editing-content="editingContent"
      @update:editing-content="$emit('update:editingContent', $event)"
      @save-edit="$emit('saveEdit', msg.id)"
      @cancel-edit="$emit('cancelEdit')"
      @start-edit="$emit('startEdit', msg.id)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import type { Message } from '@/types/chat';
import MessageItem from './MessageItem.vue';

const props = defineProps<{
  messages: Message[];
  loading: boolean;
  editingMessageId: string | null;
  editingContent: string;
}>();

defineEmits<{
  'update:editingContent': [value: string];
  'saveEdit': [id: string];
  'cancelEdit': [];
  'startEdit': [id: string];
}>();

const listRef = ref<HTMLElement>();

const scrollToBottom = async () => {
  await nextTick();
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight;
  }
};

watch(
  () => props.messages.length,
  () => {
    scrollToBottom();
  }
);
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
