<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>
    <div class="header-right">
      <button class="icon-btn" :title="themeStore.isDark ? '切换浅色' : '切换深色'" @click="themeStore.toggleTheme">
        <el-icon size="18">
          <Sunny v-if="themeStore.isDark" />
          <Moon v-else />
        </el-icon>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { Sunny, Moon } from '@element-plus/icons-vue';
import { useThemeStore } from '@/stores/themeStore';

const route = useRoute();
const themeStore = useThemeStore();

const pageTitle = computed(() => {
  return (route.meta?.title as string) || 'OmniAgent';
});
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--text-primary);
}
</style>
