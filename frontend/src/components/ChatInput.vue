<template>
  <div class="chat-input-wrapper">
    <div class="chat-input-box" :class="{ focus: isFocused }">
      <!-- 已上传附件列表 -->
      <div v-if="attachments.length > 0" class="attachment-list">
        <el-tag
          v-for="(file, index) in attachments"
          :key="file.path"
          closable
          :type="uploading ? 'info' : 'primary'"
          @close="removeAttachment(index)"
          class="attachment-tag"
        >
          📎 {{ file.name }}
          <span class="attachment-size">{{ formatFileSize(file.size) }}</span>
        </el-tag>
      </div>

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
        <div class="action-left">
          <!-- 附件上传按钮 -->
          <button
            class="attachment-btn"
            @click="triggerFileUpload"
            :disabled="loading || uploading"
            title="上传文件"
            type="button"
          >
            <el-icon :size="18"><Paperclip /></el-icon>
          </button>
          <input
            ref="fileInputRef"
            type="file"
            style="display: none"
            @change="handleFileSelected"
            accept=".txt,.md,.py,.json,.csv,.pdf,.png,.jpg,.jpeg,.xlsx,.docx"
          />
        </div>

        <div class="action-right">
          <ModelSelector />
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
import ModelSelector from './chat/ModelSelector.vue';
import { Promotion, VideoPause, Paperclip } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

interface Props {
  loading?: boolean;
  threadId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  threadId: '',
});

const emit = defineEmits<{
  (e: 'send', message: string): void;
  (e: 'abort'): void;
}>();

const inputText = ref('');
const isFocused = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

// 附件相关状态
const attachments = ref<{ name: string; path: string; size: number }[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);

const placeholderText = computed(() =>
  props.loading
    ? '正在生成回复…（可随时点击「停止」按钮中断）'
    : '告诉 OmniAgent 你要做什么… Enter 发送，Shift + Enter 换行'
);

/** 格式化文件大小 */
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const autoResize = async () => {
  await nextTick();
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  const next = Math.min(el.scrollHeight, 240);
  el.style.height = `${next}px`;
};

/** 触发文件选择器 */
const triggerFileUpload = () => {
  fileInputRef.value?.click();
};

/** 上传单个文件到后端 */
const uploadFile = async (file: File) => {
  // 限制文件大小 20MB
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB');
    return;
  }

  if (!props.threadId) {
    ElMessage.error('会话未就绪，请稍后再试');
    return;
  }

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('thread_id', props.threadId);

    const response = await fetch('/api/chat/upload', {
      method: 'POST',
      body: formData,
    });
    const result = await response.json();

    if (result.success) {
      attachments.value.push({
        name: result.name,
        path: result.path,
        size: result.size,
      });
      ElMessage.success(`已上传：${result.name}`);
    } else {
      ElMessage.error(result.message || result.detail || '上传失败');
    }
  } catch {
    ElMessage.error('上传失败，请重试');
  } finally {
    uploading.value = false;
  }
};

/** 处理文件选择 */
const handleFileSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  await uploadFile(file);
  input.value = '';
};

/** 移除附件 */
const removeAttachment = (index: number) => {
  attachments.value.splice(index, 1);
};

const send = () => {
  const msg = inputText.value.trim();
  if (!msg) return;

  // 如果有附件，在消息末尾追加附件路径信息供 Agent 读取
  let fullMessage = msg;
  if (attachments.value.length > 0) {
    const fileList = attachments.value
      .map(f => `  - ${f.name} (路径: ${f.path})`)
      .join('\n');
    fullMessage += `\n\n[已上传文件]\n${fileList}`;
    attachments.value = [];  // 发送后清空附件
  }

  emit('send', fullMessage);
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
  padding: 8px 0 0;
}

.chat-input-box {
  width: min(100%, 960px);
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 10px 12px 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: all 180ms ease;
}

.chat-input-box.focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08), 0 4px 16px rgba(37, 99, 235, 0.12);
}

/* 附件列表 */
.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px 6px 8px;
  border-bottom: 1px solid var(--border-color-light);
  margin-bottom: 4px;
}

.attachment-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.attachment-size {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 2px;
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

/* 附件上传按钮 */
.attachment-btn {
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
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.attachment-btn:hover {
  background-color: var(--bg-sidebar-hover);
  color: var(--primary-500);
}

.attachment-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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