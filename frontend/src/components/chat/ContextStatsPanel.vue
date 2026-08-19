<template>
  <div class="context-stats-panel">
    <el-popover
      placement="bottom-end"
      :width="400"
      trigger="click"
      :popper-style="{ padding: '0', border: 'none' }"
      @show="loadStats"
    >
      <template #reference>
        <button
          class="stats-trigger-btn"
          :class="triggerBtnClass"
          :title="buttonTitle"
        >
          <svg class="trigger-icon" :class="triggerBtnClass" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
          <span class="trigger-text">{{ displayText }}</span>
        </button>
      </template>

      <!-- 面板内容 -->
      <div class="stats-panel" v-loading="loading" element-loading-text="计算中...">
        <!-- 顶部：标题栏 -->
        <div class="panel-header">
          <div class="header-left">
            <svg class="header-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4"/>
              <path d="M12 8h.01"/>
            </svg>
            <span class="header-title">上下文概况</span>
          </div>
          <div class="header-badge" :class="badgeClass">
            <span class="badge-dot"/>
            <span>{{ usageLevelText }}</span>
          </div>
        </div>

        <!-- 基本信息网格 -->
        <div class="info-grid">
          <div class="info-card">
            <div class="info-card-icon msg-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="info-card-body">
              <span class="info-card-label">消息数</span>
              <span class="info-card-value">{{ stats?.message_count ?? 0 }}</span>
            </div>
          </div>
          <div class="info-card">
            <div class="info-card-icon token-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
            </div>
            <div class="info-card-body">
              <span class="info-card-label">总 Token</span>
              <span class="info-card-value">{{ formatNumber(stats?.total_tokens ?? 0) }}</span>
            </div>
          </div>
          </div>

        <!-- Token 使用进度 -->
        <div class="section">
          <div class="section-header">
            <span class="section-label">上下文窗口使用率</span>
            <span class="section-value" :class="badgeClass">{{ stats?.usage_percentage ?? 0 }}%</span>
          </div>
          <div class="progress-track">
            <div
              class="progress-fill"
              :class="progressClass"
              :style="{ width: Math.min(progressValue, 100) + '%' }"
            />
          </div>
          <div class="progress-footer">
            <span class="progress-used">{{ formatNumber(stats?.total_tokens ?? 0) }} tokens</span>
            <span class="progress-max">/ {{ formatNumber(stats?.max_context_window ?? 8192) }}</span>
          </div>
        </div>

        <!-- Token 分布明细 -->
        <div class="section">
          <div class="section-header">
            <span class="section-label">分布明细</span>
          </div>
          <div class="breakdown-bars">
            <div
              v-for="item in breakdownItems"
              :key="item.key"
              class="breakdown-row"
            >
              <div class="breakdown-row-header">
                <div class="breakdown-label-group">
                  <span class="breakdown-dot" :style="{ background: item.color }"/>
                  <span class="breakdown-label">{{ item.label }}</span>
                </div>
                <span class="breakdown-value">
                  {{ formatNumber(item.tokens) }}
                  <span class="breakdown-percent">({{ item.percentage }}%)</span>
                </span>
              </div>
              <div class="breakdown-track">
                <div
                  class="breakdown-fill"
                  :style="{
                    width: item.percentage + '%',
                    background: `linear-gradient(90deg, ${item.color}, ${item.color}dd)`
                  }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { getContextStats } from '@/api/context';
import type { ContextStats } from '@/api/context';

const props = defineProps<{
  threadId: string;
}>();

const loading = ref(false);
const stats = ref<ContextStats | null>(null);

const loadStats = async () => {
  if (!props.threadId) return;
  loading.value = true;
  try {
    stats.value = await getContextStats(props.threadId);
  } catch (error) {
    console.error('加载上下文统计失败:', error);
    stats.value = null;
  } finally {
    loading.value = false;
  }
};

watch(() => props.threadId, () => {
  stats.value = null;
});

// ---- 计算属性 ----

const displayText = computed(() => {
  if (!stats.value) return '--';
  return `${stats.value.usage_percentage}%`;
});

const buttonTitle = computed(() => {
  if (!stats.value) return '上下文信息';
  return `Token 使用率: ${stats.value.usage_percentage}% (${stats.value.total_tokens}/${stats.value.max_context_window})`;
});

const usageLevelText = computed(() => {
  if (!stats.value) return '正常';
  const pct = stats.value.usage_percentage;
  if (pct >= 80) return '偏高';
  if (pct >= 60) return '中等';
  return '正常';
});

const triggerBtnClass = computed(() => {
  if (!stats.value) return 'level-normal';
  const pct = stats.value.usage_percentage;
  if (pct >= 80) return 'level-danger';
  if (pct >= 60) return 'level-warning';
  return 'level-normal';
});

const badgeClass = computed(() => {
  if (!stats.value) return 'badge-normal';
  const pct = stats.value.usage_percentage;
  if (pct >= 80) return 'badge-danger';
  if (pct >= 60) return 'badge-warning';
  return 'badge-normal';
});

