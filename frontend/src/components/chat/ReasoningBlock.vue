<template>
  <div class="reasoning-block" :class="{ open: localOpen }">
    <button class="reasoning-toggle" @click="localOpen = !localOpen">
      <div class="reasoning-toggle-left">
        <div class="thinking-dot"></div>
        <span class="reasoning-label">思考过程</span>
        <span v-if="metaText" class="reasoning-meta">{{ metaText }}</span>
      </div>
      <el-icon class="reasoning-chevron" :class="{ rotated: localOpen }" size="16">
        <ArrowDown />
      </el-icon>
    </button>
    <transition name="reasoning-expand">
      <div v-show="localOpen" class="reasoning-content">
        <div class="reasoning-inner">
          <div
            v-for="(step, idx) in displaySteps"
            :key="step.id || idx"
            class="reasoning-step"
          >
            <div class="step-header">
              <span class="step-index">第 {{ idx + 1 }} 步</span>
              <span v-if="step.thinkingMs" class="step-time">{{ formatThinkingMs(step.thinkingMs) }}</span>
            </div>
            <pre class="reasoning-text">{{ step.text || '（未记录内容）' }}</pre>
          </div>
          <div v-if="displaySteps.length === 0" class="reasoning-empty">
            本次回复未记录中间思考过程。
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ArrowDown } from '@element-plus/icons-vue';
import type { ReasoningStep } from '@/types/chat';

interface Props {
  /** 单个文本（兼容旧版本）或思考步骤数组 */
  steps?: ReasoningStep[] | string;
  /** 外部强制控制是否展开 */
  defaultOpen?: boolean;
  /** 单个思考步骤时：开始时间戳 */
  startedAt?: number;
  /** 单个思考步骤时：结束时间戳 */
  finishedAt?: number;
}

const props = withDefaults(defineProps<Props>(), {
  defaultOpen: false,
  steps: () => [],
});

const localOpen = ref(props.defaultOpen);

watch(
  () => props.defaultOpen,
  v => (localOpen.value = v)
);

/** 统一转换为 ReasoningStep[] 处理 */
const displaySteps = computed<ReasoningStep[]>(() => {
  const { steps } = props;
  if (!steps) return [];
  if (typeof steps === 'string') {
    return [
      {
        id: 'single',
        text: steps,
        thinkingMs:
          typeof props.startedAt === 'number' && typeof props.finishedAt === 'number'
            ? props.finishedAt - props.startedAt
            : undefined,
      },
    ];
  }
  if (Array.isArray(steps)) return steps;
  return [];
});

const stepsCount = computed(() => displaySteps.value.length);

const totalDurationMs = computed(() =>
  displaySteps.value.reduce<number>((acc, s) => acc + (s.thinkingMs ?? 0), 0)
);

/** 总耗时文本：尽量简短 */
const totalDurationText = computed(() => {
  const total = totalDurationMs.value;
  if (!total) return '';
  return formatThinkingMs(total);
});

/** 头部元信息：多步或有时耗时才显示，避免出现"1 步"或"总耗时"但没数值的空字段 */
const metaText = computed(() => {
  const parts: string[] = [];
  if (stepsCount.value > 1) {
    parts.push(`${stepsCount.value} 步`);
  }
  if (totalDurationText.value) {
    parts.push(`总耗时 ${totalDurationText.value}`);
  }
  return parts.join(' · ');
});

/** 毫秒 → 人类可读（<1s 显示 ms，>=1s 显示 s） */
const formatThinkingMs = (ms: number) => {
  if (!ms) return '';
  if (ms < 1000) return `${ms} ms`;
  const s = ms / 1000;
  return s >= 60 ? `${(s / 60).toFixed(1)} 分钟` : `${s.toFixed(1)} 秒`;
};
</script>

<style scoped>
.reasoning-block {
  width: 100%;
  margin: 4px 0 10px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  background: var(--bg-soft);
  overflow: hidden;
}

.reasoning-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-family: var(--font-sans);
  transition: background-color var(--transition-fast);
}

.reasoning-toggle:hover {
  background-color: var(--bg-sidebar-hover);
}

.reasoning-toggle-left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.thinking-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12);
}

.reasoning-label {
  font-weight: 600;
  color: var(--text-primary);
}

.reasoning-meta {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.reasoning-chevron {
  color: var(--text-tertiary);
  transition: transform 200ms ease;
}
.reasoning-chevron.rotated {
  transform: rotate(180deg);
}

.reasoning-content {
  overflow: hidden;
}

.reasoning-inner {
  padding: 4px 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reasoning-step {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  padding: 10px 12px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.step-index {
  font-weight: 600;
  color: #8b5cf6;
}

.reasoning-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  line-height: 1.7;
  color: var(--text-secondary);
  background: transparent;
  padding: 0;
}

.reasoning-empty {
  padding: 12px;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  text-align: center;
  font-style: italic;
}

/* 展开动画：高度 + 透明度 */
.reasoning-expand-enter-active,
.reasoning-expand-leave-active {
  transition: max-height 300ms ease, opacity 220ms ease;
  max-height: 3000px;
  opacity: 1;
}
.reasoning-expand-enter-from,
.reasoning-expand-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
