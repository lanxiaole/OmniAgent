<template>
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">工作区管理</h2>
      <el-button size="small" :loading="refreshing" :icon="Refresh" @click="loadInfo">
        刷新
      </el-button>
    </div>

    <div v-if="loading" class="card-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else class="workspace-body">
      <!-- 路径和总大小 -->
      <div class="workspace-overview">
        <div class="overview-row">
          <span class="overview-label">路径</span>
          <span class="overview-value path-value">{{ workspacePath }}</span>
        </div>
        <div class="overview-row">
          <span class="overview-label">总大小</span>
          <span class="overview-value size-value">{{ workspaceInfo.total_display }}</span>
        </div>
      </div>

      <!-- 子目录列表（带进度条） -->
      <div class="dir-list">
        <div v-for="dir in workspaceInfo.dirs" :key="dir.name" class="dir-item">
          <div class="dir-top">
            <div class="dir-left">
              <span class="dir-name">{{ dir.name }}</span>
              <span class="dir-size">{{ dir.size_display }}</span>
            </div>
            <el-button
              v-if="canClean(dir.name)"
              size="small"
              text
              type="danger"
              :loading="cleaningTarget === dir.name"
              @click="handleClean(dir.name)"
            >
              清理
            </el-button>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: dirPercent(dir.size_bytes) }"
              :class="progressClass(dir.name)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading, Refresh } from '@element-plus/icons-vue';

interface WorkspaceDirInfo {
  name: string;
  path: string;
  size_bytes: number;
  size_display: string;
}

interface WorkspaceInfo {
  total_bytes: number;
  total_display: string;
  dirs: WorkspaceDirInfo[];
}

const workspaceInfo = reactive<WorkspaceInfo>({
  total_bytes: 0,
  total_display: '0 B',
  dirs: [],
});

const loading = ref(true);
const refreshing = ref(false);
const cleaningTarget = ref<string | null>(null);

const CLEANABLE = ['cache', 'temp', 'logs', 'uploads'];

const canClean = (name: string) => CLEANABLE.includes(name);

const workspacePath = computed(() => {
  if (workspaceInfo.dirs.length === 0) return '-';
  // 提取公共父路径
  const first = workspaceInfo.dirs[0]?.path;
  if (!first) return '-';
  const idx = first.indexOf('\\workspace\\');
  if (idx !== -1) return first.substring(0, idx + 10) + 'workspace';
  const idx2 = first.indexOf('/workspace/');
  if (idx2 !== -1) return first.substring(0, idx2 + 10) + 'workspace';
  return first;
});

const dirPercent = (bytes: number) => {
  if (workspaceInfo.total_bytes === 0) return '0%';
  return ((bytes / workspaceInfo.total_bytes) * 100).toFixed(1) + '%';
};

const progressClass = (name: string) => {
  const colors: Record<string, string> = {
    checkpoints: 'fill-blue',
    vector_stores: 'fill-purple',
    logs: 'fill-orange',
    cache: 'fill-cyan',
    temp: 'fill-gray',
    knowledge: 'fill-green',
    uploads: 'fill-pink',
  };
  return colors[name] || 'fill-blue';
};

const loadInfo = async () => {
  refreshing.value = true;
  try {
    const res = await fetch('/api/settings/workspace/info');
    const data = await res.json();
    workspaceInfo.total_bytes = data.total_bytes;
    workspaceInfo.total_display = data.total_display;
    workspaceInfo.dirs = data.dirs || [];
  } catch (e) {
    console.error('获取工作区信息失败:', e);
    ElMessage.error('获取工作区信息失败');
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
};

const handleClean = async (target: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 ${target} 目录吗？此操作不可恢复。`,
      '清理确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    );
  } catch {
    return;
  }

  cleaningTarget.value = target;
  try {
    const res = await fetch('/api/settings/workspace/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target }),
    });
    const data = await res.json();
    if (data.success) {
      ElMessage.success(`清理完成，释放 ${data.freed_display}`);
      await loadInfo();
    } else {
      ElMessage.error(data.message || '清理失败');
    }
  } catch (e) {
    console.error('清理失败:', e);
    ElMessage.error('清理失败');
  } finally {
    cleaningTarget.value = null;
  }
};

onMounted(() => {
  loadInfo();
});
</script>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--text-tertiary);
  font-size: 15px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.workspace-body {
  padding: 20px 24px 24px;
}

/* 概览区域 */
.workspace-overview {
  background: var(--bg-card-hover);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overview-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-label {
  font-size: 14px;
  color: var(--text-tertiary);
  min-width: 48px;
  flex-shrink: 0;
}

.overview-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.path-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
  word-break: break-all;
}

.size-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary-600);
}

/* 目录列表 */
.dir-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dir-item {
  padding: 0 4px;
}

.dir-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.dir-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dir-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.dir-size {
  font-size: 13px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
}

/* 进度条 */
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--bg-card-hover);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.fill-blue { background: #3b82f6; }
.fill-purple { background: #8b5cf6; }
.fill-orange { background: #f59e0b; }
.fill-cyan { background: #06b6d4; }
.fill-gray { background: #9ca3af; }
.fill-green { background: #10b981; }
.fill-pink { background: #ec4899; }
</style>