<template>
  <div class="uploader-wrapper">
    <el-upload
      drag
      action="/api/knowledge/upload"
      :before-upload="beforeUpload"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :on-progress="handleProgress"
      :show-file-list="false"
      class="upload-area"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处，或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          仅支持 .txt / .md 文件，单个文件不超过 10MB
        </div>
      </template>
    </el-upload>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="uploadPercent" :stroke-width="8" status="success" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

const emit = defineEmits<{
  success: [];
}>();

const uploading = ref(false);
const uploadPercent = ref(0);

/** 上传前校验 */
const beforeUpload = (file: File): boolean => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!ext || !['txt', 'md'].includes(ext)) {
    ElMessage.error('不支持的文件格式，仅支持 .txt / .md');
    return false;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小超过 10MB 限制');
    return false;
  }
  uploading.value = true;
  uploadPercent.value = 0;
  return true;
};

/** 上传进度回调 */
const handleProgress = (event: any): void => {
  if (event.percent !== undefined) {
    uploadPercent.value = Math.round(event.percent);
  }
};

/** 上传成功回调 */
const handleUploadSuccess = (response: any): void => {
  uploading.value = false;
  if (response.success) {
    ElMessage.success(`文件 "${response.filename}" 上传成功`);
    emit('success');
  } else {
    ElMessage.warning(response.message || '上传完成但状态未知');
    emit('success');
  }
};

/** 上传失败回调 */
const handleUploadError = (): void => {
  uploading.value = false;
  uploadPercent.value = 0;
  ElMessage.error('上传失败，请稍后重试');
};
</script>

<style scoped>
.uploader-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* 统一定制上传区域样式 */
.upload-area {
  width: 100%;
  :deep(.el-upload-dragger) {
    width: 100%;
    padding: 28px 20px;
    background: var(--bg-card);
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-lg);
    transition: all var(--transition-fast);
  }

  :deep(.el-upload-dragger:hover) {
    border-color: var(--primary-500);
    background: var(--primary-50);
  }

  :deep(.el-upload-dragger.is-dragover) {
    border-color: var(--primary-500);
    background: var(--primary-50);
  }

  :deep(.el-icon--upload) {
    color: var(--primary-500);
    margin-bottom: 8px;
  }

  :deep(.el-upload__text) {
    color: var(--text-secondary);
    font-size: var(--text-md);
    em {
      color: var(--primary-600);
      font-style: normal;
      font-weight: 500;
    }
  }

  :deep(.el-upload__tip) {
    margin-top: 8px;
    color: var(--text-tertiary);
    font-size: var(--text-sm);
    line-height: 1.5;
  }
}

.upload-progress {
  padding: 0 var(--space-1);
}
</style>