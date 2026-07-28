// useSessionManager.ts - 会话管理组合式函数
// 封装会话 Store 的调用逻辑，作为组件与 Store 之间的薄层
import { onMounted } from 'vue';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';

// 重新导出线程 ID 生成工具，方便其他模块使用
export { generateThreadId };

/**
 * 会话管理 Composable
 * 负责初始化会话、创建新会话、切换会话、清空会话、重命名等操作
 * 实际状态管理委托给 useSessionStore
 */
export function useSessionManager() {
  const store = useSessionStore();

  // 组件挂载时初始化会话数据（从 localStorage 恢复）
  onMounted(() => {
    store.init();
  });

  /**
   * 创建新会话
   * @returns 新会话的 thread_id
   */
  const handleNewSession = () => {
    return store.newSession();
  };

  /**
   * 切换到指定会话
   * @param threadId 目标会话 ID
   */
  const handleSwitchSession = (threadId: string) => {
    store.switchSession(threadId);
  };

  /**
   * 清空指定会话（删除后端历史 + 前端列表项）
   * @param threadId 要清空的会话 ID
   */
  const handleClearSession = async (threadId: string) => {
    await store.clearSession(threadId);
  };

  /**
   * 更新会话 ID（消息编辑后生成新 thread_id 时使用）
   * @param oldThreadId 原会话 ID
   * @param newThreadId 新会话 ID
   */
  const updateSessionId = (oldThreadId: string, newThreadId: string) => {
    store.updateSessionId(oldThreadId, newThreadId);
  };

  /**
   * 重命名会话
   * @param threadId 目标会话 ID
   * @param newTitle 新标题
   */
  const renameSession = (threadId: string, newTitle: string) => {
    store.renameSession(threadId, newTitle);
  };

  // 对外暴露会话状态和操作方法
  return {
    sessions: store.sessions,
    currentThreadId: store.currentThreadId,
    handleNewSession,
    handleSwitchSession,
    handleClearSession,
    updateSessionId,
    renameSession
  };
}