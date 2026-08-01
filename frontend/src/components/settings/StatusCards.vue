<template>
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">服务状态</h2>
    </div>
    <div v-if="loading" class="card-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else class="status-grid">
      <div
        v-for="svc in services"
        :key="svc.key"
        class="status-card"
        :class="statusClass(svc)"
      >
        <div class="status-indicator">
          <span class="status-emoji">{{ statusEmoji(svc) }}</span>
        </div>
        <div class="status-info">
          <span class="status-name">{{ svc.name }}</span>
          <span class="status-desc">{{ statusDesc(svc) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Loading } from '@element-plus/icons-vue';

interface ServiceStatus {
  name: string;
  key: string;
  configured: boolean;
  status: string;
}

const services = ref<ServiceStatus[]>([]);
const loading = ref(true);

const statusEmoji = (svc: ServiceStatus) => {
  if (svc.configured && svc.status === 'active') return '🟢';
  if (svc.key === 'vector_store' && !svc.configured) return '🟡';
  return '🔴';
};

const statusDesc = (svc: ServiceStatus) => {
  if (svc.configured && svc.status === 'active') return '已配置';
  if (svc.key === 'vector_store' && !svc.configured) return '未构建';
  return '未配置';
};

const statusClass = (svc: ServiceStatus) => {
  if (svc.configured && svc.status === 'active') return 'card-active';
  if (svc.key === 'vector_store' && !svc.configured) return 'card-warning';
  return 'card-inactive';
};

const fetchStatus = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/settings/status');
    const data = await res.json();
    services.value = data.services || [];
  } catch (e) {
    console.error('获取服务状态失败:', e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchStatus();
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

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px 20px 20px;
}

.status-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 14px;
  border-radius: var(--radius-md);
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color-light);
  transition: all var(--transition-fast);
  text-align: center;
}

.status-card:hover {
  border-color: var(--border-color);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.card-active {
  border-color: rgba(16, 185, 129, 0.3);
}

.card-active:hover {
  border-color: rgba(16, 185, 129, 0.6);
}

.card-warning {
  border-color: rgba(245, 158, 11, 0.3);
}

.card-warning:hover {
  border-color: rgba(245, 158, 11, 0.6);
}

.card-inactive {
  border-color: var(--border-color-light);
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-emoji {
  font-size: 28px;
  line-height: 1;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.status-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.status-desc {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 10px;
  background: var(--bg-card);
  color: var(--text-secondary);
}

.card-active .status-desc {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.card-warning .status-desc {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.card-inactive .status-desc {
  background: var(--bg-card);
  color: var(--text-tertiary);
}
</style>