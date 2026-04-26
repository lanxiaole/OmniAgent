<template>
  <div class="app-container">
    <Sidebar
      :sessions="sessions"
      :current-thread-id="currentThreadId"
      @new-session="handleNewSession"
      @switch-session="handleSwitchSession"
      @clear-session="handleClearSession"
    />
    <ChatContainer
      :thread-id="currentThreadId"
      @update-session-id="updateSessionId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Sidebar from './components/Sidebar.vue';
import ChatContainer from './components/ChatContainer.vue';
import { clearHistory } from './api/chat';

interface Session {
  id: string;
  title: string;
}

const sessions = ref<Session[]>([]);
const currentThreadId = ref<string>('');

// 生成新的 threadId
const generateThreadId = (): string => {
  return Date.now() + '-' + Math.random().toString(36).substring(2, 8);
};

// 从 localStorage 加载会话数据
const loadFromLocalStorage = () => {
  try {
    const savedSessions = localStorage.getItem('omni_sessions');
    const savedCurrentThread = localStorage.getItem('omni_current_thread');

    if (savedSessions) {
      sessions.value = JSON.parse(savedSessions);
    }

    if (savedCurrentThread) {
      currentThreadId.value = savedCurrentThread;
    }

    // 如果没有会话，创建一个默认会话
    if (sessions.value.length === 0) {
      const defaultThreadId = generateThreadId();
      sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
      currentThreadId.value = defaultThreadId;
      saveToLocalStorage();
    }
  } catch (error) {
    console.error('加载会话数据失败:', error);
    // 发生错误时，创建默认会话
    const defaultThreadId = generateThreadId();
    sessions.value = [{ id: defaultThreadId, title: `会话 1` }];
    currentThreadId.value = defaultThreadId;
    saveToLocalStorage();
  }
};

// 保存会话数据到 localStorage
const saveToLocalStorage = () => {
  try {
    localStorage.setItem('omni_sessions', JSON.stringify(sessions.value));
    localStorage.setItem('omni_current_thread', currentThreadId.value);
  } catch (error) {
    console.error('保存会话数据失败:', error);
  }
};

// 处理新建会话
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

// 处理切换会话
const handleSwitchSession = (threadId: string) => {
  currentThreadId.value = threadId;
  saveToLocalStorage();
};

// 处理清空会话
const handleClearSession = async (threadId: string) => {
  try {
    // 调用后端接口清空会话
    await clearHistory(threadId);

    // 从会话列表中移除
    const index = sessions.value.findIndex(session => session.id === threadId);
    if (index !== -1) {
      sessions.value.splice(index, 1);
    }

    // 如果清空的是当前会话，切换到第一个会话或新建一个
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

// 更新会话ID
const updateSessionId = (oldThreadId: string, newThreadId: string) => {
  const session = sessions.value.find(s => s.id === oldThreadId);
  if (session) {
    session.id = newThreadId;
    session.title = `会话 ${sessions.value.length}`;
  }
  currentThreadId.value = newThreadId;
  saveToLocalStorage();
};

// 组件挂载时加载数据
onMounted(() => {
  loadFromLocalStorage();
});
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  background-color: #fff;
}

.app-container {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100% !important;
    height: 200px !important;
    border-right: none !important;
    border-bottom: 1px solid #e0e0e0;
  }
}
</style>

