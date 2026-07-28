import { onMounted } from 'vue';
import { useSessionStore, generateThreadId } from '@/stores/sessionStore';

export { generateThreadId };

export function useSessionManager() {
  const store = useSessionStore();

  onMounted(() => {
    store.init();
  });

  const handleNewSession = () => {
    return store.newSession();
  };

  const handleSwitchSession = (threadId: string) => {
    store.switchSession(threadId);
  };

  const handleClearSession = async (threadId: string) => {
    await store.clearSession(threadId);
  };

  const updateSessionId = (oldThreadId: string, newThreadId: string) => {
    store.updateSessionId(oldThreadId, newThreadId);
  };

  const renameSession = (threadId: string, newTitle: string) => {
    store.renameSession(threadId, newTitle);
  };

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