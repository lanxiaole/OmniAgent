<template>
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">关于</h2>
    </div>
    <div v-if="loading" class="card-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else class="about-body">
      <div class="about-item">
        <span class="about-label">应用名称</span>
        <span class="about-value">OmniAgent</span>
      </div>
      <div class="about-item">
        <span class="about-label">版本</span>
        <span class="about-value">{{ aboutInfo.version }}</span>
      </div>
      <div class="about-item">
        <span class="about-label">运行时间</span>
        <span class="about-value">{{ aboutInfo.uptime_display }}</span>
      </div>
      <div class="about-item">
        <span class="about-label">Python 版本</span>
        <span class="about-value about-python">{{ aboutInfo.python_version }}</span>
      </div>
      <div class="about-item">
        <span class="about-label">框架</span>
        <span class="about-value">LangChain + FastAPI + Vue 3</span>
      </div>
      <div class="about-item">
        <span class="about-label">描述</span>
        <span class="about-value about-desc">个人智能助手，支持对话、知识库、记忆、联网搜索等功能</span>
      </div>
      <div class="about-divider"></div>
      <div class="about-item config-path-item">
        <span class="about-label">配置目录</span>
        <div class="config-path-content">
          <span class="about-value config-path-text">{{ configPath }}</span>
          <el-button size="small" class="open-folder-btn" @click="openConfigFolder">
            <el-icon><FolderOpened /></el-icon>
            打开文件夹
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { Loading, FolderOpened } from '@element-plus/icons-vue';

interface AboutInfo {
  version: string;
  python_version: string;
  uptime_seconds: number;
  uptime_display: string;
}

const aboutInfo = reactive<AboutInfo>({
  version: '-',
  python_version: '-',
  uptime_seconds: 0,
  uptime_display: '-',
});

const loading = ref(true);
const configPath = ref('');

const fetchAbout = async () => {
  loading.value = true;
  try {
    const res = await fetch('/api/settings/about');
    const data = await res.json();
    aboutInfo.version = data.version;
    aboutInfo.python_version = data.python_version;
    aboutInfo.uptime_seconds = data.uptime_seconds;
    aboutInfo.uptime_display = data.uptime_display;
  } catch (e) {
    console.error('获取关于信息失败:', e);
  } finally {
    loading.value = false;
  }
};

const fetchConfigPath = async () => {
  try {
    const res = await fetch('/api/settings/config-path');
    const data = await res.json();
    configPath.value = data.path;
  } catch (e) {
    console.error('获取配置目录失败:', e);
    configPath.value = '获取失败';
  }
};

const openConfigFolder = () => {
  if (!configPath.value || configPath.value === '获取失败') return;
  // Electron 环境：使用预加载脚本暴露的 API
  if ((window as any).electronAPI?.openPath) {
    (window as any).electronAPI.openPath(configPath.value);
  } else {
    // Web 开发环境：调用后端接口在服务器端打开文件夹
    fetch('/api/settings/open-config-path', { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          console.error('打开配置目录失败:', data.message);
        }
      })
      .catch(e => console.error('打开配置目录失败:', e));
  }
};

onMounted(() => {
  fetchAbout();
  fetchConfigPath();
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

.about-body {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.about-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.about-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-tertiary);
  min-width: 80px;
  flex-shrink: 0;
  padding-top: 2px;
}

.about-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.about-python {
  font-size: 13px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  word-break: break-all;
}

.about-desc {
  line-height: 1.6;
  color: var(--text-secondary);
  font-weight: 400;
}

.about-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

.config-path-item {
  align-items: flex-start;
}

.config-path-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.config-path-text {
  font-size: 13px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  word-break: break-all;
  line-height: 1.5;
}

.open-folder-btn {
  align-self: flex-start;
}
</style>