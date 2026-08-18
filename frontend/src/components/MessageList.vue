<template>
  <div class="message-list" ref="listRef" @scroll="handleScroll">
    <template v-for="msg in messages" :key="msg.id">
      <SummaryNotice
        v-if="msg.isSummaryNotice"
        :data="msg.summaryData"
      />
      <MessageItem
        v-else
        :message="msg"
        :loading="loading"
        :editing="editingMessageId === msg.id"
        :editing-content="editingContent"
        @update:editing-content="$emit('update:editingContent', $event)"
        @save-edit="$emit('saveEdit', msg.id)"
        @cancel-edit="$emit('cancelEdit')"
        @start-edit="$emit('startEdit', msg.id)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import type { Message } from '@/types/chat';
import MessageItem from './MessageItem.vue';
import SummaryNotice from './chat/SummaryNotice.vue';

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

const shouldAutoScroll = ref(true);

const isAtBottom = (): boolean => {
  if (!listRef.value) return false;
  const { scrollTop, scrollHeight, clientHeight } = listRef.value;
  return scrollHeight - scrollTop - clientHeight < 80; // 80px 容差，指尖触底就算
};

const handleScroll = () => {
  shouldAutoScroll.value = isAtBottom();
};

const scrollToBottom = async (smooth = false) => {
  await nextTick();
  if (!listRef.value || !shouldAutoScroll.value) return;
  if (smooth) {
    listRef.value.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' });
  } else {
    listRef.value.scrollTop = listRef.value.scrollHeight;
  }
};

// 新消息出现 → 立刻滚到底
watch(
  () => props.messages.length,
  () => scrollToBottom()
);

// 最后一条消息 content 变化（流式输出）→ 自动跟随
watch(
  () => {
    const msgs = props.messages;
    const last = msgs.length > 0 ? msgs[msgs.length - 1] : null;
    return last?.content ?? '';
  },
  () => {
    if (props.loading && shouldAutoScroll.value) {
      scrollToBottom();
    }
  }
);

// 流式结束后做一次平滑滚动收尾
watch(
  () => props.loading,
  (val) => {
    if (!val) {
      shouldAutoScroll.value = true;
      scrollToBottom(true);
    }
  }
);
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 背景透明，融入父容器 */
  background: transparent;
}

.message-list > * {
  width: 100%;
  max-width: 960px;
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
