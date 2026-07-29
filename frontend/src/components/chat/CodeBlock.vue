<template>
  <div class="code-block-wrapper">
    <div class="code-block-header">
      <div class="code-lang">{{ language }}</div>
      <div class="code-actions">
        <button
          class="copy-btn"
          :class="{ copied }"
          @click="handleCopy"
          :title="copied ? '已复制' : '复制代码'"
        >
          <el-icon size="14">
            <Check v-if="copied" />
            <CopyDocument v-else />
          </el-icon>
          <span>{{ copied ? '已复制' : '复制' }}</span>
        </button>
      </div>
    </div>
    <pre class="hljs code-block" :data-lang="language"><code :class="`language-${language}`" v-html="highlightedCode"></code></pre>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import hljs from 'highlight.js';
import { CopyDocument, Check } from '@element-plus/icons-vue';
import { copyToClipboard } from '@/utils/markdown';

interface Props {
  code: string;
  language?: string;
}

const props = withDefaults(defineProps<Props>(), {
  language: 'text',
});

const copied = ref(false);

const language = computed(() => {
  const lang = (props.language || '').toLowerCase();
  if (lang && hljs.getLanguage(lang)) return lang;
  return 'plaintext';
});

const highlightedCode = computed(() => {
  try {
    return hljs.highlight(props.code, {
      language: language.value,
      ignoreIllegals: true,
    }).value;
  } catch {
    return escapeHtml(props.code);
  }
});

const escapeHtml = (str: string): string =>
  str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c);

const handleCopy = async () => {
  const ok = await copyToClipboard(props.code);
  if (ok) {
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  }
};
</script>

<style scoped>
.code-block-wrapper {
  margin: 12px 0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  font-family: var(--font-mono);
}

.code-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background-color: var(--bg-card-hover);
  border-bottom: 1px solid var(--border-color);
}

.code-lang {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.code-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.copy-btn:hover {
  color: var(--text-primary);
  border-color: var(--border-color-strong);
}

.copy-btn.copied {
  color: var(--success);
  border-color: var(--success);
}

.code-block {
  margin: 0 !important;
  padding: 14px 16px !important;
  font-size: 13px !important;
  line-height: 1.6;
  overflow-x: auto;
  background: transparent !important;
}
</style>
