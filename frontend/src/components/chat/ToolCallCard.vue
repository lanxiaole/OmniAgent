<template>
  <div class="tool-card" :class="[status, { expanded: localOpen }]">
    <button class="tool-card-header" @click="handleToggle">
      <div class="tool-icon" :class="meta.category">
        <el-icon size="18">
          <component :is="meta.iconComponent" />
        </el-icon>
      </div>
      <div class="tool-info">
        <div class="tool-name">
          <span class="tool-label">{{ displayName }}</span>
          <span v-if="statusText" class="tool-status" :class="status">{{ statusText }}</span>
        </div>
        <div class="tool-desc">{{ meta.description }}</div>
      </div>
      <div class="tool-meta-right">
        <span v-if="durationText" class="tool-duration">{{ durationText }}</span>
        <el-icon class="tool-chevron" :class="{ rotated: localOpen }" size="16">
          <ArrowDown />
        </el-icon>
      </div>
    </button>

    <transition name="tool-expand">
      <div v-show="localOpen" class="tool-card-body">
        <div v-if="argsText" class="tool-section">
          <div class="tool-section-label">
            <el-icon size="14"><EditPen /></el-icon>
            <span>参数</span>
          </div>
          <pre class="tool-section-content" v-if="argsType === 'json'"><code>{{ argsText }}</code></pre>
          <div class="tool-section-content" v-else>{{ argsText }}</div>
        </div>

        <div v-if="errorDisplay" class="tool-section error">
          <div class="tool-section-label">
            <el-icon size="14"><WarningFilled /></el-icon>
            <span>错误</span>
          </div>
          <pre class="tool-section-content error-text"><code>{{ errorDisplay }}</code></pre>
        </div>

        <div v-if="resultText && (status === 'success' || status === 'error')" class="tool-section">
          <div class="tool-section-label">
            <el-icon size="14"><CircleCheckFilled /></el-icon>
            <span>结果</span>
          </div>
          <pre class="tool-section-content" v-if="resultIsJson"><code>{{ resultPretty }}</code></pre>
          <div class="tool-section-content" v-else v-html="renderedResultHtml"></div>
        </div>

        <div v-if="status === 'running' || status === 'pending'" class="tool-section">
          <div class="tool-progress">
            <div class="progress-track">
              <div class="progress-bar"></div>
            </div>
            <span class="progress-text">{{ status === 'running' ? '执行中…' : '待执行' }}</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, markRaw } from 'vue';
import {
  ArrowDown,
  EditPen,
  WarningFilled,
  CircleCheckFilled,
  // 图标池：meta.icon 字符串转组件用
  Clock,
  Collection,
  Sunny,
  Cpu,
  Document,
  FolderOpened,
  Search,
  Files,
  Link,
  MagicStick,
} from '@element-plus/icons-vue';
import type { ToolCall, ToolCallStatus } from '@/types/chat';
import type { ToolCategory } from '@/utils/markdown';
import {
  getToolMeta,
  formatToolArgs,
  formatDuration,
  renderMarkdown,
  stringifyResult,
  looksLikeJson,
  formatError,
} from '@/utils/markdown';

/** Element Plus 图标名 → 组件对象的映射池 */
const ICON_POOL: Record<string, unknown> = {
  Clock: markRaw(Clock),
  Collection: markRaw(Collection),
  Sunny: markRaw(Sunny),
  Cpu: markRaw(Cpu),
  Document: markRaw(Document),
  EditPen: markRaw(EditPen),
  FolderOpened: markRaw(FolderOpened),
  Search: markRaw(Search),
  Files: markRaw(Files),
  Link: markRaw(Link),
  MagicStick: markRaw(MagicStick),
};

interface Props extends ToolCall {}

const props = defineProps<Props>();

/** 工具元数据（来自本地注册表，缺省时给占位） */
const toolMetaBase = computed(() => getToolMeta(props.name));

/** 合并 ToolCall 自身的 category 覆盖默认 */
const meta = computed(() => {
  const base = toolMetaBase.value;
  const category: ToolCategory = (props.category as ToolCategory) ?? base.category ?? 'other';
  const iconName = base.icon || 'MagicStick';
  return {
    name: base.name,
    label: base.label,
    description: base.description,
    category,
    iconComponent: (ICON_POOL[iconName] ?? ICON_POOL.MagicStick) as any,
  };
});

/** 展示用名称：用户自定义 displayName > 注册表 label > 原始 name */
const displayName = computed(
  () => props.displayName?.trim() || meta.value.label || props.name || '未命名工具'
);

const statusText = computed(() => {
  const map: Record<ToolCallStatus, string> = {
    pending: '待执行',
    running: '执行中',
    success: '成功',
    error: '失败',
  };
  return map[props.status];
});

/** 耗时：优先 durationMs，否则用开始/结束时间推导 */
const durationText = computed(() => {
  if (typeof props.durationMs === 'number' && props.durationMs > 0) {
    const d = props.durationMs;
    return d < 1000 ? `${d} ms` : `${(d / 1000).toFixed(1)} s`;
  }
  return formatDuration(props.startedAt, props.finishedAt);
});

/** 参数格式化 */
const argsFormatted = computed(() => formatToolArgs(props.args));
const argsType = computed(() => argsFormatted.value.type);
const argsText = computed(() => argsFormatted.value.value);

/** 错误展示：优先 error 对象，其次是 errorMsg 字符串 */
const errorDisplay = computed(() => {
  if (props.error && typeof props.error === 'object') return formatError(props.error);
  if (props.errorMsg) return props.errorMsg;
  return '';
});

