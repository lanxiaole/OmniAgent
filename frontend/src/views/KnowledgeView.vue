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
          :build-info="buildInfo"
          :rebuilding="rebuilding"
          @rebuild="handleRebuild"
        />

        <!-- 文件上传 -->
        <KnowledgeUploader @success="handleUploadSuccess" />

        <!-- 文件列表（自动撑满剩余高度） -->
        <div class="file-list-wrapper">
          <KnowledgeFileList
            :files="fileList"
            @delete="handleDelete"
            @change="loadData"
          />
        </div>
      </div>

      <!-- 右栏：检索沙盒（自动撑满高度） -->
      <div class="content-right">
        <KnowledgeRetrievalTester />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import {
  getKnowledgeStatus,
  getKnowledgeFiles,
  deleteKnowledgeFile,
  rebuildKnowledge,
  getBuildStatus,
} from '@/api/knowledge';
import type { KnowledgeStatus, KnowledgeFile, BuildStatus } from '@/api/knowledge';
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

// ====== 后台构建进度轮询 ======

const buildInfo = ref<BuildStatus>({
  building: false,
  stage: '',
  current: 0,
  total: 0,
  message: '',
  error: null,
});
let pollTimer: number | null = null;

const stopPolling = (): void => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
};

const pollBuild = async (): Promise<void> => {
  let info: BuildStatus;
  try {
    info = await getBuildStatus();
  } catch {
    stopPolling();
    return;
  }
  buildInfo.value = info;
  if (!info.building) {
    stopPolling();
    if (info.stage === 'error') {
      ElMessage.error(info.error || '索引构建失败');
    }
    await loadData();
  }
};

const startPolling = (): void => {
  if (pollTimer === null) {
    pollTimer = window.setInterval(pollBuild, 1000);
  }
  pollBuild();
};

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

/** 上传成功后开始轮询构建进度（上传与解析均在此后台任务中完成） */
const handleUploadSuccess = (): void => {
  loadData();
  startPolling();
};

const handleRebuild = async () => {
  rebuilding.value = true;
  try {
    const result = await rebuildKnowledge();
    if (result.success) {
      ElMessage.success(result.message || '已开始重建索引');
    } else {
      ElMessage.error(result.message || '重建失败');
    }
  } catch (error) {
    console.error('重建索引失败:', error);
    ElMessage.error('重建索引失败，请稍后重试');
  } finally {
    rebuilding.value = false;
  }
  startPolling();
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
  loadData().finally(() => {
    loading.value = false;
  });
  // 若页面刷新时后台仍在构建，恢复进度显示
  getBuildStatus().then((info) => {
    if (info.building) startPolling();
  });
});

onUnmounted(stopPolling);
</script>

<style scoped>
.view-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-body);
}

.knowledge-content {
  display: grid;
  /* 左侧主内容（弹性）| 右侧检索面板（固定 360px，约为主内容的 1/2）*/
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: var(--space-6);
  padding: var(--space-6);
  width: 90%;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - var(--header-height));
}

.content-left {
  /* grid 单元格，移除 flex: 1 */
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* 文件列表容器，自动撑满左栏剩余高度 */
.file-list-wrapper {
  flex: 1;
  min-height: 0;
}

.content-right {
  /* grid 单元格，移除 width/flex-shrink */
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  max-height: 100%;
}

.content-right .retrieval-tester {
  flex: 1;
  min-height: 0;
}

/* ====== 骨架屏 ====== */

.skeleton-wrapper {
  /* 跨满整个知识库内容区的两栏 grid，布局与实际内容保持一致 */
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: var(--space-6);
  width: 100%;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
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