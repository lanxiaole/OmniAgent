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
import Sidebar from './components/Sidebar.vue';
import ChatContainer from './components/ChatContainer.vue';
import { useSessionManager } from './composables/useSessionManager';

const { sessions, currentThreadId, handleNewSession, handleSwitchSession, handleClearSession, updateSessionId } = useSessionManager();
</script>

<style>
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
