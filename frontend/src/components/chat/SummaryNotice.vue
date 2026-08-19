<template>
  <div class="summary-notice-wrapper">
    <div class="summary-notice-card">
      <div class="notice-header">
        <div class="notice-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div class="notice-title">对话已压缩</div>
      </div>

      <div class="notice-body">
        <span class="notice-description">
          已将前 <strong>{{ data?.summarized_count ?? 0 }}</strong> 条消息压缩为上下文摘要，
          保留最近 <strong>{{ data?.preserved_count ?? 0 }}</strong> 条消息
        </span>
        <span class="notice-time" v-if="data?.triggered_at">
          {{ formatTime(data.triggered_at) }}
        </span>
      </div>

      <div class="notice-actions">
        <button class="notice-btn primary" @click="showDetail = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
          查看摘要
        </button>
      </div>
    </div>

    <!-- 查看摘要弹窗 -->
    <Teleport to="body">
      <div v-if="showDetail" class="summary-overlay" @click.self="showDetail = false">
        <div class="summary-modal">
          <div class="modal-header">
            <div class="modal-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              上下文摘要详情
            </div>
            <button class="modal-close" @click="showDetail = false">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="summary-meta">
              <span class="meta-item">
                <strong>压缩前：</strong>{{ data?.summarized_count ?? 0 }} 条消息
              </span>
              <span class="meta-sep">|</span>
              <span class="meta-item">
                <strong>保留：</strong>{{ data?.preserved_count ?? 0 }} 条消息
              </span>
              <span class="meta-sep">|</span>
              <span class="meta-item">
                <strong>时间：</strong>{{ data?.triggered_at ? formatTime(data.triggered_at) : '-' }}
              </span>
            </div>
            <div class="summary-content" v-if="data?.content">
              <MarkdownRenderer :content="data.content" />
            </div>
            <div class="summary-empty" v-else>
              暂无摘要内容
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { SummaryNoticeData } from '@/types/chat';
import MarkdownRenderer from '@/components/chat/MarkdownRenderer.vue';

defineProps<{
  data?: SummaryNoticeData;
}>();

const showDetail = ref(false);

const formatTime = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  } catch {
    return isoString;
  }
};
</script>

<style scoped>
.summary-notice-wrapper {
  width: 100%;
  max-width: 960px;
  margin: 16px auto;
  padding: 0 24px;
}

.summary-notice-card {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border: 1px solid #dce3f5;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
}

.notice-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #e8edfb;
  border-radius: 6px;
  color: #4a6cf7;
  flex-shrink: 0;
}

.notice-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.notice-body {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-left: 36px;
}

.notice-description {
  font-size: 13px;
  color: #5a6a7a;
  line-height: 1.5;
}

.notice-description strong {
  color: #4a6cf7;
  font-weight: 600;
}

.notice-time {
  font-size: 12px;
  color: #95a5b5;
  margin-left: auto;
  white-space: nowrap;
}

.notice-actions {
  display: flex;
  gap: 8px;
  padding-left: 36px;
}

.notice-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.notice-btn.primary {
  background: #4a6cf7;
  color: #fff;
}

.notice-btn.primary:hover {
  background: #3b5de7;
  box-shadow: 0 2px 8px rgba(74, 108, 247, 0.3);
}

/* 弹窗样式 */
.summary-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.summary-modal {
  background: #fff;
  border-radius: 14px;
  width: 90%;
  max-width: 680px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid #eef2f7;
  flex-shrink: 0;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  color: #7a8a9a;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e8ecf2;
  color: #2c3e50;
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.summary-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f8f9fc;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #5a6a7a;
  flex-wrap: wrap;
}

.meta-item strong {
  color: #2c3e50;
  font-weight: 600;
}

.meta-sep {
  color: #dce0e6;
}

.summary-content {
  font-size: 14px;
  line-height: 1.7;
  color: #2c3e50;
}

.summary-content :deep(h1),
.summary-content :deep(h2),
.summary-content :deep(h3),
.summary-content :deep(h4) {
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  color: #1a2a3a;
}

.summary-content :deep(h2) {
  font-size: 16px;
  border-bottom: 1px solid #eef2f7;
  padding-bottom: 6px;
}

.summary-content :deep(p) {
  margin: 0.5em 0;
}

.summary-content :deep(ul),
.summary-content :deep(ol) {
  padding-left: 20px;
  margin: 0.4em 0;
}

.summary-content :deep(li) {
  margin: 0.2em 0;
}

.summary-content :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #e74c3c;
}

.summary-empty {
  text-align: center;
  color: #95a5b5;
  padding: 40px 0;
  font-size: 14px;
}
</style>