const progressClass = computed(() => {
  if (!stats.value) return 'progress-normal';
  const pct = stats.value.usage_percentage;
  if (pct >= 80) return 'progress-danger';
  if (pct >= 60) return 'progress-warning';
  return 'progress-normal';
});

const progressValue = computed(() => {
  if (!stats.value) return 0;
  return Math.min(stats.value.usage_percentage, 100);
});

interface BreakdownItem {
  key: string;
  label: string;
  tokens: number;
  percentage: number;
  color: string;
}

const breakdownItems = computed(() => {
  if (!stats.value) return [];
  const bd = stats.value.breakdown;
  const total = bd.history_messages || 1;
  const items: BreakdownItem[] = [
    { key: 'user_messages', label: '用户消息', tokens: bd.user_messages, percentage: 0, color: '#3b82f6' },
    { key: 'ai_replies', label: 'AI 回复', tokens: bd.ai_replies, percentage: 0, color: '#22c55e' },
    { key: 'tool_calls', label: '工具调用', tokens: bd.tool_calls, percentage: 0, color: '#f59e0b' },
    { key: 'tool_results', label: '工具结果', tokens: bd.tool_results, percentage: 0, color: '#8b5cf6' },
    { key: 'summary', label: '上下文总结', tokens: bd.summary, percentage: 0, color: '#06b6d4' },
    { key: 'manual_context', label: '手动上下文', tokens: bd.manual_context, percentage: 0, color: '#10b981' },
  ];
  const filtered = items.filter(item => item.tokens > 0);
  const display = filtered.length > 0 ? filtered : items;
  return display.map(item => ({
    ...item,
    percentage: Math.round((item.tokens / total) * 100),
  }));
});

const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
};
</script>

<style scoped>
.context-stats-panel {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

/* ====== 入口按钮 ====== */
.stats-trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px 4px 8px;
  border: 1px solid;
  border-radius: 20px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  font-family: inherit;
}

.stats-trigger-btn.level-normal {
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.25);
}
.stats-trigger-btn.level-normal:hover {
  background: rgba(34, 197, 94, 0.08);
  border-color: rgba(34, 197, 94, 0.5);
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.12);
}

.stats-trigger-btn.level-warning {
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.25);
}
.stats-trigger-btn.level-warning:hover {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.12);
}

.stats-trigger-btn.level-danger {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.25);
}
.stats-trigger-btn.level-danger:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.12);
}

.trigger-icon {
  flex-shrink: 0;
  transition: transform 0.2s ease;
}
.stats-trigger-btn:hover .trigger-icon {
  transform: rotate(8deg);
}

.trigger-text {
  font-weight: 600;
  min-width: 28px;
  text-align: center;
  letter-spacing: 0.3px;
}

/* ====== 面板容器 ====== */
.stats-panel {
  padding: 0;
  max-height: 540px;
  overflow-y: auto;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border-radius: 14px;
}

/* ====== 标题栏 ====== */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #eef2f6;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: #6366f1;
  flex-shrink: 0;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.2px;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.badge-normal {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.badge-normal .badge-dot { background: #22c55e; }

.badge-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}
.badge-warning .badge-dot { background: #f59e0b; }

.badge-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}
.badge-danger .badge-dot { background: #ef4444; }

/* ====== 基本信息网格 ====== */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 14px 20px;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px;
  background: #ffffff;
  border: 1px solid #eef2f6;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.info-card:hover {
  border-color: #dde3ea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.info-card-icon {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
}

.msg-icon {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.token-icon {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.info-card-body {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.info-card-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  line-height: 1.2;
}

.info-card-value {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  line-height: 1.3;
}

/* ====== 区块通用 ====== */
.section {
  padding: 10px 20px;
}

.section + .section {
  border-top: 1px solid #eef2f6;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-value {
  font-size: 12px;
  font-weight: 700;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* ====== Token 进度条 ====== */
.progress-track {
  width: 100%;
  height: 8px;
  background: #eef2f6;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25));
  border-radius: 4px;
}

.progress-normal {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.progress-warning {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.progress-danger {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.progress-footer {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  margin-top: 6px;
  font-size: 12px;
}

.progress-used {
  font-weight: 600;
  color: #1e293b;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

.progress-max {
  color: #94a3b8;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* ====== 分布明细 ====== */
.breakdown-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.breakdown-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breakdown-row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breakdown-label-group {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.breakdown-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.breakdown-label {
  font-size: 12px;
  font-weight: 500;
  color: #334155;
}

.breakdown-value {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

.breakdown-percent {
  font-weight: 400;
  color: #94a3b8;
  font-size: 11px;
}

.breakdown-track {
  width: 100%;
  height: 5px;
  background: #eef2f6;
  border-radius: 3px;
  overflow: hidden;
}

.breakdown-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ====== 滚动条 ====== */
.stats-panel::-webkit-scrollbar {
  width: 4px;
}

.stats-panel::-webkit-scrollbar-track {
  background: transparent;
}

.stats-panel::-webkit-scrollbar-thumb {
  background: #dde3ea;
  border-radius: 2px;
}

.stats-panel::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>