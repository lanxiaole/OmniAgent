<template>
  <div class="view-container">
    <!-- 加载骨架屏 -->
    <div v-if="loading" class="knowledge-content">
      <div class="skeleton-wrapper">
        <div class="skeleton-loading-overlay">
          <el-icon class="loading-icon"><Loading /></el-icon>
          加载中...
        </div>
        <div class="content-left">
          <div class="skeleton-card">
            <div class="skeleton-stats">
              <div class="skeleton-block skeleton-stat-item" v-for="i in 3" :key="i" />
            </div>
          </div>
          <div class="skeleton-card skeleton-upload" />
          <div class="skeleton-card skeleton-file-list" />
        </div>
        <div class="content-right">
          <div class="skeleton-card skeleton-retrieval" />
        </div>
      </div>
    </div>

    <!-- 实际内容 -->
    <div v-else class="knowledge-content">
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
import { Loading } from '@element-plus/icons-vue';
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
const loading = ref(true);

const loadData = async () => {
  loading.value = true;
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
  } finally {
    loading.value = false;
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

/* ====== 骨架屏 ====== */

.skeleton-wrapper {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  position: relative;
}

.skeleton-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-size: var(--text-lg);
  color: var(--text-tertiary);
  z-index: 10;
  user-select: none;
  pointer-events: none;
}

.skeleton-loading-overlay .loading-icon {
  animation: skeleton-spin 1s linear infinite;
}

@keyframes skeleton-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.skeleton-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.skeleton-stats {
  display: flex;
  gap: var(--space-6);
  padding: var(--space-5);
}

.skeleton-stat-item {
  height: 44px;
  flex: 1;
  border-radius: var(--radius-md);
  background: linear-gradient(
    90deg,
    var(--border-color-light) 0%,
    var(--bg-card-hover) 50%,
    var(--border-color-light) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
}

.skeleton-upload {
  height: 160px;
  background: linear-gradient(
    90deg,
    var(--bg-card) 0%,
    var(--bg-card-hover) 50%,
    var(--bg-card) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
}

.skeleton-file-list {
  height: 280px;
  background: linear-gradient(
    90deg,
    var(--bg-card) 0%,
    var(--bg-card-hover) 50%,
    var(--bg-card) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
}

.skeleton-retrieval {
  height: 500px;
  background: linear-gradient(
    90deg,
    var(--bg-card) 0%,
    var(--bg-card-hover) 50%,
    var(--bg-card) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>