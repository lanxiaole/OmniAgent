<template>
  <div class="chat-container">
    <div class="chat-header">
      <span>OmniAgent</span>
    </div>
    <div class="message-list" ref="messageListRef">
      <MessageBubble v-for="(msg, index) in messages" :key="index" :message="msg" />
    </div>
    <div class="input-area">
      <ChatInput :loading="loading" @send="handleSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { sendMessageStream } from '@/api/chat'
import type { Message } from '@/types/chat'
import ChatInput from './ChatInput.vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{
  threadId: string
}>();

const messages = ref<Message[]>([]);
const loading = ref(false);
const messageListRef = ref<HTMLElement>();

// 打字机队列：全局状态
const typewriterQueue = ref<string[]>([]);
let typewriterTimer: ReturnType<typeof setInterval> | null = null;

// 打字机速度（毫秒/字），可调整此值改变速度
const TYPING_SPEED = 50;

/**
 * 启动打字机效果
 * @param assistantIndex 助手消息在 messages 数组中的索引
 */
const startTypewriter = (assistantIndex: number) => {
  if (typewriterTimer) return; // 已经在运行

  typewriterTimer = setInterval(() => {
    if (typewriterQueue.value.length === 0) {
      // 队列为空，停止定时器
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
      return;
    }

    // 取出队列第一个字符，追加到消息上
    const char = typewriterQueue.value.shift()!;
    const assistantMessage = messages.value[assistantIndex];
    if (assistantMessage) {
      assistantMessage.content += char;
      saveLocalHistory(props.threadId, messages.value);
      scrollToBottom();
    }
  }, TYPING_SPEED);
};

/**
 * 停止打字机效果并清空队列
 */
const stopTypewriter = () => {
  if (typewriterTimer) {
    clearInterval(typewriterTimer);
    typewriterTimer = null;
  }
  typewriterQueue.value = [];
};

const scrollToBottom = async () => {
  await nextTick();
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
};

// 从本地存储加载历史消息
const loadLocalHistory = (threadId: string): Message[] => {
  try {
    const storedMessages = localStorage.getItem(`omni_messages_${threadId}`);
    if (storedMessages) {
      return JSON.parse(storedMessages);
    }
  } catch (error) {
    console.error('加载本地历史消息失败:', error);
  }
  return [];
};

// 保存历史消息到本地存储
const saveLocalHistory = (threadId: string, msgs: Message[]) => {
  try {
    localStorage.setItem(`omni_messages_${threadId}`, JSON.stringify(msgs));
  } catch (error) {
    console.error('保存本地历史消息失败:', error);
  }
};

const loadHistory = (threadId: string) => {
  // 从本地存储加载历史消息
  const localMessages = loadLocalHistory(threadId);
  if (localMessages.length > 0) {
    messages.value = localMessages;
  } else {
    // 如果没有历史消息，显示欢迎消息
    messages.value = [{ role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
  }
  scrollToBottom();
};

const handleSend = async (userMessage: string) => {
  if (loading.value) return;

  // 1. 添加用户消息
  messages.value.push({ role: 'user', content: userMessage });
  saveLocalHistory(props.threadId, messages.value);
  await scrollToBottom();

  // 2. 添加空的助手消息占位
  const assistantMessageIndex = messages.value.length;
  messages.value.push({ role: 'assistant', content: '' });

  loading.value = true;

  try {
    // 3. 流式接收回复
    await sendMessageStream(
      userMessage,
      props.threadId,
      (token: string) => {
        // 将 token 拆成单个字符，加入打字机队列
        for (const char of token) {
          typewriterQueue.value.push(char);
        }
        // 启动打字机（如果尚未启动）
        startTypewriter(assistantMessageIndex);
      }
    );
  } catch (error) {
    console.error('流式发送失败:', error);
    stopTypewriter();
    const assistantMessage = messages.value[assistantMessageIndex];
    if (assistantMessage) {
      assistantMessage.content = '抱歉，服务暂时不可用，请稍后再试。';
      saveLocalHistory(props.threadId, messages.value);
    }
  } finally {
    loading.value = false;
    await scrollToBottom();
  }
};

// 当 threadId 变化时，重新加载历史消息
watch(
  () => props.threadId,
  (newThreadId) => {
    loadHistory(newThreadId);
  },
  { immediate: true }
);

// 组件挂载时加载历史消息
onMounted(() => {
  loadHistory(props.threadId);
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  flex: 1;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #eaeef2;
  font-weight: 500;
  font-size: 18px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.input-area {
  padding: 12px 16px 20px;
  background: #f5f7fa;
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
