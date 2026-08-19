<template>
  <header class="app-header">
    <!-- 左侧：Logo -->
    <div class="header-left">
      <router-link to="/" class="logo-link" title="OmniAgent">
        <div class="logo-mark">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2.5" />
            <circle cx="16" cy="16" r="6" fill="currentColor" />
            <path d="M16 2V8M16 24V30M2 16H8M24 16H30" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
          </svg>
        </div>
        <span class="logo-text">OmniAgent</span>
      </router-link>
    </div>

    <!-- 中间：导航按钮，均匀分布 -->
    <nav class="header-nav">
      <router-link
        v-for="routeItem in routes"
        :key="routeItem.name"
        :to="routeItem.path"
        class="nav-btn"
        :class="{ active: isRouteActive(routeItem) }"
        :title="(routeItem.meta?.title as string)"
      >
        <el-icon class="nav-icon">
          <component :is="iconMap[routeItem.meta?.icon as string]" />
        </el-icon>
        <span class="nav-label">{{ routeItem.meta?.title }}</span>
        <span class="nav-indicator" />
      </router-link>
    </nav>

    <!-- 右侧：主题切换 -->
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
import { useRoute } from 'vue-router';
import {
  Sunny,
  Moon,
  ChatRound,
  Collection,
  Memo,
  Folder,
  Setting,
} from '@element-plus/icons-vue';
import { routes } from '@/router/routes';
import { useThemeStore } from '@/stores/themeStore';
import type { RouteRecordRaw } from 'vue-router';

const route = useRoute();
const themeStore = useThemeStore();
void route;

// 图标名称 → 组件映射，解决路由 meta.icon 存字符串无法被 <component :is> 解析的问题
const iconMap: Record<string, object> = {
  ChatRound,
  Collection,
  Memo,
  Folder,
  Setting,
};

// 判断当前路径是否为该导航项激活状态（含子路由前缀匹配）
const isRouteActive = (routeItem: RouteRecordRaw) =>
  route.path === routeItem.path ||
  (routeItem.path !== '/' && route.path.startsWith(routeItem.path + '/'));
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 var(--space-5);
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

/* ========== 左侧：Logo ========== */
.header-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  text-decoration: none;
  transition: background-color var(--transition-fast);
}

.logo-link:hover {
  background-color: var(--bg-sidebar-hover);
}

.logo-mark {
  width: 26px;
  height: 26px;
  color: var(--primary-600);
}

.logo-mark svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

/* ========== 中间：导航 ========== */
.header-nav {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
}

.nav-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 38px;
  padding: 0 20px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-md);
  font-weight: 500;
  white-space: nowrap;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.nav-btn:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--text-primary);
}

.nav-btn.active {
  background-color: var(--primary-50);
  color: var(--primary-600);
}

[data-theme='dark'] .nav-btn.active {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--primary-500);
}

/* 图标 */
.nav-icon {
  font-size: 19px;
  flex-shrink: 0;
}

/* 文字 */
.nav-label {
  font-size: 13.5px;
  line-height: 1;
}

/* 激活态底部指示条 */
.nav-indicator {
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 60%;
  height: 2.5px;
  border-radius: 2px 2px 0 0;
  background-color: var(--primary-500);
  transition: transform var(--transition-fast) ease;
}

.nav-btn.active .nav-indicator {
  transform: translateX(-50%) scaleX(1);
}

.nav-btn:hover .nav-indicator {
  transform: translateX(-50%) scaleX(1);
}

/* 窄屏：隐藏文字，只保留图标 */
@media (max-width: 900px) {
  .nav-label,
  .logo-text {
    display: none;
  }

  .nav-btn {
    min-width: 38px;
    padding: 0;
    gap: 0;
  }

  .header-nav {
    gap: var(--space-0);
  }
}

/* ========== 右侧：主题切换 ========== */
.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
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
