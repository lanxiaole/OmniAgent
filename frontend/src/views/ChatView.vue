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
        <!-- 启动页：无消息时显示 -->
        <transition name="fade" mode="out-in">
          <StartPage
            v-if="!hasMessages"
            key="start"
            @send="handleFirstSend"
            @scenario-selected="handleScenarioSelected"
          />
          <!-- 对话页：有消息时显示 -->
          <ChatContainer
            v-else
            key="chat"
            :thread-id="currentThreadId"
            :scenario-name="currentScenarioName"
            @update-session-id="sessionStore.updateSessionId"
          />
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import Sidebar from '@/components/Sidebar.vue';
import ChatContainer from '@/components/ChatContainer.vue';
import StartPage from '@/components/chat/StartPage.vue';
import { useSessionStore } from '@/stores/sessionStore';
import { useChatStore } from '@/stores/chatStore';
import { useModelStore } from '@/stores/modelStore';
import { getScenarios, getCurrentScenario } from '@/api/settings';
import type { ScenarioPreset } from '@/types/settings';

const sessionStore = useSessionStore();
const chatStore = useChatStore();
const modelStore = useModelStore();
const { sessions, currentThreadId } = storeToRefs(sessionStore);

// 当前场景名称（用于 ChatInput 的动态 placeholder）
const currentScenarioName = ref('');
// 场景预设列表（用于根据场景 ID 查找名称）
const scenarioPresets = ref<ScenarioPreset[]>([]);

// 是否有消息（驱动启动页/对话页切换）
const hasMessages = computed(() => chatStore.hasMessages);

/**
 * 处理 StartPage 发送的第一条消息
 * 发送成功后，hasMessages 变为 true，自动切换到对话页
 */
const handleFirstSend = async (message: string) => {
  await chatStore.sendMessage(message, currentThreadId.value);
};

/**
 * 场景切换后的回调
 */
const handleScenarioSelected = async (scenarioId: string) => {
  const preset = scenarioPresets.value.find(p => p.id === scenarioId);
  if (preset) {
    currentScenarioName.value = preset.name;
  }
};

/**
 * 加载场景列表和当前场景
 */
const loadScenarioInfo = async () => {
  try {
    const [presets, currentId] = await Promise.all([
      getScenarios(),
      getCurrentScenario(),
    ]);
    scenarioPresets.value = presets;
    const active = presets.find(p => p.id === currentId);
    if (active) {
      currentScenarioName.value = active.name;
    }
  } catch (e) {
    // 静默失败，不影响主功能
    console.warn('加载场景信息失败:', e);
  }
};

// 加载历史消息：页面刷新时从后端/localStorage 恢复当前会话消息
// 不依赖 hasMessages，因为刷新后 store 的消息为空
const loadHistoryIfNeeded = () => {
  if (currentThreadId.value) {
    chatStore.loadHistory(currentThreadId.value);
  }
};

onMounted(() => {
  sessionStore.init();
  modelStore.loadModels();
  loadScenarioInfo();
  loadHistoryIfNeeded();
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

/* 淡入淡出过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式：小屏时隐藏会话侧边栏 */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }
}
</style>