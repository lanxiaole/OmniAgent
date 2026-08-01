<template>
  <div class="file-tree">
    <!-- 返回上一级（固定在顶部） -->
    <div v-if="currentPath !== ''" class="tree-back-bar" @click="goBack">
      <span class="back-icon">📁</span>
      <span class="back-name">..</span>
      <span class="back-label">返回上级</span>
    </div>

    <!-- 目录列表（可滚动区域） -->
    <div class="tree-list">
      <div
        v-for="node in nodes"
        :key="node.path"
        class="tree-item"
        :class="{
          directory: node.type === 'directory',
          selected: node.type === 'file' && node.path === selectedPath,
        }"
        @click="handleClick(node)"
      >
        <span class="tree-item-icon">{{ node.type === 'directory' ? '📁' : '📄' }}</span>
        <span class="tree-item-name">{{ node.name }}</span>
        <span v-if="node.type === 'file' && node.size != null" class="tree-item-size">
          {{ formatFileSize(node.size) }}
        </span>
      </div>

      <!-- 空状态 -->
      <div v-if="nodes.length === 0 && !loading" class="empty-state">
        此目录为空
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkspaceNode } from '@/api/workspace';

interface Props {
  nodes: WorkspaceNode[];
  currentPath: string;
  selectedPath?: string;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  selectedPath: '',
});

const emit = defineEmits<{
  navigate: [path: string];
  preview: [path: string];
}>();

/** 格式化文件大小 */
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/** 返回上级目录 */
const goBack = () => {
  const parentPath = props.currentPath.split('/').slice(0, -1).join('/');
  emit('navigate', parentPath);
};

/** 点击节点 */
const handleClick = (node: WorkspaceNode) => {
  if (node.type === 'directory') {
    emit('navigate', node.path);
  } else {
    emit('preview', node.path);
  }
};
</script>

<style scoped>
.file-tree {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 返回上级 bar（固定顶部） */
.tree-back-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  margin: var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color-light);
  padding-bottom: var(--space-3);
  transition: background-color 120ms ease;
  user-select: none;
  flex-shrink: 0;
}

.tree-back-bar:hover {
  background-color: var(--bg-card-hover);
}

.tree-back-bar:active {
  background-color: var(--bg-page);
}

.back-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.back-name {
  flex: 1;
  font-size: var(--text-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.back-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* 可滚动列表 */
.tree-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-2) var(--space-2);
}

.tree-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 120ms ease, transform 80ms ease;
  user-select: none;
}

.tree-item:hover {
  background-color: var(--bg-card-hover);
}

.tree-item:active {
  transform: scale(0.98);
  background-color: var(--bg-page);
}

.tree-item.directory {
  font-weight: 500;
}

.tree-item.selected {
  background-color: var(--primary-50);
  color: var(--primary-600);
}

[data-theme='dark'] .tree-item.selected {
  background-color: rgba(59, 130, 246, 0.12);
  color: var(--primary-400);
}

.tree-item-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.tree-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
}

.tree-item-size {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}
</style>