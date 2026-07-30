<template>
  <aside class="app-sidebar" :class="{ collapsed: layoutStore.sidebarCollapsed }">
    <div class="sidebar-top">
      <AppLogo :collapsed="layoutStore.sidebarCollapsed" />
      <nav class="sidebar-nav">
        <router-link
          v-for="route in routes"
          :key="route.name"
          :to="route.path"
          class="nav-item"
          :class="{ active: $route.path === route.path }"
        >
          <el-icon class="nav-icon">
            <component :is="route.meta?.icon" />
          </el-icon>
          <span v-if="!layoutStore.sidebarCollapsed" class="nav-title">{{ route.meta?.title }}</span>
        </router-link>
      </nav>
    </div>

    <div class="sidebar-bottom">
      <button class="collapse-btn" @click="layoutStore.toggleSidebar">
        <el-icon class="collapse-icon" :class="{ rotated: layoutStore.sidebarCollapsed }">
          <Fold />
        </el-icon>
        <span v-if="!layoutStore.sidebarCollapsed" class="collapse-text">收起侧边栏</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Fold } from '@element-plus/icons-vue';
import { useRoute } from 'vue-router';
import { routes } from '@/router/routes';
import { useLayoutStore } from '@/stores/layoutStore';
import AppLogo from './AppLogo.vue';

const layoutStore = useLayoutStore();
const $route = useRoute();
</script>

<style scoped>
.app-sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  /* 弱化背景：使用更深一层的底色，使其从主内容区后退 */
  background-color: var(--bg-page);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
  transition: width var(--transition-base);
  position: relative;
  z-index: 100;
}

.app-sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 折叠状态下的样式优化 */
.app-sidebar.collapsed .sidebar-top {
  padding: 16px 8px;
  align-items: center;
}

.app-sidebar.collapsed .sidebar-bottom {
  padding: 12px 8px;
}

.sidebar-top {
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  gap: 24px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  position: relative;
}

.app-sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.nav-item:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background-color: var(--primary-50);
  color: var(--primary-600);
  font-weight: 600;
}

[data-theme='dark'] .nav-item.active {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--primary-500);
}

.nav-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-title {
  font-size: var(--text-md);
  white-space: nowrap;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 14px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.app-sidebar.collapsed .collapse-btn {
  justify-content: center;
  padding: 0;
}

.collapse-btn:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--text-primary);
}

.collapse-icon {
  font-size: 18px;
  transition: transform var(--transition-base);
}

.collapse-icon.rotated {
  transform: rotate(180deg);
}

.collapse-text {
  white-space: nowrap;
}
</style>
