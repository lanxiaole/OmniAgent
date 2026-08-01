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
        class="status-item"
        :class="{ 'status-active': svc.status === 'active' }"
      >
        <div class="status-dot" :class="`dot-${svc.status}`" />
        <div class="status-info">
          <span class="status-name">{{ svc.name }}</span>
          <span class="status-label">{{ svc.configured ? '已配置' : '未配置' }}</span>
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

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px 20px 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color-light);
  transition: all var(--transition-fast);
}

.status-item:hover {
  border-color: var(--border-color);
}

.status-active {
  border-color: var(--success);
  border-opacity: 0.3;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-active {
  background: var(--success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
}

.dot-inactive {
  background: var(--text-tertiary);
}

.dot-unknown {
  background: var(--warning);
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.status-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-label {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>