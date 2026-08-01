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
      <!-- 总大小 -->
      <div class="total-size">
        <span class="total-label">总占用</span>
        <span class="total-value">{{ workspaceInfo.total_display }}</span>
      </div>

      <!-- 子目录列表 -->
      <div class="dir-list">
        <div v-for="dir in workspaceInfo.dirs" :key="dir.name" class="dir-item">
          <div class="dir-left">
            <el-icon :size="16" class="dir-icon"><Folder /></el-icon>
            <span class="dir-name">{{ dir.name }}</span>
          </div>
          <div class="dir-right">
            <span class="dir-size">{{ dir.size_display }}</span>
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading, Refresh, Folder } from '@element-plus/icons-vue';

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
  padding: 16px 20px 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.workspace-body {
  padding: 16px 20px 20px;
}

.total-size {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-card-hover);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
}

.total-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.total-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary-600);
}

.dir-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dir-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.dir-item:hover {
  background: var(--bg-card-hover);
}

.dir-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dir-icon {
  color: var(--text-tertiary);
}

.dir-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.dir-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dir-size {
  font-size: 13px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
}
</style>