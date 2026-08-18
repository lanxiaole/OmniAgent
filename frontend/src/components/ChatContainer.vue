<!--
  ChatContainer.vue - 聊天主容器组件
  布局结构：消息列表区域 + 审批对话框 + 底部输入框
  协调 chatStore、sessionStore 和 useMessageEdit composable
-->
<template>
  <div class="chat-container">
    <!-- 消息列表组件：展示所有消息，处理消息编辑 -->
    <div class="messages-area">
      <!-- 上下文信息面板入口 -->
      <div class="messages-header">
        <ContextStatsPanel :thread-id="currentThreadId" />
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

      <!-- 审批对话框：在消息列表区域内绝对定位 -->
      <ApprovalDialog
        :visible="showApprovalDialog"
        :approval="currentApproval"
        @result="handleApprovalResult"
      />
    </div>

    <!-- 输入区域：聊天输入框，支持发送/中止 -->
    <div class="input-area">
      <ChatInput :loading="loading" :thread-id="currentThreadId" :scenario-name="scenarioName" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, computed } from 'vue';
import { storeToRefs } from 'pinia';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import ApprovalDialog from './ApprovalDialog.vue';
import ContextStatsPanel from './chat/ContextStatsPanel.vue';
import { useChatStore } from '@/stores/chatStore';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';
import { useMessageEdit } from '@/composables/useMessageEdit';

defineProps<{
  threadId: string;
  scenarioName?: string;
}>();

// 初始化两个 Store
const sessionStore = useSessionStore();
const chatStore = useChatStore();

// 从 chatStore 获取响应式的消息列表和加载状态
const messages = computed(() => chatStore.messages);
const loading = computed(() => chatStore.loading);
const pendingApproval = computed(() => chatStore.pendingApproval);

// 当前会话 thread_id，直接从 sessionStore 获取（响应式，无需本地 ref 中转）
const { currentThreadId } = storeToRefs(sessionStore);

// 审批对话框是否显示
const showApprovalDialog = computed(() => {
  return pendingApproval.value !== null;
});

// 当前审批请求（用于传给 ApprovalDialog）
const currentApproval = computed(() => {
  return pendingApproval.value || { request_id: '', tool: '', args: {}, reason: '' };
});

/**
 * 处理审批结果
 * 用户点击批准/拒绝后，清除待审批状态
 * 审批通过后，Agent 继续执行，流式输出会自动恢复
 */
const handleApprovalResult = (requestId: string, approved: boolean) => {
  chatStore.clearApproval();
  // 审批结果已通过 API 发送到后端，后端会唤醒等待的线程继续执行
  // 流式 SSE 连接仍然保持，后端会继续推送后续事件
  console.log(`审批请求 ${requestId} 已${approved ? '批准' : '拒绝'}`);
};

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

// 监听 threadId 变化，切换会话时保存当前消息并加载新会话历史
// 注意：不使用 { immediate: true }，首次加载由 ChatView 的 onMounted 处理
// 避免从 StartPage 过渡到 ChatContainer 时覆盖正在流式传输的消息
watch(
  currentThreadId,
  (newThreadId, oldThreadId) => {
    if (newThreadId && newThreadId !== oldThreadId) {
      // 切换会话：先把当前会话的消息保存到 localStorage
      if (oldThreadId) {
        chatStore.saveLocalHistory(oldThreadId, chatStore.messages);
      }
      // 清空当前消息，准备加载新会话
      chatStore.clearMessages();
      // 加载新会话的历史消息
      loadHistory(newThreadId);
    }
  },
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

.messages-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.messages-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 16px 0;
  flex-shrink: 0;
}

.input-area {
  padding: 0 24px 16px;
  /* 背景透明，融入整体 */
  background: transparent;
}
</style>