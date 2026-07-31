<template>
  <div class="file-browser">
    <!-- 左栏：文件树 -->
    <div class="browser-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">文件浏览</span>
        <span v-if="currentPath" class="sidebar-path">{{ currentPath || '/' }}</span>
      </div>
      <FileTree
        :nodes="nodes"
        :current-path="currentPath"
        :selected-path="previewPath"
        :loading="loading"
        @navigate="handleNavigate"
        @preview="handlePreview"
      />
    </div>

    <!-- 右栏：文件预览 -->
    <div class="browser-content">
      <FilePreview
        :file-path="previewPath"
        :content="fileContent"
        :file-size="previewFileSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getWorkspaceTree, getFileContent } from '@/api/workspace';
import type { WorkspaceNode } from '@/api/workspace';
import FileTree from '@/components/workspace/FileTree.vue';
import FilePreview from '@/components/workspace/FilePreview.vue';

const currentPath = ref('');        // 当前浏览的路径
const nodes = ref<WorkspaceNode[]>([]);
const loading = ref(false);
const previewPath = ref('');       // 当前预览的文件路径
const fileContent = ref('');       // 预览文件内容
const previewFileSize = ref(0);    // 预览文件大小

/** 加载目录树 */
const loadTree = async (path: string) => {
  loading.value = true;
  try {
    nodes.value = await getWorkspaceTree(path);
  } catch (e) {
    console.error('加载目录失败:', e);
    nodes.value = [];
  } finally {
    loading.value = false;
  }
};

/** 导航到指定目录 */
const handleNavigate = (path: string) => {
  currentPath.value = path;
  loadTree(path);
};

/** 预览文件 */
const handlePreview = async (path: string) => {
  previewPath.value = path;
  try {
    const result = await getFileContent(path);
    fileContent.value = result.content;
    previewFileSize.value = result.size;
  } catch (e) {
    console.error('加载文件失败:', e);
    fileContent.value = '';
    previewFileSize.value = 0;
  }
};

/** 初始化：加载根目录 */
onMounted(() => {
  loadTree('');
});
</script>

<style scoped>
.file-browser {
  display: flex;
  width: 100%;
  height: 100%;
  background-color: var(--bg-body);
}

/* 左栏：文件树 */
.browser-sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-card);
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.sidebar-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-path {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右栏：文件预览 */
.browser-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
</style>