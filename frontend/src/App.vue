<!--
  App.vue - 应用根组件
  布局结构：左侧会话列表（Sidebar）+ 右侧聊天区域（ChatContainer）
  负责初始化全局状态和子组件通信
-->
<template>
  <div class="app-container">
    <!-- 侧边栏：会话列表，处理新会话、切换、清空、重命名操作 -->
    <Sidebar
      :sessions="sessions"
      :current-thread-id="currentThreadId"
      @new-session="sessionStore.newSession"
      @switch-session="sessionStore.switchSession"
      @clear-session="sessionStore.clearSession"
      @rename-session="sessionStore.renameSession"
    />
    <!-- 聊天容器：消息列表 + 输入框，处理消息发送、编辑等 -->
    <ChatContainer
      :thread-id="currentThreadId"
      @update-session-id="sessionStore.updateSessionId"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import Sidebar from './components/Sidebar.vue';
import ChatContainer from './components/ChatContainer.vue';
import { useSessionStore } from './stores/sessionStore';

// 初始化会话 Store，通过 storeToRefs 解构为响应式引用
const sessionStore = useSessionStore();
const { sessions, currentThreadId } = storeToRefs(sessionStore);

// 应用启动时初始化会话数据（从 localStorage 恢复）
onMounted(() => {
  sessionStore.init();
});
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

/* 响应式：小屏设备切换为垂直布局 */
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