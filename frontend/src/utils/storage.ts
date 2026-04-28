// 统一的 localStorage 工具
const STORAGE_PREFIX = 'omni';

export const storage = {
  get<T>(key: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(`${STORAGE_PREFIX}_${key}`);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  },

  set(key: string, value: unknown): void {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}_${key}`, JSON.stringify(value));
    } catch (e) {
      console.error('localStorage 写入失败:', e);
    }
  },

  remove(key: string): void {
    localStorage.removeItem(`${STORAGE_PREFIX}_${key}`);
  },
};
