<!--
  ChatContainer.vue - 聊天主容器组件
  布局结构：顶部标题栏 + 消息列表 + 底部输入框
  协调 chatStore、sessionStore 和 useMessageEdit composable
-->
<template>
  <div class="chat-container">
    <!-- 消息列表组件：展示所有消息，处理消息编辑 -->
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
    <!-- 输入区域：聊天输入框，支持发送/中止 -->
    <div class="input-area">
      <ChatInput :loading="loading" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, computed } from 'vue';
import { storeToRefs } from 'pinia';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import { useChatStore } from '@/stores/chatStore';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';
import { useMessageEdit } from '@/composables/useMessageEdit';

// 初始化两个 Store
const sessionStore = useSessionStore();
const chatStore = useChatStore();

// 从 chatStore 获取响应式的消息列表和加载状态
const messages = computed(() => chatStore.messages);
const loading = computed(() => chatStore.loading);

// 当前会话 thread_id，直接从 sessionStore 获取（响应式，无需本地 ref 中转）
const { currentThreadId } = storeToRefs(sessionStore);

/**
 * 加载指定会话的历史消息
 * @param threadId 会话 ID
 */
const loadHistory = (threadId: string) => {
  chatStore.loadHistory(threadId);
};

/**
 * 发送消息到当前会话
 * @param message 用户输入文本
 */
const handleSend = async (message: string) => {
  await chatStore.sendMessage(message, currentThreadId.value);
};

/**
 * 中止当前正在进行的流式响应
 */
const abortStream = async () => {
  await chatStore.abort(currentThreadId.value);
};

/**
 * 智能发送/中止：
 * 正在加载时视为中止操作，否则视为发送操作
 */
const sendOrAbort = (message: string) => {
  if (chatStore.loading) {
    abortStream();
  } else {
    handleSend(message);
  }
};

// 监听 threadId 变化，仅在获得有效 ID 后加载对应会话历史
watch(
  currentThreadId,
  (newThreadId, oldThreadId) => {
    if (newThreadId && newThreadId !== oldThreadId) {
      loadHistory(newThreadId);
    }
  },
  { immediate: true }
);

// 消息编辑功能：处理用户编辑历史消息后的截断和重新发送
const { editingMessageId, editingContent, startEdit, cancelEdit, saveEdit } = useMessageEdit(
  messages,
  handleSend,
  generateThreadId,
  // 编辑保存后回调：更新 session 中的 thread_id
  (oldThreadId, newThreadId) => {
    sessionStore.updateSessionId(oldThreadId, newThreadId);
    currentThreadId.value = newThreadId;
  },
  // 获取当前 thread_id
  () => currentThreadId.value
);
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  /* 背景透明，继承父容器的白色背景 */
  background: transparent;
}

.input-area {
  padding: 0 24px 16px;
  /* 背景透明，融入整体 */
  background: transparent;
}
</style>