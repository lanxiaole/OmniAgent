<template>
  <div class="chat-container">
    <div class="chat-header">
      <span>OmniAgent</span>
    </div>
    <div class="message-list" ref="messageListRef">
      <MessageItem
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :loading="loading"
        :editing="editingMessageId === msg.id"
        :editing-content="editingContent"
        @update:editing-content="editingContent = $event"
        @save-edit="saveEdit(msg.id)"
        @cancel-edit="cancelEdit"
        @start-edit="editMessage(msg.id)"
      />
    </div>
    <div class="input-area">
      <ChatInput :loading="loading" @send="sendOrAbort" @abort="abortStream" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { sendMessageStream } from '@/api/chat'
import type { Message } from '@/types/chat'
import ChatInput from './ChatInput.vue'
import MessageItem from './MessageItem.vue'

const props = defineProps<{
  threadId: string
}>();

const emit = defineEmits<{ 'update-session-id': [oldThreadId: string, newThreadId: string] }>();

// 当前会话ID
const currentThreadId = ref(props.threadId);

// 监听threadId变化
watch(() => props.threadId, (newThreadId) => {
  currentThreadId.value = newThreadId;
  loadHistory(newThreadId);
});

const generateMessageId = () => { return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10); };

const generateThreadId = (): string => {
  return Date.now() + '-' + Math.random().toString(36).substring(2, 8);
};

const messages = ref<Message[]>([]);
const loading = ref(false);
const messageListRef = ref<HTMLElement>();
const abortController = ref<AbortController | null>(null);
const editingMessageId = ref<string | null>(null);
const editingContent = ref('');

// 打字机队列：全局状态
const typewriterQueue = ref<string[]>([]);
let typewriterTimer: ReturnType<typeof setInterval> | null = null;

// 打字机速度（毫秒/字），可调整此值改变速度
const TYPING_SPEED = 20;

/**
 * 启动打字机效果
 * @param assistantIndex 助手消息在 messages 数组中的索引
 */
const startTypewriter = (assistantIndex: number) => {
  if (typewriterTimer) return; // 已经在运行

  typewriterTimer = setInterval(async () => {
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
      await scrollToBottom();
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
    messages.value = [{ id: generateMessageId(), role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }];
  }
  scrollToBottom();
};

const sendOrAbort = (message: string) => {
  if (loading.value) {
    abortStream();
  } else {
    handleSend(message);
  }
};

const abortStream = async () => {
  // 1. 中止网络请求
  if (abortController.value) {
    abortController.value.abort();
    abortController.value = null;
  }

  // 2. 停止打字机
  stopTypewriter();

  // 3. 清理空的助手占位消息
  if (messages.value.length > 0) {
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
      messages.value.pop();
    }
  }

  // 4. 保存并重置状态
  saveLocalHistory(props.threadId, messages.value);
  loading.value = false;
};

const handleSend = async (userMessage: string) => {
  if (loading.value) return;

  // 【新增】前置清理：如果上一条消息是空的助手消息，干掉它
  if (messages.value.length > 0) {
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.trim() === '') {
      messages.value.pop();
    }
  }

  // 中止前一个请求
  if (abortController.value) {
    abortController.value.abort();
    abortController.value = null;
  }

  // 1. 添加用户消息
  messages.value.push({ id: generateMessageId(), role: 'user', content: userMessage });
  saveLocalHistory(props.threadId, messages.value);
  await scrollToBottom();

  // 2. 添加空的助手消息占位
  const assistantMessageIndex = messages.value.length;
  messages.value.push({ id: generateMessageId(), role: 'assistant', content: '' });

  loading.value = true;
  await scrollToBottom();

  try {
    // 创建新的 AbortController
    abortController.value = new AbortController();

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
      },
      abortController.value.signal
    );
  } catch (err: unknown) {
    if (typeof err === 'object' && err !== null && 'name' in err && err.name === 'AbortError') {
      console.log('用户主动中止了请求。');
      return; // 用户主动中止，不显示错误
    }
    console.error('流式发送失败:', err);
    stopTypewriter();
    const assistantMessage = messages.value[assistantMessageIndex];
    if (assistantMessage) {
      assistantMessage.content = '抱歉，服务暂时不可用，请稍后再试。';
      saveLocalHistory(props.threadId, messages.value);
    }
  } finally {
    abortController.value = null; // 请求结束后无论成功与否，清理 controller
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
  loadHistory(currentThreadId.value);
});

// 编辑消息
const editMessage = (messageId: string) => {
  // 如果 AI 正在回复，不允许编辑
  if (loading.value) return;

  // 找到要编辑的消息
  const msg = messages.value.find(m => m.id === messageId);
  if (!msg || msg.role !== 'user') return;

  // 设置编辑状态
  editingMessageId.value = messageId;
  editingContent.value = msg.content;
};

// 取消编辑
const cancelEdit = () => {
  editingMessageId.value = null;
  editingContent.value = '';
};

// 保存编辑
const saveEdit = async (messageId: string) => {
  if (loading.value) return;

  const newContent = editingContent.value.trim();
  if (!newContent) return;

  const editIndex = messages.value.findIndex(m => m.id === messageId);
  if (editIndex === -1) return;

  const editedMessage = messages.value[editIndex];
  if (!editedMessage) return;

  const oldContent = editedMessage.content;
  if (oldContent === newContent) {
    cancelEdit();
    return;
  }

  // 1. 截断：保留被编辑消息之前的干净历史
  const cleanHistory = messages.value.slice(0, editIndex);

  // 2. 生成全新 thread_id，彻底重置后端上下文
  const newThreadId = generateThreadId();
  const oldThreadId = props.threadId;

  // 3. 把干净历史迁移到新 thread_id 下
  localStorage.setItem(`omni_messages_${newThreadId}`, JSON.stringify(cleanHistory));

  // 4. 删除旧 thread_id 的历史
  localStorage.removeItem(`omni_messages_${oldThreadId}`);

  // 5. 更新 messages 为本地的干净历史
  messages.value = [...cleanHistory];

  // 6. 通知 App.vue 更新 thread_id
  emit('update-session-id', oldThreadId, newThreadId);

  // 7. 退出编辑模式，保存状态
  cancelEdit();
  saveLocalHistory(newThreadId, messages.value);

  // 8. 等待 threadId prop 更新后，用新内容重新发送
  await nextTick();
  await handleSend(newContent);
};
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
