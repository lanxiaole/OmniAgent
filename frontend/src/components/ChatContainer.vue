<template>
  <div class="chat-container">
    <div class="chat-header">
      <span>OmniAgent</span>
      <el-button text @click="clearChat">清空对话</el-button>
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
import { ref, nextTick } from 'vue'
import { sendMessage } from '@/api/chat'
import type { Message } from '@/types/chat'
import ChatInput from './ChatInput.vue'
import MessageBubble from './MessageBubble.vue'

const messages = ref<Message[]>([
  { role: 'assistant', content: '你好！我是 OmniAgent，有什么可以帮你？' }
])
const loading = ref(false)
const messageListRef = ref<HTMLElement>()

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const handleSend = async (userMessage: string) => {
  if (loading.value) return
  // 添加用户消息
  messages.value.push({ role: 'user', content: userMessage })
  await scrollToBottom()
  loading.value = true
  try {
    const reply = await sendMessage(userMessage, 'web_user')
    messages.value.push({ role: 'assistant', content: reply })
  } catch {
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后再试。' })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = [{ role: 'assistant', content: '对话已清空，有什么可以帮你？' }]
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
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
</style>
