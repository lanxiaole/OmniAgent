<template>
  <div class="file-preview">
    <!-- 未选中文件 -->
    <div v-if="!filePath" class="empty-state">
      <el-icon :size="48" color="var(--text-tertiary)">
        <Document />
      </el-icon>
      <p>从左侧选择一个文件查看</p>
    </div>

    <!-- 已选中文件 -->
    <template v-else>
      <div class="preview-header">
        <span class="preview-filename">{{ fileName }}</span>
        <span class="preview-size">{{ formatFileSize(fileSize) }}</span>
      </div>

      <div class="preview-body">
        <!-- Markdown 渲染 -->
        <MarkdownRenderer v-if="isMarkdown" :content="content" />
        <!-- 图片 -->
        <img v-else-if="isImage" :src="imageUrl" :alt="fileName" class="preview-image" />
        <!-- 纯文本 -->
        <pre v-else class="preview-text"><code>{{ content }}</code></pre>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Document } from '@element-plus/icons-vue';
import MarkdownRenderer from '@/components/chat/MarkdownRenderer.vue';

interface Props {
  filePath: string;
  content: string;
  fileSize: number;
}

const props = defineProps<Props>();

/** 文件名（从路径提取） */
const fileName = computed(() => {
  const parts = props.filePath.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1] || props.filePath;
});

/** 是否为 Markdown 文件 */
const isMarkdown = computed(() => {
  return /\.(md|markdown)$/i.test(fileName.value);
});

/** 是否为图片文件 */
const isImage = computed(() => {
  return /\.(png|jpg|jpeg|gif|svg|webp|bmp)$/i.test(fileName.value);
});

/** 图片预览 URL */
const imageUrl = computed(() => {
  return `/api/workspace/file?path=${encodeURIComponent(props.filePath)}&raw=1`;
});

/** 格式化文件大小 */
const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};
</script>

<style scoped>
.file-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-4);
  color: var(--text-tertiary);
  font-size: var(--text-md);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-card);
  flex-shrink: 0;
}

.preview-filename {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-size {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
  margin-left: var(--space-3);
}

.preview-body {
  flex: 1;
  overflow: auto;
  padding: var(--space-4);
}

.preview-text {
  margin: 0;
  padding: var(--space-4);
  background-color: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  overflow: auto;
  white-space: pre;
  color: var(--text-primary);
}

.preview-text code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: var(--radius-md);
}
</style>