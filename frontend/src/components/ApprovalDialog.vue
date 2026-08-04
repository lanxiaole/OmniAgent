<template>
  <Transition name="approval-fade">
    <div v-if="visible" class="approval-overlay" @click.self="handleOverlayClick">
      <div class="approval-dialog">
        <div class="approval-header">
          <div class="approval-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
              <path d="M12 8V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <span class="approval-title">需要审批</span>
        </div>

        <div class="approval-body">
          <div class="approval-reason">
            <span class="label">原因：</span>
            <span class="value">{{ approval.reason }}</span>
          </div>

          <div class="approval-tool">
            <span class="label">工具：</span>
            <span class="value tool-name">{{ getToolDisplayName(approval.tool) }}</span>
          </div>

          <div class="approval-args">
            <span class="label">参数：</span>
            <pre class="args-json">{{ formatArgs(approval.args) }}</pre>
          </div>
        </div>

        <div class="approval-footer">
          <button
            class="btn btn-reject"
            @click="handleReject"
            :disabled="processing"
          >
            <span v-if="!processing">拒绝</span>
            <span v-else>处理中...</span>
          </button>
          <button
            class="btn btn-approve"
            @click="handleApprove"
            :disabled="processing"
          >
            <span v-if="!processing">批准</span>
            <span v-else>处理中...</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { sendApproval } from '@/api/chat';
import type { ApprovalRequest } from '@/api/chat';

const props = defineProps<{
  visible: boolean;
  approval: ApprovalRequest;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'result', requestId: string, approved: boolean): void;
}>();

const processing = ref(false);

const getToolDisplayName = (tool: string): string => {
  const map: Record<string, string> = {
    write_file: '写入文件',
    execute_python: '执行代码',
    delete_file: '删除文件',
  };
  return map[tool] || tool;
};

const formatArgs = (args: Record<string, unknown>): string => {
  try {
    return JSON.stringify(args, null, 2);
  } catch {
    return String(args);
  }
};

const handleApprove = async () => {
  processing.value = true;
  const result = await sendApproval(props.approval.request_id, true);
  processing.value = false;
  if (result.success) {
    emit('result', props.approval.request_id, true);
  }
};

const handleReject = async () => {
  processing.value = true;
  const result = await sendApproval(props.approval.request_id, false);
  processing.value = false;
  if (result.success) {
    emit('result', props.approval.request_id, false);
  }
};

const handleOverlayClick = () => {
  // 不允许点击遮罩关闭，用户必须做出选择
};
</script>

<style scoped>
.approval-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
  padding: 20px;
  pointer-events: auto;
}

.approval-dialog {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 520px;
  overflow: hidden;
  animation: slide-up 0.25s ease-out;
}

@keyframes slide-up {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.approval-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.approval-icon {
  width: 24px;
  height: 24px;
  color: #e6a23c;
  flex-shrink: 0;
}

.approval-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.approval-body {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-reason,
.approval-tool,
.approval-args {
  display: flex;
  gap: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.label {
  color: #666;
  flex-shrink: 0;
  min-width: 48px;
  font-weight: 500;
}

.value {
  color: #1a1a1a;
  word-break: break-word;
}

.tool-name {
  color: #409eff;
  font-weight: 500;
}

.args-json {
  margin: 0;
  background: #f6f8fa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #333;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
  max-height: 200px;
  overflow-y: auto;
}

.approval-footer {
  display: flex;
  gap: 12px;
  padding: 12px 20px 16px;
  justify-content: flex-end;
}

.btn {
  padding: 8px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-reject {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #e0e0e0;
}

.btn-reject:hover:not(:disabled) {
  background: #fef0f0;
  color: #f56c6c;
  border-color: #f56c6c;
}

.btn-approve {
  background: #409eff;
  color: #fff;
}

.btn-approve:hover:not(:disabled) {
  background: #66b1ff;
}

/* 过渡动画 */
.approval-fade-enter-active,
.approval-fade-leave-active {
  transition: opacity 0.2s ease;
}

.approval-fade-enter-from,
.approval-fade-leave-to {
  opacity: 0;
}
</style>