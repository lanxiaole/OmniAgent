// sessionStore.ts - 会话状态管理
// 使用 Pinia Composition API 风格管理会话列表和当前会话
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { clearHistory } from '@/api/chat';
import { storage } from '@/utils/storage';
import type { Session } from '@/types/session';

/**
 * 生成唯一的会话线程 ID
 * 格式：时间戳 + 随机字符串
 */
export const generateThreadId = (): string => {
  return Date.now() + '-' + Math.random().toString(36).substring(2, 8);
};

/**
 * 会话 Store：管理会话列表、当前会话及相关操作
 * State: sessions（会话数组）、currentThreadId（当前会话 ID）
 * Actions: init / newSession / switchSession / clearSession / renameSession / updateSessionId
 */
export const useSessionStore = defineStore('session', () => {
  // 会话列表
  const sessions = ref<Session[]>([]);
  // 当前选中的会话 ID
  const currentThreadId = ref<string>('');

  // 计算属性：获取当前选中的会话对象
  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentThreadId.value) ?? null
  );

  /**
   * 初始化会话数据：从 localStorage 加载历史会话
   * 如果没有历史数据，自动创建一个默认会话
   */
  const init = () => {
    try {
      // 从本地存储读取已保存的会话列表和当前线程
      const savedSessions = storage.get<Session[]>('sessions', []);
      const savedCurrentThread = storage.get<string>('current_thread', '');

      if (savedSessions.length > 0) {
        sessions.value = savedSessions;
      }

      if (savedCurrentThread) {
        currentThreadId.value = savedCurrentThread;
      }

      // 首次使用时创建默认会话
      if (sessions.value.length === 0) {
        const defaultThreadId = generateThreadId();
        sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
        currentThreadId.value = defaultThreadId;
        saveToLocalStorage();
      }
    } catch (error) {
      // 加载失败时创建默认会话作为兜底
      console.error('加载会话数据失败:', error);
      const defaultThreadId = generateThreadId();
      sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
      currentThreadId.value = defaultThreadId;
      saveToLocalStorage();
    }
  };

  // 将会话状态持久化到 localStorage
  const saveToLocalStorage = () => {
    storage.set('sessions', sessions.value);
    storage.set('current_thread', currentThreadId.value);
  };

  /**
   * 创建新会话：添加到列表末尾并自动切换到新会话
   * @returns 新会话的 thread_id
   */
  const newSession = () => {
    const newThreadId = generateThreadId();
    const newSessionItem: Session = {
      id: newThreadId,
      title: `会话 ${sessions.value.length + 1}`,
      updatedAt: Date.now(),
    };

    sessions.value.push(newSessionItem);
    currentThreadId.value = newThreadId;
    saveToLocalStorage();
    return newThreadId;
  };

  /**
   * 切换到指定会话：同时刷新该会话的最近活动时间
   * @param threadId 目标会话 ID
   */
  const switchSession = (threadId: string) => {
    const session = sessions.value.find(s => s.id === threadId);
    if (session) {
      session.updatedAt = Date.now();
    }
    currentThreadId.value = threadId;
    saveToLocalStorage();
  };

  /**
   * 切换置顶状态
   * @param threadId 目标会话 ID
   */
  const togglePin = (threadId: string) => {
    const session = sessions.value.find(s => s.id === threadId);
    if (session) {
      session.pinned = !session.pinned;
      saveToLocalStorage();
    }
  };

  /**
   * 清空指定会话：调用后端 API 删除历史，然后从列表中移除
   * 如果清空的是当前会话，自动切换到第一个会话或创建新会话
   * @param threadId 要清空的会话 ID
   */
  const clearSession = async (threadId: string) => {
    try {
      // 调用后端 API 清空该会话的聊天历史
      await clearHistory(threadId);

      // 从会话列表中移除
      const index = sessions.value.findIndex(session => session.id === threadId);
      if (index !== -1) {
        sessions.value.splice(index, 1);
      }

      // 如果清空的是当前会话，需要切换或重建
      if (threadId === currentThreadId.value) {
        if (sessions.value.length > 0 && sessions.value[0]) {
          currentThreadId.value = sessions.value[0].id;
        } else {
          // 没有可用会话时创建一个新的默认会话
          const newThreadId = generateThreadId();
          sessions.value = [{ id: newThreadId, title: `会话 1` }];
          currentThreadId.value = newThreadId;
        }
      }

      saveToLocalStorage();
    } catch (error) {
      console.error('清空会话失败:', error);
    }
  };

  /**
   * 重命名会话
   * @param threadId 目标会话 ID
   * @param newTitle 新的会话标题
   */
  const renameSession = (threadId: string, newTitle: string) => {
    const session = sessions.value.find(s => s.id === threadId);
    if (session) {
      // 如果没有提供新标题，使用默认编号标题
      session.title = newTitle || `会话 ${sessions.value.findIndex(s => s.id === threadId) + 1}`;
      saveToLocalStorage();
    }
  };

  /**
   * 更新会话 ID（用于消息编辑后重新生成 thread_id 的场景）
   * @param oldThreadId 原会话 ID
   * @param newThreadId 新会话 ID
   */
  const updateSessionId = (oldThreadId: string, newThreadId: string) => {
    const session = sessions.value.find(s => s.id === oldThreadId);
    if (session) {
      session.id = newThreadId;
    }
    currentThreadId.value = newThreadId;
    saveToLocalStorage();
  };

  // 导出状态和方法供组件使用
  return {
    sessions,
    currentThreadId,
    currentSession,
    init,
    newSession,
    switchSession,
    clearSession,
    renameSession,
    updateSessionId,
    togglePin,
  };
});