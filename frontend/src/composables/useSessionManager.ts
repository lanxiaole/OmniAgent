import { ref, onMounted } from 'vue';
import { clearHistory } from '../api/chat';
import { storage } from '../utils/storage';

interface Session {
  id: string;
  title: string;
}

const sessions = ref<Session[]>([]);
const currentThreadId = ref<string>('');

const generateThreadId = (): string => {
  return Date.now() + '-' + Math.random().toString(36).substring(2, 8);
};

const loadFromLocalStorage = () => {
  try {
    const savedSessions = storage.get<Session[]>('sessions', []);
    const savedCurrentThread = storage.get<string>('current_thread', '');

    if (savedSessions.length > 0) {
      sessions.value = savedSessions;
    }

    if (savedCurrentThread) {
      currentThreadId.value = savedCurrentThread;
    }

    if (sessions.value.length === 0) {
      const defaultThreadId = generateThreadId();
      sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
      currentThreadId.value = defaultThreadId;
      saveToLocalStorage();
    }
  } catch (error) {
    console.error('加载会话数据失败:', error);
    const defaultThreadId = generateThreadId();
    sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
    currentThreadId.value = defaultThreadId;
    saveToLocalStorage();
  }
};

const saveToLocalStorage = () => {
  storage.set('sessions', sessions.value);
  storage.set('current_thread', currentThreadId.value);
};

const handleNewSession = async () => {
  const newThreadId = generateThreadId();
  const newSession: Session = {
    id: newThreadId,
    title: `会话 ${sessions.value.length + 1}`
  };

  sessions.value.push(newSession);
  currentThreadId.value = newThreadId;
  saveToLocalStorage();
};

const handleSwitchSession = (threadId: string) => {
  currentThreadId.value = threadId;
  saveToLocalStorage();
};

const handleClearSession = async (threadId: string) => {
  try {
    await clearHistory(threadId);

    const index = sessions.value.findIndex(session => session.id === threadId);
    if (index !== -1) {
      sessions.value.splice(index, 1);
    }

    if (threadId === currentThreadId.value) {
      if (sessions.value.length > 0 && sessions.value[0]) {
        currentThreadId.value = sessions.value[0].id;
      } else {
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

const updateSessionId = (oldThreadId: string, newThreadId: string) => {
  const session = sessions.value.find(s => s.id === oldThreadId);
  if (session) {
    session.id = newThreadId;
    session.title = `会话 ${sessions.value.length}`;
  }
  currentThreadId.value = newThreadId;
  saveToLocalStorage();
};

export function useSessionManager() {
  onMounted(() => {
    loadFromLocalStorage();
  });

  return {
    sessions,
    currentThreadId,
    handleNewSession,
    handleSwitchSession,
    handleClearSession,
    updateSessionId
  };
}
