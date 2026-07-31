<template>
  <div class="markdown-renderer" ref="refHost">
    <div v-if="plain" class="plain-text">{{ content }}</div>
    <div v-else class="rich-text" v-html="safeHtml"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, nextTick, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { renderMarkdown, copyToClipboard } from '@/utils/markdown';

interface Props {
  content: string;
  /** 如果为 true，将以纯文本方式展示（用于未完成的流式输出） */
  plain?: boolean;
  /** 流式输出中：始终渲染 Markdown，仅处理未闭合代码块 */
  streaming?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  plain: false,
  streaming: false,
});

/** 流式场景下，去掉末尾未闭合的代码围栏，避免后续内容都变成代码 */
const safeStreamingContent = (raw: string): string => {
  const parts = raw.split('```');
  // 偶数 parts = 奇数个 ``` = 最后一个未闭合，去掉
  if (parts.length > 1 && parts.length % 2 === 0) {
    return parts.slice(0, -1).join('```');
  }
  return raw;
};

const safeHtml = computed(() => {
  if (props.plain) return '';
  const text = props.streaming ? safeStreamingContent(props.content) : props.content;
  return renderMarkdown(text);
});
const refHost = ref<HTMLElement | null>(null);

/**
 * 接管代码块中的复制按钮（renderMarkdown 渲染出的 pre.code-block）
 * 由于 CodeBlock 组件只在手写场景使用，这里用原生 DOM 操作给 pre 加个复制入口
 */
const attachCopyButtons = () => {
  if (!refHost.value) return;
  const pres = refHost.value.querySelectorAll<HTMLPreElement>('pre.code-block');
  pres.forEach(pre => {
    if (pre.dataset.copyAttached === '1') return;
    pre.dataset.copyAttached = '1';

    const wrapper = document.createElement('div');
    wrapper.className = '__md_code_wrapper';
    wrapper.style.cssText =
      'position:relative;border-radius:12px;overflow:hidden;margin:12px 0;border:1px solid var(--border-color);background:var(--bg-page);';

    const header = document.createElement('div');
    header.style.cssText =
      'display:flex;align-items:center;justify-content:space-between;padding:8px 14px;background:var(--bg-card-hover);border-bottom:1px solid var(--border-color);';
    const lang = document.createElement('span');
    lang.textContent = pre.dataset.lang?.toUpperCase() ?? 'CODE';
    lang.style.cssText =
      'font-size:11px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;';

    const copyBtn = document.createElement('button');
    copyBtn.textContent = '复制';
    copyBtn.style.cssText =
      'display:inline-flex;align-items:center;gap:4px;height:24px;padding:0 10px;border:1px solid var(--border-color);border-radius:6px;background:var(--bg-card);color:var(--text-secondary);font-size:11px;cursor:pointer;transition:all 150ms ease;';
    copyBtn.addEventListener('mouseenter', () => {
      copyBtn.style.color = 'var(--text-primary)';
      copyBtn.style.borderColor = 'var(--border-color-strong)';
    });
    copyBtn.addEventListener('mouseleave', () => {
      if (copyBtn.dataset.copied !== '1') {
        copyBtn.style.color = 'var(--text-secondary)';
        copyBtn.style.borderColor = 'var(--border-color)';
      }
    });

    const codeEl = pre.querySelector('code');
    copyBtn.addEventListener('click', async () => {
      const text = codeEl?.textContent ?? pre.textContent ?? '';
      const ok = await copyToClipboard(text);
      if (ok) {
        copyBtn.dataset.copied = '1';
        copyBtn.textContent = '已复制';
        copyBtn.style.color = 'var(--success)';
        copyBtn.style.borderColor = 'var(--success)';
        ElMessage({ message: '代码已复制', type: 'success', duration: 1200 });
        setTimeout(() => {
          copyBtn.dataset.copied = '';
          copyBtn.textContent = '复制';
          copyBtn.style.color = 'var(--text-secondary)';
          copyBtn.style.borderColor = 'var(--border-color)';
        }, 2000);
      } else {
        ElMessage({ message: '复制失败', type: 'error', duration: 1500 });
      }
    });

    header.appendChild(lang);
    header.appendChild(copyBtn);

    pre.parentNode?.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
    pre.style.cssText =
      'margin:0!important;padding:14px 16px!important;overflow-x:auto;background:transparent!important;font-family:var(--font-mono);font-size:13px;line-height:1.6;';
  });
};

onMounted(async () => {
  await nextTick();
  attachCopyButtons();
});
</script>

<style scoped>
.markdown-renderer {
  width: 100%;
  word-break: break-word;
}

.plain-text {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: var(--text-md);
}

.rich-text {
  line-height: 1.75;
  font-size: var(--text-md);
}

.rich-text :deep(p) {
  margin: 0 0 14px;
}

.rich-text :deep(p:last-child) {
  margin-bottom: 0;
}

.rich-text :deep(h1),
.rich-text :deep(h2),
.rich-text :deep(h3),
.rich-text :deep(h4) {
  margin: 20px 0 10px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.rich-text :deep(h1) {
  font-size: 22px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color-light);
}

.rich-text :deep(h2) {
  font-size: 19px;
}

.rich-text :deep(h3) {
  font-size: 16.5px;
}

.rich-text :deep(ul),
.rich-text :deep(ol) {
  margin: 0 0 14px;
  padding-left: 22px;
}

.rich-text :deep(li) {
  margin: 4px 0;
}

.rich-text :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 14px;
  border-left: 3px solid var(--primary-500);
  background-color: var(--primary-50);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-secondary);
}

[data-theme='dark'] .rich-text :deep(blockquote) {
  background-color: rgba(59, 130, 246, 0.1);
}

.rich-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  font-size: var(--text-sm);
}

.rich-text :deep(th) {
  text-align: left;
  padding: 10px 12px;
  background-color: var(--bg-card-hover);
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
}

.rich-text :deep(td) {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.rich-text :deep(tr:last-child td) {
  border-bottom: none;
}

.rich-text :deep(a) {
  color: var(--text-link);
  text-decoration: none;
  border-bottom: 1px dashed rgba(37, 99, 235, 0.3);
  padding-bottom: 1px;
}

.rich-text :deep(a:hover) {
  border-bottom-style: solid;
}

.rich-text :deep(code:not(pre code)) {
  font-family: var(--font-mono);
  font-size: 12.5px;
  padding: 1px 6px;
  margin: 0 1px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-page);
  border: 1px solid var(--border-color-light);
  color: #dc2626;
}

[data-theme='dark'] .rich-text :deep(code:not(pre code)) {
  color: #fca5a5;
}

.rich-text :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color-light);
  margin: 20px 0;
}

.rich-text :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin: 12px 0;
}
</style>
