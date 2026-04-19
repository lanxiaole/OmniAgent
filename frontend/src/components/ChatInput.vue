<template>
  <div class="chat-input-container">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      :disabled="loading"
      placeholder="输入消息，Enter 发送，Shift+Enter 换行"
      @keydown.enter="handleEnter"
    />
    <el-button
      type="primary"
      :loading="loading"
      :disabled="!inputText.trim() || loading"
      @click="send"
    >
      {{ loading ? '发送中...' : '发送' }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{ loading?: boolean }>()
const emit = defineEmits<{ (e: 'send', message: string): void }>()
const inputText = ref('')
const send = () => {
  const msg = inputText.value.trim()
  if (!msg || props.loading) return
  emit('send', msg)
  inputText.value = ''
}
const handleEnter = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<style scoped>
.chat-input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: white;
  border-radius: 24px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
:deep(.el-textarea__inner) {
  border: none;
  padding: 8px 0;
  font-size: 15px;
  resize: none;
  box-shadow: none;
}
:deep(.el-textarea__inner:focus) {
  box-shadow: none;
  border: none;
}
.el-button {
  border-radius: 20px;
  padding: 8px 20px;
  background-color: #409eff;
  border: none;
}
.el-button:hover {
  background-color: #66b1ff;
}
</style>
