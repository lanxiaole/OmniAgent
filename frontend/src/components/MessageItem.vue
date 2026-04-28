<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-bubble">
      <!-- 用户消息 -->
      <template v-if="message.role === 'user'">
        <!-- 普通状态 -->
        <template v-if="!editing">
          {{ message.content }}
        </template>
        <!-- 编辑状态 -->
        <template v-else>
          <el-input type="textarea" :model-value="editingContent" @update:model-value="$emit('update:editingContent', $event)" :rows="2" />
          <div class="edit-buttons">
            <el-button size="small" @click="$emit('save-edit')">保存</el-button>
            <el-button size="small" @click="$emit('cancel-edit')">取消</el-button>
          </div>
        </template>
      </template>
      <!-- 助手消息 -->
      <template v-else-if="message.role === 'assistant'">
        <!-- 消息内容为空且正在加载 -->
        <template v-if="message.content === '' && loading">
          思考中<span class="thinking-dots"></span>
        </template>
        <!-- 消息内容不为空且正在加载 -->
        <template v-else-if="message.content !== '' && loading">
          {{ message.content }}
        </template>
        <!-- 消息内容不为空且未加载 -->
        <template v-else>
          {{ message.content }}
        </template>
      </template>
    </div>
    <!-- 编辑按钮 -->
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
</template>

<script setup lang="ts">
import type { Message } from '@/types/chat';
import { Edit } from '@element-plus/icons-vue';

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
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 40px;
  position: relative;
}

.message-wrapper.user {
  align-items: flex-end;
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.edit-action-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
  border-radius: 8px;
  border: none;
  background-color: #f0f2f5;
  color: #606266;
  font-size: 13px;
  padding: 2px 8px;
  height: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  z-index: 10;
  white-space: nowrap;
  margin-top: 8px;
}

.edit-action-btn:hover {
  background-color: #e0e4e8;
  color: #303133;
}

.message-wrapper.user:hover .edit-action-btn {
  opacity: 1;
  pointer-events: auto;
}

.edit-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.message-bubble {
  position: relative;
  max-width: 75%;
  padding: 10px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .message-bubble {
  background-color: #409eff;
  color: white;
}

.assistant .message-bubble {
  background-color: #f0f0f0;
  color: #333;
}

/* 思考中的跳动点动画 */
.thinking-dots::after {
  content: '...';
  animation: dotPulse 1.5s infinite;
}

@keyframes dotPulse {
  0% { content: '.'; }
  33% { content: '..'; }
  66% { content: '...'; }
  100% { content: '.'; }
}
</style>
