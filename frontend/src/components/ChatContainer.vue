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

    <!-- 压缩状态提示条 -->
    <div v-if="compressingStatus === 'compressing'" class="compress-status">
      <span class="compress-spinner"></span>
      <span>正在压缩上下文...</span>
    </div>
    <div v-else-if="compressingStatus === 'done'" class="compress-status compress-done">
      <el-icon :size="14"><CircleCheck /></el-icon>
      <span>压缩完毕</span>
    </div>

    <!-- 输入区域：聊天输入框，支持发送/中止 -->
    <div class="input-area">
      <ChatInput :loading="loading" :thread-id="currentThreadId" :scenario-name="scenarioName" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import ChatInput from './ChatInput.vue';
import MessageList from './MessageList.vue';
import ApprovalDialog from './ApprovalDialog.vue';
import ContextStatsPanel from './chat/ContextStatsPanel.vue';
import { useChatStore } from '@/stores/chatStore';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';
import { useMessageEdit } from '@/composables/useMessageEdit';
import { CircleCheck } from '@element-plus/icons-vue';

const emit = defineEmits<{
  (e: 'update-session-id', oldThreadId: string, newThreadId: string): void;
}>();

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
const compressingStatus = computed(() => chatStore.compressingStatus);

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

// 消息编辑功能：处理用户编辑历史消息后的截断和重新发送
// 注意：会话切换（保存/清空/加载历史）逻辑已统一上移到 ChatView 层，
// 此处不再 watch currentThreadId，避免 ChatContainer 卸载时切换失效、
// 以及编辑消息时被误当作"切换会话"处理
const { editingMessageId, editingContent, startEdit, cancelEdit, saveEdit } = useMessageEdit(
  messages,
  handleSend,
  generateThreadId,
  // 编辑保存后回调：由父组件（ChatView）统一更新会话引用并跳过切换逻辑
  (oldThreadId, newThreadId) => {
    emit('update-session-id', oldThreadId, newThreadId);
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
  /* 供绝对定位的压缩状态浮层定位参考 */
  position: relative;
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

/* 压缩状态提示条：居中悬浮于对话框，紧贴输入框上方 */
.compress-status {
  position: absolute;
  bottom: 150px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  font-size: var(--text-sm);
  color: var(--primary-500);
  background: var(--bg-2);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  animation: compressFadeIn 0.25s ease;
}

.compress-status.compress-done {
  color: var(--success);
}

.compress-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes compressFadeIn {
  from { opacity: 0; transform: translateX(-50%) translateY(6px); }
  to { opacity: 1; transform: translateX(-50%); }
}
</style>