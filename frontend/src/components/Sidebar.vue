<template>
  <aside class="sidebar">
    <!-- 开启新对话按钮：DeepSeek 风格的圆角胶囊 + 加号 -->
    <button class="new-session-btn" @click="$emit('new-session')">
      <el-icon size="16"><Plus /></el-icon>
      <span>开启新对话</span>
    </button>

    <!-- 会话列表：按时间分组（置顶 / 今天 / 昨天 / 7天内 / 30天内 / 更早） -->
    <div class="session-list">
      <template v-for="group in groupedSessions" :key="group.label">
        <div v-if="group.items && group.items.length > 0" class="group">
          <div class="group-label">{{ group.label }}</div>
          <div
            v-for="session in group.items"
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
            <span v-else class="session-title" @dblclick.stop="startRename(session.id, session.title)">{{ session.title }}</span>

            <div v-if="editingSessionId !== session.id" class="session-actions">
              <el-icon class="action-icon" :class="{ active: session.pinned }" @click.stop="$emit('toggle-pin', session.id)">
                <Star v-if="session.pinned" />
                <StarFilled v-else />
              </el-icon>
              <el-icon class="action-icon delete" @click.stop="$emit('clear-session', session.id)">
                <Delete />
              </el-icon>
            </div>
          </div>
        </div>
      </template>

      <div v-if="sessions.length === 0" class="empty-state">
        暂无历史会话
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, nextTick } from 'vue';
import { Delete, Star, StarFilled, Plus } from '@element-plus/icons-vue';
import type { Session } from '@/types/session';

const props = defineProps<{
  sessions: Session[];
  currentThreadId: string;
}>();

const emit = defineEmits<{
  'new-session': [];
  'switch-session': [threadId: string];
  'clear-session': [threadId: string];
  'rename-session': [threadId: string, newTitle: string];
  'toggle-pin': [threadId: string];
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

/**
 * 把时间戳归类到对应分组
 * 分组：今天 / 昨天 / 7天内 / 30天内 / 更早
 */
const bucketOf = (ts?: number): string => {
  if (!ts) return 'more';
  const now = Date.now();
  const diff = now - ts;
  const oneDay = 24 * 60 * 60 * 1000;
  if (diff < oneDay && new Date(ts).toDateString() === new Date(now).toDateString()) {
    return 'today';
  }
  // 昨天：和今天相邻的那一天
  const yesterdayStart = new Date(now);
  yesterdayStart.setDate(yesterdayStart.getDate() - 1);
  yesterdayStart.setHours(0, 0, 0, 0);
  const yesterdayEnd = new Date(now);
  yesterdayEnd.setHours(0, 0, 0, 0);
  if (ts >= yesterdayStart.getTime() && ts < yesterdayEnd.getTime()) {
    return 'yesterday';
  }
  if (diff < 7 * oneDay) return 'within7';
  if (diff < 30 * oneDay) return 'within30';
  return 'more';
};

const groupedSessions = computed(() => {
  const order: { key: string; label: string }[] = [
    { key: 'pinned', label: '置顶' },
    { key: 'today', label: '今天' },
    { key: 'yesterday', label: '昨天' },
    { key: 'within7', label: '7 天内' },
    { key: 'within30', label: '30 天内' },
    { key: 'more', label: '更早' },
  ];

  const pinned = props.sessions.filter(s => s.pinned);
  const others = props.sessions
    .filter(s => !s.pinned)
    .slice()
    .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0));

  const buckets: Record<string, Session[]> = {
    pinned: [...pinned],
    today: [],
    yesterday: [],
    within7: [],
    within30: [],
    more: [],
  };

  for (const s of others) {
    const key = bucketOf(s.updatedAt);
    buckets[key]!.push(s);
  }

  return order.map(o => ({ label: o.label, items: buckets[o.key] }));
});
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 14px 12px;
  box-sizing: border-box;
  background-color: transparent;
}

/* ========== 开启新对话按钮 ========== */
.new-session-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 40px;
  margin-bottom: 14px;
  padding: 0 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background-color: var(--bg-card);
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.new-session-btn:hover {
  background-color: var(--bg-card-hover);
  border-color: var(--primary-500);
  color: var(--primary-600);
}

.new-session-btn .el-icon {
  color: var(--primary-600);
}

/* ========== 会话列表 ========== */
.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.group-label {
  padding: 6px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  user-select: none;
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
  color: var(--text-primary);
  font-size: var(--text-md);
}

.session-item:hover {
  background-color: var(--bg-card-hover);
}

.session-item.active {
  background-color: var(--primary-50);
  color: var(--primary-700);
  font-weight: 500;
}

[data-theme='dark'] .session-item.active {
  background-color: rgba(59, 130, 246, 0.18);
  color: var(--primary-500);
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1.5px solid var(--primary-500);
  border-radius: var(--radius-sm);
  outline: none;
  font-size: var(--text-md);
  color: var(--text-primary);
  background-color: var(--bg-card);
}

.session-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.session-item:hover .session-actions,
.session-item.active .session-actions {
  opacity: 1;
}

.action-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-icon:hover {
  background-color: var(--bg-card);
  color: var(--text-primary);
}

.action-icon.active {
  color: #f59e0b;
  opacity: 1;
}

.action-icon.delete:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

/* ========== 空状态 ========== */
.empty-state {
  padding: 40px 0;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* ========== 滚动条 ========== */
.session-list::-webkit-scrollbar {
  width: 4px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: var(--border-color-strong);
  border-radius: var(--radius-full);
}

.session-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}
</style>