/** 结果归一化 → 字符串 */
const resultText = computed(() => stringifyResult(props.result));

/** 结果是否以 JSON 形式展示（美化后的 JSON） */
const resultIsJson = computed(() => {
  if (!resultText.value) return false;
  // 先尝试解析：如果是合法 JSON，用美化后的版本；否则看字符串形状
  if (looksLikeJson(resultText.value)) {
    try {
      JSON.parse(resultText.value);
      return true;
    } catch {
      return false;
    }
  }
  return false;
});

/** 美化后的 JSON（仅当 resultIsJson = true 时使用） */
const resultPretty = computed(() => {
  if (!resultIsJson.value) return resultText.value;
  try {
    return JSON.stringify(JSON.parse(resultText.value), null, 2);
  } catch {
    return resultText.value;
  }
});

/** 非 JSON 文本 → 用 Markdown 渲染（支持链接、列表、粗体等） */
const renderedResultHtml = computed(() => {
  if (resultIsJson.value || !resultText.value) return '';
  return renderMarkdown(resultText.value);
});

/** 默认展开：有错误或状态成功时展开 */
const defaultOpen = computed(
  () => props.status === 'error' || props.status === 'success'
);

const localOpen = ref(false);

watch(
  defaultOpen,
  v => (localOpen.value = v || localOpen.value),
  { immediate: true }
);

const handleToggle = () => {
  localOpen.value = !localOpen.value;
};
</script>

<style scoped>
.tool-card {
  margin: 8px 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-color);
  background-color: var(--bg-card);
  transition: border-color var(--transition-fast);
}

.tool-card.success {
  border-color: rgba(16, 185, 129, 0.3);
}

.tool-card.error {
  border-color: rgba(239, 68, 68, 0.3);
}

.tool-card.running {
  border-color: rgba(59, 130, 246, 0.35);
}

.tool-card-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 10px 14px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background-color var(--transition-fast);
}

.tool-card-header:hover {
  background-color: var(--bg-card-hover);
}

.tool-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-600);
  background-color: var(--primary-50);
}

[data-theme='dark'] .tool-icon {
  background-color: rgba(59, 130, 246, 0.12);
  color: var(--primary-500);
}

.tool-icon.system {
  color: var(--warning);
  background-color: rgba(245, 158, 11, 0.1);
}

.tool-icon.web {
  color: #8b5cf6;
  background-color: rgba(139, 92, 246, 0.1);
}

.tool-icon.knowledge {
  color: var(--success);
  background-color: rgba(16, 185, 129, 0.1);
}

.tool-icon.memory {
  color: #ec4899;
  background-color: rgba(236, 72, 153, 0.1);
}

.tool-icon.code {
  color: #14b8a6;
  background-color: rgba(20, 184, 166, 0.1);
}

.tool-icon.file {
  color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.1);
}

.tool-icon.other {
  color: #64748b;
  background-color: rgba(100, 116, 139, 0.1);
}

.tool-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tool-name {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
}

.tool-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-status {
  font-size: var(--text-xs);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.tool-status.success {
  color: var(--success);
  background-color: rgba(16, 185, 129, 0.1);
}

.tool-status.error {
  color: var(--danger);
  background-color: rgba(239, 68, 68, 0.1);
}

.tool-status.running {
  color: var(--primary-600);
  background-color: var(--primary-50);
}

[data-theme='dark'] .tool-status.running {
  background-color: rgba(59, 130, 246, 0.12);
  color: var(--primary-500);
}

.tool-status.pending {
  color: var(--text-tertiary);
  background-color: var(--border-color-light);
}

.tool-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-meta-right {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.tool-duration {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.tool-chevron {
  color: var(--text-tertiary);
  transition: transform var(--transition-base);
}

.tool-chevron.rotated {
  transform: rotate(180deg);
}

.tool-card-body {
  padding: 0 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tool-section-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
}

.tool-section-content {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background-color: var(--bg-page);
  border: 1px solid var(--border-color-light);
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-section-content code {
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.tool-section-content.error-text {
  color: var(--danger);
  background-color: rgba(239, 68, 68, 0.06);
  border-color: rgba(239, 68, 68, 0.18);
}

.tool-section-content :deep(p) {
  margin: 0 0 8px;
}

.tool-section-content :deep(p:last-child) {
  margin: 0;
}

.tool-section-content :deep(ul) {
  padding-left: 20px;
  margin: 4px 0;
}

.tool-section-content :deep(li) {
  margin: 2px 0;
}

.tool-section-content :deep(a) {
  color: var(--text-link);
  text-decoration: none;
}

.tool-section-content :deep(a:hover) {
  text-decoration: underline;
}

.tool-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-track {
  flex: 1;
  height: 4px;
  border-radius: var(--radius-full);
  background-color: var(--border-color-light);
  overflow: hidden;
}

.progress-bar {
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), #60a5fa);
  border-radius: var(--radius-full);
  animation: tool-progress 1.4s ease-in-out infinite;
}

@keyframes tool-progress {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(400%);
  }
}

.progress-text {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.tool-expand-enter-active,
.tool-expand-leave-active {
  transition: all 200ms ease;
  overflow: hidden;
}

.tool-expand-enter-from,
.tool-expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  margin-bottom: 0;
  gap: 0;
}

.tool-expand-enter-to,
.tool-expand-leave-from {
  opacity: 1;
  max-height: 2000px;
}
</style>
