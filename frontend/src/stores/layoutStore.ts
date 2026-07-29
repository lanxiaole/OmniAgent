// layoutStore.ts - 布局状态管理
// 管理侧边栏展开/折叠等全局布局状态，持久化到 localStorage
import { defineStore } from 'pinia';
import { ref, onMounted } from 'vue';

const SIDEBAR_KEY = 'omniagent-sidebar-collapsed';

export const useLayoutStore = defineStore('layout', () => {
  const sidebarCollapsed = ref(false);

  const setCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed;
    localStorage.setItem(SIDEBAR_KEY, String(collapsed));
  };

  const toggleSidebar = () => {
    setCollapsed(!sidebarCollapsed.value);
  };

  const init = () => {
    const saved = localStorage.getItem(SIDEBAR_KEY);
    if (saved !== null) {
      sidebarCollapsed.value = saved === 'true';
    }
  };

  onMounted(() => {
    init();
  });

  return {
    sidebarCollapsed,
    setCollapsed,
    toggleSidebar,
    init,
  };
});
