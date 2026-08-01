<template>
  <div class="chat-view">
    <div class="chat-layout">
      <!-- 会话侧边栏：沿用现有 Sidebar 组件的会话管理能力 -->
      <aside class="chat-sidebar">
        <Sidebar
          :sessions="sessions"
          :current-thread-id="currentThreadId"
          @new-session="sessionStore.newSession"
          @switch-session="sessionStore.switchSession"
          @clear-session="sessionStore.clearSession"
          @rename-session="sessionStore.renameSession"
          @toggle-pin="sessionStore.togglePin"
        />
      </aside>

      <!-- 聊天主区域 -->
      <div class="chat-main">
        <ChatContainer
          :thread-id="currentThreadId"
          @update-session-id="sessionStore.updateSessionId"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import Sidebar from '@/components/Sidebar.vue';
import ChatContainer from '@/components/ChatContainer.vue';
import { useSessionStore } from '@/stores/sessionStore';
import { useModelStore } from '@/stores/modelStore';

const sessionStore = useSessionStore();
const modelStore = useModelStore();
const { sessions, currentThreadId } = storeToRefs(sessionStore);

onMounted(() => {
  sessionStore.init();
  modelStore.loadModels();
});
</script>

<style scoped>
.chat-view {
  width: 100%;
  height: 100%;
  background-color: var(--bg-card);
}

.chat-layout {
  display: flex;
  width: 100%;
  height: 100%;
}

.chat-sidebar {
  width: 260px;
  height: 100%;
  flex-shrink: 0;
  background-color: var(--bg-body);
  position: relative;
  overflow: hidden;
  z-index: 1;
}

/* 用阴影投影代替硬边框，分隔更柔和 */
.chat-sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: -1px;
  width: 1px;
  height: 100%;
  background: linear-gradient(
    180deg,
    transparent 0%,
    var(--border-color) 8%,
    var(--border-color) 92%,
    transparent 100%
  );
}

.chat-main {
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-card);
}

/* 响应式：小屏时隐藏会话侧边栏 */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }
}
</style>