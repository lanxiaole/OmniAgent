<template>
  <div class="chat-input-wrapper">
    <div class="chat-input-box" :class="{ focus: isFocused }">
      <textarea
        ref="textareaRef"
        class="chat-textarea"
        v-model="inputText"
        :disabled="loading"
        :placeholder="placeholderText"
        rows="1"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @input="autoResize"
        @keydown="handleKeydown"
      />

      <div class="chat-input-actions">
        <div class="action-left"></div>

        <div class="action-right">
          <button
            class="send-btn"
            :class="loading ? 'abort' : 'primary'"
            :disabled="!inputText.trim() && !loading"
            @click="handleButtonClick"
            type="button"
          >
            <template v-if="loading">
              <el-icon :size="18"><VideoPause /></el-icon>
              <span>停止</span>
            </template>
            <template v-else>
              <span>发送</span>
              <el-icon :size="18"><Promotion /></el-icon>
            </template>
          </button>
        </div>
      </div>
    </div>

    <p class="input-hint">
      OmniAgent 支持调用多种工具（查询天气、网络搜索、读写文件、执行代码、知识库检索等），生成内容请自行核实。
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue';
import { Promotion, VideoPause } from '@element-plus/icons-vue';

interface Props {
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  (e: 'send', message: string): void;
  (e: 'abort'): void;
}>();

const inputText = ref('');
const isFocused = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const placeholderText = computed(() =>
  props.loading
    ? '正在生成回复…（可随时点击「停止」按钮中断）'
    : '告诉 OmniAgent 你要做什么… Enter 发送，Shift + Enter 换行'
);

const autoResize = async () => {
  await nextTick();
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  const next = Math.min(el.scrollHeight, 240);
  el.style.height = `${next}px`;
};

const send = () => {
  const msg = inputText.value.trim();
  if (!msg) return;
  emit('send', msg);
  inputText.value = '';
  autoResize();
};

const handleButtonClick = () => {
  if (props.loading) {
    emit('abort');
  } else {
    send();
  }
};

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (props.loading) return;
    send();
  }
};
</script>

<style scoped>
.chat-input-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 0 8px;
}

.chat-input-box {
  width: min(100%, 860px);
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 10px 12px 6px;
  box-shadow: var(--shadow-sm);
  transition: all 180ms ease;
}

.chat-input-box.focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08), var(--shadow-md);
}

.chat-textarea {
  width: 100%;
  min-height: 28px;
  max-height: 240px;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-md);
  line-height: 1.65;
  padding: 6px 6px 8px;
}

.chat-textarea::placeholder {
  color: var(--text-tertiary);
}

.chat-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 2px 2px;
}

.action-left {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.quick-tool {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.quick-tool:hover {
  background-color: var(--bg-sidebar-hover);
}

.action-right {
  display: inline-flex;
  align-items: center;
}

.send-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: var(--radius-full);
  border: 1px solid transparent;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.send-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.18);
}

.send-btn.primary:hover {
  filter: brightness(1.04);
  transform: translateY(-0.5px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
}

.send-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
  filter: none;
}

.send-btn.abort {
  background: var(--bg-card-hover);
  color: var(--danger);
  border-color: rgba(239, 68, 68, 0.3);
}

.send-btn.abort:hover {
  background: rgba(239, 68, 68, 0.06);
}

.input-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  text-align: center;
}
</style>
