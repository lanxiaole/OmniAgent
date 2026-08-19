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

// 是否自动跟随滚动。
// 仅当用户明确向上滚动离开"底部附近"时临时关闭；用户滚回底部附近立即自动恢复。
// 采用抗抖容差 + 双向恢复，避免流式输出时轻微抖动导致"永久失灵"。
const shouldAutoScroll = ref(true);

// 判定"在底部附近"的容差（px）。放大容差，减少边缘抖动与平滑动画造成的误判。
const AT_BOTTOM_TOLERANCE = 120;

const isAtBottom = (): boolean => {
  const el = listRef.value;
  if (!el) return true;
  return el.scrollHeight - el.scrollTop - el.clientHeight < AT_BOTTOM_TOLERANCE;
};

const handleScroll = () => {
  // 双向更新：离开底部则暂停跟随，回到底部则重新跟随
  shouldAutoScroll.value = isAtBottom();
};

// 即时滚动到底部。
// 故意不使用 behavior:'smooth'：平滑动画的中间态会触发 scroll 事件，
// 把 shouldAutoScroll 误置为 false —— 这正是"跟一小下就失灵"的根因。
const scrollToBottomNow = () => {
  const el = listRef.value;
  if (!el || !shouldAutoScroll.value) return;
  el.scrollTop = el.scrollHeight;
};

// 内容更新后等渲染完成再滚动。分两步确保取到最新 scrollHeight，
// 并再次兜底检查 shouldAutoScroll（期间用户可能已上滚）。
const followContent = () => {
  if (!shouldAutoScroll.value) return;
  nextTick(() => {
    scrollToBottomNow();
  });
};

// 新消息出现 → 立刻滚到底
watch(
  () => props.messages.length,
  () => followContent()
);

// 最后一条消息 content 变化（流式输出）→ 自动跟随
watch(
  () => {
    const msgs = props.messages;
    const last = msgs.length > 0 ? msgs[msgs.length - 1] : null;
    return last?.content ?? '';
  },
  () => {
    if (props.loading) followContent();
  }
);

// 流式结束：做一次收尾滚动（若用户正上滚读历史则尊重其位置，不强制拉回）
watch(
  () => props.loading,
  (val) => {
    if (!val) followContent();
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
