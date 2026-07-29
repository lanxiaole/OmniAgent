// themeStore.ts - 主题状态管理
// 管理全局浅色/深色主题，持久化到 localStorage，并同步到 document 的 data-theme 属性
import { defineStore } from 'pinia';
import { ref, onMounted } from 'vue';

export type ThemeMode = 'light' | 'dark' | 'auto';

const STORAGE_KEY = 'omniagent-theme';

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<ThemeMode>('light');
  const isDark = ref(false);

  /**
   * 判断当前是否应使用深色模式
   */
  const resolveDarkMode = (mode: ThemeMode): boolean => {
    if (mode === 'dark') return true;
    if (mode === 'light') return false;
    // auto: 跟随系统偏好
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  };

  /**
   * 应用主题到 DOM
   */
  const applyTheme = (dark: boolean) => {
    isDark.value = dark;
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  };

  /**
   * 设置主题模式
   */
  const setTheme = (mode: ThemeMode) => {
    theme.value = mode;
    localStorage.setItem(STORAGE_KEY, mode);
    applyTheme(resolveDarkMode(mode));
  };

  /**
   * 切换浅色/深色（在 light 和 dark 之间切换，不处理 auto）
   */
  const toggleTheme = () => {
    const next = isDark.value ? 'light' : 'dark';
    setTheme(next);
  };

  /**
   * 初始化主题：从 localStorage 读取，否则默认浅色
   */
  const init = () => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    const mode: ThemeMode = saved || 'light';
    theme.value = mode;
    applyTheme(resolveDarkMode(mode));

    // 监听系统主题变化（仅 auto 模式需要）
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', e => {
      if (theme.value === 'auto') {
        applyTheme(e.matches);
      }
    });
  };

  onMounted(() => {
    init();
  });

  return {
    theme,
    isDark,
    setTheme,
    toggleTheme,
    init,
  };
});
