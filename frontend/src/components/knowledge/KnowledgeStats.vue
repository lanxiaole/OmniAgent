<template>
  <div class="knowledge-stats">
    <div class="stats-cards">
      <!-- 文件总数 -->
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="22"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ status.total_files }}</span>
          <span class="stat-label">知识文件</span>
        </div>
      </div>

      <!-- 向量块数 -->
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="22"><Grid /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ status.total_chunks }}</span>
          <span class="stat-label">向量块</span>
        </div>
      </div>

      <!-- 最后构建时间 -->
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon :size="22"><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value time-value">{{ formattedBuildTime }}</span>
          <span class="stat-label">最后构建</span>
        </div>
      </div>
    </div>

    <!-- 操作区 -->
    <div class="stats-actions">
      <div v-if="status.hash_changed" class="change-hint">
        <span class="dot dot-warning"></span>
        <span>有文件变更，点击重建索引更新知识库</span>
      </div>
      <el-button
        type="primary"
        :loading="rebuilding"
        :icon="Refresh"
        @click="$emit('rebuild')"
      >
        重建索引
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Document, Grid, Clock, Refresh } from '@element-plus/icons-vue';
import type { KnowledgeStatus } from '@/api/knowledge';

interface Props {
  status: KnowledgeStatus;
  rebuilding: boolean;
}

const props = defineProps<Props>();

defineEmits<{
  rebuild: [];
}>();

const formattedBuildTime = computed(() => {
  if (!props.status.last_build) return '未构建';
  try {
    const d = new Date(props.status.last_build);
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return props.status.last_build;
  }
});
</script>

<style scoped>
.knowledge-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
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
  background: var(--primary-50);
  color: var(--primary-600);
  flex-shrink: 0;
  transition: background var(--transition-fast);
}

.stat-card:hover .stat-icon {
  background: var(--primary-100);
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

.time-value {
  font-size: var(--text-base);
  font-weight: 600;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.stats-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-shrink: 0;
}

.change-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--warning);
  white-space: nowrap;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.dot-warning {
  background: var(--warning);
}
</style>