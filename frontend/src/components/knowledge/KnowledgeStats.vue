<template>
  <div class="knowledge-stats">
    <div class="stats-top">
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
          :disabled="buildInfo.building"
          :icon="Refresh"
          @click="$emit('rebuild')"
        >
          重建索引
        </el-button>
      </div>
    </div>

    <!-- 构建进度条 -->
    <div v-if="buildInfo.building" class="build-progress">
      <div class="build-progress-header">
        <span class="build-progress-label">
          <span class="dot dot-building"></span>{{ progressLabel }}
        </span>
        <span class="build-progress-percent">{{ progressPercent }}%</span>
      </div>
      <el-progress
        :percentage="progressPercent"
        :stroke-width="8"
        :status="progressPercent >= 100 ? 'success' : undefined"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Document, Grid, Clock, Refresh } from '@element-plus/icons-vue';
import type { KnowledgeStatus, BuildStatus } from '@/api/knowledge';

interface Props {
  status: KnowledgeStatus;
  buildInfo: BuildStatus;
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

/** 构建进度标签 */
const progressLabel = computed(() => {
  const s = props.buildInfo;
  if (s.stage === 'parsing') return `解析文档 ${s.current}/${s.total}`;
  if (s.stage === 'embedding') return `生成向量 ${s.current}/${s.total}`;
  return '准备中...';
});

/** 综合百分比：解析阶段占 40%，向量化阶段占 60% */
const progressPercent = computed(() => {
  const s = props.buildInfo;
  if (s.total <= 0) return 5;
  if (s.stage === 'parsing') return Math.round((s.current / s.total) * 40);
  if (s.stage === 'embedding') return Math.round(40 + (s.current / s.total) * 60);
  return 5;
});
</script>

<style scoped>
.knowledge-stats {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.stats-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.stats-cards {
  display: flex;
  flex-wrap: wrap;          /* 窄屏时自动换行到下一行，避免挤压 */
  gap: var(--space-4) var(--space-6);
  flex: 1;
  min-width: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1 1 140px;          /* 可伸缩，基础宽度 140px */
  min-width: 0;             /* 允许内容收缩，防止 flex 子项被强制撑大 */
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
  min-width: 0;
  flex: 1;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  overflow-wrap: anywhere;   /* 长字符串（如日期）允许在任意字符处断行 */
  word-break: break-word;
}

.time-value {
  font-size: var(--text-sm);  /* 缩小日期字号，给横向留更多空间 */
  font-weight: 600;
  white-space: nowrap;        /* 日期保持单行，配合 flex-wrap 整体换行 */
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

/* 构建进度 */
.build-progress {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-color-light);
}

.build-progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--text-sm);
}

.build-progress-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
}

.dot-building {
  background: var(--primary-500);
  animation: pulse 1s ease-in-out infinite;
}

.build-progress-percent {
  font-weight: 600;
  color: var(--primary-600);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
</style>