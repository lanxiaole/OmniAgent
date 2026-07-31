<template>
  <div class="knowledge-file-list">
    <!-- 空状态 -->
    <EmptyState
      v-if="files.length === 0"
      icon="Collection"
      title="知识库为空"
      description="知识库目录中没有 .txt 或 .md 文件，请添加文件后重建索引。"
    />

    <!-- 文件列表 -->
    <div v-else class="file-table">
      <div class="file-table-header">
        <span class="col-name">文件名</span>
        <span class="col-size">大小</span>
        <span class="col-time">修改时间</span>
        <span class="col-status">状态</span>
        <span class="col-action">操作</span>
      </div>
      <div
        v-for="file in files"
        :key="file.name"
        class="file-table-row"
      >
        <span class="col-name col-name-clickable" @click="handlePreview(file.name)">
          <el-icon :size="16"><Document /></el-icon>
          <span class="truncate">{{ file.name }}</span>
        </span>
        <span class="col-size">{{ formatSize(file.size) }}</span>
        <span class="col-time">{{ formatTime(file.modified_at) }}</span>
        <span class="col-status">
          <el-tag v-if="file.is_indexed" size="small" type="success" effect="plain">
            <span class="dot dot-success"></span>
            已索引
          </el-tag>
          <el-tag v-else size="small" type="info" effect="plain">
            <span class="dot dot-muted"></span>
            待索引
          </el-tag>
        </span>
        <span class="col-action">
          <el-tooltip content="删除文件" placement="top">
            <el-button
              text
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(file.name)"
            />
          </el-tooltip>
        </span>
      </div>
    </div>

    <!-- 文件预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="680px"
      top="5vh"
      destroy-on-close
    >
      <div v-loading="previewLoading" class="preview-content">
        <pre v-if="previewContent" class="preview-text">{{ previewContent }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Document, Delete } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import EmptyState from '@/components/common/EmptyState.vue';
import { getFileContent } from '@/api/knowledge';
import type { KnowledgeFile } from '@/api/knowledge';

interface Props {
  files: KnowledgeFile[];
}

const { files } = defineProps<Props>();

const emit = defineEmits<{
  delete: [filename: string];
}>();

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatTime = (iso: string): string => {
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
};

const handleDelete = async (filename: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${filename}" 吗？删除后向量库将自动重建。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    emit('delete', filename);
  } catch {
    // 用户取消操作，不做处理
  }
};

// ====== 文件预览 ======

const previewVisible = ref(false);
const previewLoading = ref(false);
const previewContent = ref('');
const previewTitle = ref('');

const handlePreview = async (filename: string) => {
  previewVisible.value = true;
  previewLoading.value = true;
  previewContent.value = '';
  previewTitle.value = `预览 - ${filename}`;
  try {
    const data = await getFileContent(filename);
    previewContent.value = data.content;
  } catch (error) {
    console.error('获取文件内容失败:', error);
    ElMessage.error('获取文件内容失败');
    previewVisible.value = false;
  } finally {
    previewLoading.value = false;
  }
};
</script>

<style scoped>
.knowledge-file-list {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.file-table {
  width: 100%;
}

.file-table-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-body);
}

.file-table-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  font-size: var(--text-base);
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.file-table-row:last-child {
  border-bottom: none;
}

.file-table-row:hover {
  background: var(--bg-card-hover);
}

.col-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
}

.col-name-clickable {
  cursor: pointer;
  color: var(--text-link);
  transition: color var(--transition-fast);
}

.col-name-clickable:hover {
  color: var(--primary-700);
  text-decoration: underline;
}

.col-name .el-icon {
  color: var(--primary-500);
  flex-shrink: 0;
}

.col-size {
  width: 80px;
  flex-shrink: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.col-time {
  width: 160px;
  flex-shrink: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.col-status {
  width: 90px;
  flex-shrink: 0;
}

.col-action {
  width: 48px;
  flex-shrink: 0;
  text-align: center;
}

.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  margin-right: 4px;
  vertical-align: middle;
}

.dot-success {
  background: var(--success);
}

.dot-muted {
  background: var(--text-tertiary);
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 预览弹窗 */
.preview-content {
  min-height: 200px;
  max-height: 65vh;
  overflow: auto;
}

.preview-text {
  margin: 0;
  padding: var(--space-4);
  background: var(--bg-body);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
}
</style>