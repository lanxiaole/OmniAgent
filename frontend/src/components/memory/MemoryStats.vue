<template>
  <div class="memory-stats">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="22"><Memo /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ count }}</span>
          <span class="stat-label">记忆条目</span>
        </div>
      </div>
    </div>

    <div class="stats-actions">
      <el-button type="primary" :icon="Plus" @click="$emit('add')">
        添加记忆
      </el-button>
      <el-button
        type="danger"
        :icon="Delete"
        :disabled="count === 0"
        @click="$emit('clear')"
      >
        清空所有
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Memo, Plus, Delete } from '@element-plus/icons-vue';

interface Props {
  count: number;
}

defineProps<Props>();

defineEmits<{
  add: [];
  clear: [];
}>();
</script>

<style scoped>
.memory-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.stats-cards {
  display: flex;
  gap: var(--space-6);
  flex: 1;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 140px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--bg-body);
  color: var(--primary-500);
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.stats-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}
</style>