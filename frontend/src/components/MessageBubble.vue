<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-bubble">
      {{ message.content }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '@/types/chat'
defineProps<{ message: Message }>()
</script>

<style scoped>
.message-wrapper {
  display: flex;
  margin-bottom: 12px;
}
.message-wrapper.user {
  justify-content: flex-end;
}
.message-wrapper.assistant {
  justify-content: flex-start;
}
.message-bubble {
  max-width: 75%;
  padding: 10px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.user .message-bubble {
  background-color: #409eff;
  color: white;
}
.assistant .message-bubble {
  background-color: #f0f0f0;
  color: #333;
}
</style>
