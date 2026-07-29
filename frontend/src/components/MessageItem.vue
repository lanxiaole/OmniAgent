<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-avatar">
      <div v-if="message.role === 'user'" class="avatar avatar-user">你</div>
      <div v-else class="avatar avatar-assistant">
        <div class="avatar-mark">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2.5" />
            <circle cx="16" cy="16" r="6" fill="currentColor" />
          </svg>
        </div>
      </div>
    </div>

    <div class="message-main">
      <div v-if="message.role === 'assistant'" class="message-meta">
        <span class="sender-name">OmniAgent</span>
        <span v-if="message.createdAt" class="send-time">{{ formatTime(message.createdAt) }}</span>
      </div>

      <!-- 助手消息：思考过程 -->
      <ReasoningBlock
        v-if="message.role === 'assistant' && message.reasoning"
        :steps="message.reasoning"
        :default-open="message.reasoningOpen"
        :started-at="message.createdAt"
      />

      <!-- 助手消息：工具调用卡片 -->
      <template v-if="message.role === 'assistant' && message.toolCalls?.length">
        <ToolCallCard
          v-for="tc in message.toolCalls"
          :key="tc.id"
          v-bind="tc"
        />
      </template>

      <!-- 消息正文气泡 -->
      <div class="message-bubble" :class="{ editing }">
        <!-- 用户消息：编辑态 -->
        <template v-if="message.role === 'user' && editing">
          <el-input
            type="textarea"
            :model-value="editingContent"
            @update:model-value="$emit('update:editingContent', $event)"
            :rows="3"
            resize="none"
          />
          <div class="edit-buttons">
            <el-button type="primary" size="small" @click="$emit('save-edit')">保存并重新发送</el-button>
            <el-button size="small" @click="$emit('cancel-edit')">取消</el-button>
          </div>
        </template>

        <!-- 用户消息：普通 -->
        <template v-else-if="message.role === 'user' && !editing">
          <div class="bubble-text">{{ message.content }}</div>
        </template>

        <!-- 助手消息：普通/加载中 -->
        <template v-else>
          <template v-if="message.content === '' && loading">
            <div class="loading-indicator">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="loading-text">思考中</span>
            </div>
          </template>
          <MarkdownRenderer
            v-else
            :content="message.content"
            :plain="loading"
          />
        </template>
      </div>

      <!-- 编辑按钮：用户消息 hover 显示 -->
      <el-button
        v-if="message.role === 'user' && !editing"
        class="edit-action-btn"
        size="small"
        :icon="Edit"
        @click.stop="$emit('start-edit')"
      >
        编辑
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Edit } from '@element-plus/icons-vue';
import type { Message } from '@/types/chat';
import MarkdownRenderer from './chat/MarkdownRenderer.vue';
import ReasoningBlock from './chat/ReasoningBlock.vue';
import ToolCallCard from './chat/ToolCallCard.vue';
import { formatTime } from '@/utils/markdown';

defineProps<{
  message: Message;
  loading: boolean;
  editing: boolean;
  editingContent: string;
}>();

defineEmits<{
  'update:editingContent': [value: string];
  'save-edit': [];
  'cancel-edit': [];
  'start-edit': [];
}>();
</script>

<style scoped>
.message-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 28px;
  animation: msgEnter 250ms ease;
}

@keyframes msgEnter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.avatar-user {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  color: white;
}

.avatar-assistant {
  background: linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%);
  border: 1px solid var(--border-color);
  color: var(--primary-600);
}

[data-theme='dark'] .avatar-assistant {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  color: var(--primary-500);
}

.avatar-mark {
  width: 22px;
  height: 22px;
}

.avatar-mark svg {
  width: 100%;
  height: 100%;
}

.message-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.message-wrapper.user .message-main {
  align-items: flex-end;
}

.message-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  padding: 0 4px;
}

.sender-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.send-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.message-bubble {
  position: relative;
  max-width: min(78%, 820px);
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
  font-size: var(--text-md);
  white-space: normal;
  word-break: break-word;
  box-sizing: border-box;
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border-top-right-radius: 6px;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.message-wrapper.assistant .message-bubble {
  background-color: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color-light);
  border-top-left-radius: 6px;
}

.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-wrapper.user .bubble-text {
  line-height: 1.7;
}

/* 用户消息编辑态 */
.message-bubble.editing {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  min-width: 420px;
}

.edit-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

/* 编辑按钮（hover 显示） */
.edit-action-btn {
  opacity: 0;
  margin-top: 6px;
  pointer-events: none;
  border-radius: var(--radius-md);
  border: none;
  background-color: var(--bg-sidebar-hover);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  padding: 2px 10px;
  height: auto;
  transition: all var(--transition-fast);
  z-index: 10;
  white-space: nowrap;
}

.edit-action-btn:hover {
  background-color: var(--bg-card-hover);
  color: var(--text-primary);
}

.message-wrapper.user:hover .edit-action-btn {
  opacity: 1;
  pointer-events: auto;
}

/* 加载指示器 */
.loading-indicator {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.loading-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--primary-500);
  opacity: 0.4;
  animation: dotBounce 1.2s infinite ease-in-out;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes dotBounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.35;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.loading-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
