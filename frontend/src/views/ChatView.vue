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

const sessionStore = useSessionStore();
const { sessions, currentThreadId } = storeToRefs(sessionStore);

onMounted(() => {
  sessionStore.init();
});
</script>

<style scoped>
.chat-view {
  width: 100%;
  height: 100%;
  /* 统一白色背景，使侧边栏和主区域融为一体 */
  background-color: var(--bg-card);
}

.chat-layout {
  display: flex;
  width: 100%;
  height: 100%;
}

.chat-sidebar {
  width: 280px;
  height: 100%;
  flex-shrink: 0;
  /* 同样的白色背景，消除割裂感 */
  background-color: var(--bg-card);
  /* 使用更柔和的分割线 */
  border-right: 1px solid var(--border-color-light);
  overflow: hidden;
}

.chat-main {
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-card);
}

/* 响应式：小屏时隐藏会话侧边栏（后续可加入移动端抽屉交互） */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }
}
</style>
