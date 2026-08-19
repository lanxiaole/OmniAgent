<template>
  <div class="settings-layout">
    <!-- 侧边栏 + 内容区 -->
    <div class="settings-body">
      <!-- 侧边栏菜单 -->
      <aside class="settings-sidebar">
        <nav class="settings-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="settings-nav-item"
            :class="{ active: isActive(item.path) }"
          >
            <el-icon class="settings-nav-icon">
              <component :is="item.icon" />
            </el-icon>
            <span class="settings-nav-title">{{ item.title }}</span>
          </router-link>
        </nav>
      </aside>

      <!-- 内容区 -->
      <main class="settings-content">
        <router-view v-slot="{ Component }">
          <transition name="settings-page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  DataLine,
  Cpu,
  FolderOpened,
  Link,
  Grid,
  InfoFilled,
} from '@element-plus/icons-vue';

const route = useRoute();

// 侧边栏菜单项配置：路由路径 + 标题 + 图标
const menuItems = computed(() => [
  { path: '/settings/status', title: '服务状态', icon: DataLine },
  { path: '/settings/models', title: '模型管理', icon: Cpu },
  { path: '/settings/workspace', title: '工作区', icon: FolderOpened },
  { path: '/settings/api', title: 'API 配置', icon: Link },
  { path: '/settings/scenarios', title: '场景管理', icon: Grid },
  { path: '/settings/about', title: '关于', icon: InfoFilled },
]);

// 判断当前路径是否与菜单项匹配（含子路径前缀）
const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/');
</script>

<style scoped>
/* 整体布局：标题 + 内容，纵向排列，撑满可用高度 */
.settings-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ========== 主体：侧边栏 + 内容 ========== */
.settings-body {
  flex: 1;
  min-height: 0;
  display: flex;
}

/* 侧边栏：固定 220px，高度撑满 */
.settings-sidebar {
  width: 220px;
  flex-shrink: 0;
  padding: 16px 12px;
  background: var(--bg-page);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-md);
  font-weight: 500;
  transition: all var(--transition-fast);
  overflow: hidden;
}

/* 左侧选中指示竖条 */
.settings-nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 60%;
  border-radius: 0 3px 3px 0;
  background: var(--primary-500);
  transition: transform var(--transition-fast);
}

.settings-nav-item:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--text-primary);
}

.settings-nav-item.active {
  background-color: var(--primary-50);
  color: var(--primary-600);
  font-weight: 600;
}

.settings-nav-item.active::before {
  transform: translateY(-50%) scaleY(1);
}

[data-theme='dark'] .settings-nav-item.active {
  background-color: rgba(59, 130, 246, 0.15);
  color: var(--primary-500);
}

.settings-nav-icon {
  font-size: 19px;
  flex-shrink: 0;
}

.settings-nav-title {
  white-space: nowrap;
}

/* ========== 内容区：可滚动 ========== */
.settings-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 24px 32px;
  background: var(--bg-body);
}

/* 子页面切换动画 */
.settings-page-enter-active,
.settings-page-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.settings-page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.settings-page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>