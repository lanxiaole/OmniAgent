<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span>会话历史</span>
      <el-button type="primary" size="small" @click="$emit('new-session')">
        新建会话
      </el-button>
    </div>
    <div class="session-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentThreadId }"
        @click="!editingSessionId && $emit('switch-session', session.id)"
      >
        <input
          v-if="editingSessionId === session.id"
          v-model="editingTitle"
          @keyup.enter="saveRename(session.id)"
          @keyup.esc="cancelRename"
          @blur="saveRename(session.id)"
          ref="editInput"
          class="edit-input"
          type="text"
          @click.stop
        />
        <span v-else class="session-title">{{ session.title }}</span>
        <div class="session-actions">
          <el-icon
            v-if="editingSessionId !== session.id"
            class="edit-icon"
            @click.stop="startRename(session.id, session.title)"
          >
            <Edit />
          </el-icon>
          <el-icon
            class="delete-icon"
            @click.stop="$emit('clear-session', session.id)"
          >
            <Delete />
          </el-icon>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Delete, Edit } from '@element-plus/icons-vue';
import { ref, nextTick } from 'vue';

interface Session {
  id: string;
  title: string;
}

defineProps<{
  sessions: Session[];
  currentThreadId: string;
}>();

const emit = defineEmits<{
  'new-session': [];
  'switch-session': [threadId: string];
  'clear-session': [threadId: string];
  'rename-session': [threadId: string, newTitle: string];
}>();

const editingSessionId = ref<string>('');
const editingTitle = ref<string>('');
const editInput = ref<HTMLInputElement>();

const startRename = (threadId: string, currentTitle: string) => {
  editingSessionId.value = threadId;
  editingTitle.value = currentTitle;
  nextTick(() => {
    editInput.value?.focus();
    editInput.value?.select();
  });
};

const saveRename = (threadId: string) => {
  if (editingSessionId.value) {
    emit('rename-session', threadId, editingTitle.value);
    editingSessionId.value = '';
    editingTitle.value = '';
  }
};

const cancelRename = () => {
  editingSessionId.value = '';
  editingTitle.value = '';
};
</script>

<style scoped>
.sidebar {
  width: 260px;
  background-color: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px 0;
  box-sizing: border-box;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px 20px;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 10px;
}

.sidebar-header span {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 10px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #fff;
  border: 1px solid #e0e0e0;
}

.session-item:hover {
  background-color: #e8f0fe;
  border-color: #c6e2ff;
}

.session-item.active {
  background-color: #e6f7ff;
  border-color: #91d5ff;
  font-weight: 500;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
  color: #333;
}

.edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #409eff;
  border-radius: 4px;
  outline: none;
  font-size: 14px;
  color: #333;
  background-color: #fff;
  margin-right: 10px;
}

.session-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edit-icon {
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #409eff;
  font-size: 16px;
  cursor: pointer;
}

.delete-icon {
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #ff4d4f;
  font-size: 16px;
  cursor: pointer;
}

.session-item:hover .edit-icon,
.session-item:hover .delete-icon {
  opacity: 1;
}

.edit-icon:hover {
  color: #66b1ff;
}

.delete-icon:hover {
  color: #ff7875;
}

/* 滚动条样式 */
.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
