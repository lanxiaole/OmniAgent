<template>
  <div class="view-container">
    <div class="knowledge-content">
      <!-- 左栏：管理功能 -->
      <div class="content-left">
        <!-- 状态卡片 -->
        <KnowledgeStats
          :status="statusData"
          :rebuilding="rebuilding"
          @rebuild="handleRebuild"
        />

        <!-- 文件上传 -->
        <KnowledgeUploader @success="loadData" />

        <!-- 文件列表 -->
        <KnowledgeFileList
          :files="fileList"
          @delete="handleDelete"
        />
      </div>

      <!-- 右栏：检索沙盒 -->
      <div class="content-right">
        <KnowledgeRetrievalTester />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  getKnowledgeStatus,
  getKnowledgeFiles,
  deleteKnowledgeFile,
  rebuildKnowledge,
} from '@/api/knowledge';
import type { KnowledgeStatus, KnowledgeFile } from '@/api/knowledge';
import KnowledgeStats from '@/components/knowledge/KnowledgeStats.vue';
import KnowledgeUploader from '@/components/knowledge/KnowledgeUploader.vue';
import KnowledgeFileList from '@/components/knowledge/KnowledgeFileList.vue';
import KnowledgeRetrievalTester from '@/components/knowledge/KnowledgeRetrievalTester.vue';

const statusData = ref<KnowledgeStatus>({
  total_files: 0,
  total_chunks: 0,
  last_build: null,
  hash_changed: false,
});
const fileList = ref<KnowledgeFile[]>([]);
const rebuilding = ref(false);

const loadData = async () => {
  try {
    const [status, files] = await Promise.all([
      getKnowledgeStatus(),
      getKnowledgeFiles(),
    ]);
    statusData.value = status;
    fileList.value = files;
  } catch (error) {
    console.error('加载知识库数据失败:', error);
    ElMessage.error('加载知识库数据失败，请稍后重试');
  }
};

const handleRebuild = async () => {
  rebuilding.value = true;
  try {
    const result = await rebuildKnowledge();
    if (result.success) {
      const msg = result.chunks_added !== undefined
        ? `索引重建完成，新增 ${result.chunks_added} 个向量块`
        : '索引重建完成';
      ElMessage.success(msg);
    } else {
      ElMessage.error(result.message || '重建失败');
    }
    await loadData();
  } catch (error) {
    console.error('重建索引失败:', error);
    ElMessage.error('重建索引失败，请稍后重试');
  } finally {
    rebuilding.value = false;
  }
};

const handleDelete = async (filename: string) => {
  try {
    const result = await deleteKnowledgeFile(filename);
    if (result.success) {
      ElMessage.success(`文件 "${filename}" 已删除`);
    } else {
      ElMessage.error(result.message || '删除失败');
    }
    await loadData();
  } catch (error) {
    console.error('删除文件失败:', error);
    ElMessage.error('删除文件失败，请稍后重试');
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.view-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: var(--bg-body);
}

.knowledge-content {
  display: flex;
  gap: var(--space-6);
  padding: var(--space-6);
  width: 80%;
  max-width: 1400px;
  margin: 0 auto;
  align-items: flex-start;
}

.content-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.content-right {
  width: 420px;
  flex-shrink: 0;
  position: sticky;
  top: calc(var(--header-height) + var(--space-6));
  max-height: calc(100vh - var(--header-height) - var(--space-6) * 2);
  overflow-y: auto;
}

.content-right .retrieval-tester {
  min-height: 400px;
}
</style>