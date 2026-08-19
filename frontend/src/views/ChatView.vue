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
        <transition name="fade" mode="out-in">
          <!-- 会话切换中：显示加载占位，避免"选择场景"页覆盖对话内容 -->
          <div v-if="isSessionSwitching" key="switching" class="chat-switching">
            <div class="switching-spinner"></div>
            <span class="switching-text">正在切换会话…</span>
          </div>
          <!-- 启动页：无消息时显示，key 绑定 currentThreadId 确保每次切换会话都重新挂载 -->
          <StartPage
            v-else-if="!hasMessages"
            :key="'start-' + currentThreadId"
            @send="handleFirstSend"
            @scenario-selected="handleScenarioSelected"
          />
          <!-- 对话页：有消息时显示 -->
          <ChatContainer
            v-else
            key="chat"
            :thread-id="currentThreadId"
            :scenario-name="currentScenarioName"
            @update-session-id="handleUpdateSessionId"
          />
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, nextTick } from 'vue';
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

// 会话切换中状态：加载新会话历史期间不显示 StartPage，避免"选择场景"覆盖对话内容
const isSessionSwitching = ref(false);
// 切换令牌：仅最后一次切换的加载完成才结束"切换中"状态（防快速连续切换竞态）
let switchToken = 0;
// 标记下一次 currentThreadId 变化来自 updateSessionId（编辑消息），跳过切换逻辑
let suppressSwitchWatch = false;

/**
 * 处理编辑消息后的 thread_id 更新
 * 仅同步会话引用，不触发"切换会话"逻辑（消息内容未变，无需重新加载历史）
 */
const handleUpdateSessionId = (oldThreadId: string, newThreadId: string) => {
  suppressSwitchWatch = true;
  sessionStore.updateSessionId(oldThreadId, newThreadId);
};

/**
 * 统一处理 currentThreadId 变化（切换会话 / 新建会话）
 *
 * 注意：该逻辑必须放在 ChatView 层，而不是 ChatContainer 内部。
 * 因为 ChatContainer 只在"有消息"时渲染，一旦切换到空会话（或加载历史期间）
 * 它就会卸载，其内部 watch 随之失效 —— 导致"选择场景"页显示期间再切换会话
 * 永远不会加载新会话的历史消息（对话页面被一直覆盖）。
 */
watch(currentThreadId, (newId, oldId) => {
  if (!newId || newId === oldId) return;
  // 编辑消息触发的 thread_id 更新：跳过会话切换逻辑
  if (suppressSwitchWatch) {
    suppressSwitchWatch = false;
    return;
  }

  // 保存当前会话消息到本地，清空并加载新会话历史
  if (oldId) {
    chatStore.saveLocalHistory(oldId, chatStore.messages);
  }
  const token = ++switchToken;
  isSessionSwitching.value = true;
  chatStore.clearMessages();
  chatStore.loadHistory(newId).finally(() => {
    if (token === switchToken) {
      // 使用 nextTick 确保 DOM 更新完成后再结束切换状态
      // 避免 StartPage 组件在切换动画完成前就被渲染
      nextTick(() => {
        if (token === switchToken) {
          isSessionSwitching.value = false;
        }
      });
    }
  });
});

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

/* 切换会话时的加载占位：避免选择场景页覆盖对话内容 */
.chat-switching {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  background-color: var(--bg-card);
}

.switching-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border-color, #e4e7ed);
  border-top-color: var(--primary-500, #409eff);
  border-radius: 50%;
  animation: chat-switching-spin 0.8s linear infinite;
}

.switching-text {
  font-size: 13px;
  color: var(--text-tertiary, #909399);
}

@keyframes chat-switching-spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式：小屏时隐藏会话侧边栏 */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }
}
</style>