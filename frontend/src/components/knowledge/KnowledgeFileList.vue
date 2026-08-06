<template>
  <div class="knowledge-file-list">
    <!-- 工具栏 -->
    <div class="file-toolbar">
      <span class="toolbar-title">文件列表</span>
      <el-button size="small" type="primary" :icon="Plus" @click="handleNewFile">
        新建文件
      </el-button>
    </div>

    <!-- 空状态 -->
    <div v-if="files.length === 0" class="empty-wrapper">
      <EmptyState
        icon="Collection"
        title="知识库为空"
        description="知识库目录中没有 .txt 或 .md 文件，请添加文件后重建索引。"
      />
    </div>

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
        <span class="col-name col-name-clickable" @click="handleEdit(file.name)">
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
          <el-tooltip content="编辑文件" placement="top">
            <el-button
              text
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(file.name)"
            />
          </el-tooltip>
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

    <!-- 文件编辑器弹窗 -->
    <el-dialog
      v-model="editorVisible"
      :title="editorTitle"
      width="720px"
      top="5vh"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <div v-loading="editorLoading" class="editor-content">
        <el-input
          v-model="editorContent"
          type="textarea"
          :rows="20"
          class="editor-textarea"
          placeholder="请输入文件内容..."
        />
      </div>
      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" :loading="editorSaving" @click="handleSaveEditor">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建文件弹窗 -->
    <el-dialog
      v-model="newFileVisible"
      title="新建文件"
      width="480px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <el-form label-width="80px" class="new-file-form">
        <el-form-item label="文件名">
          <el-input
            v-model="newFileName"
            placeholder="例如: my_note.txt"
            @keyup.enter="handleCreateFile"
          />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="newFileContent"
            type="textarea"
            :rows="10"
            placeholder="可选，文件内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newFileVisible = false">取消</el-button>
        <el-button type="primary" :loading="newFileCreating" @click="handleCreateFile">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Document, Delete, Edit, Plus } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import EmptyState from '@/components/common/EmptyState.vue';
import { getFileContent, updateKnowledgeFile, createKnowledgeFile } from '@/api/knowledge';
import type { KnowledgeFile } from '@/api/knowledge';

interface Props {
  files: KnowledgeFile[];
}

const { files } = defineProps<Props>();

const emit = defineEmits<{
  delete: [filename: string];
  change: [];
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

// ====== 文件编辑 ======

const editorVisible = ref(false);
const editorLoading = ref(false);
const editorSaving = ref(false);
const editorContent = ref('');
const editorTitle = ref('');
const editingFile = ref('');

const handleEdit = async (filename: string) => {
  editorVisible.value = true;
  editorLoading.value = true;
  editorContent.value = '';
  editingFile.value = filename;
  editorTitle.value = `编辑 - ${filename}`;
  try {
    const data = await getFileContent(filename);
    editorContent.value = data.content;
  } catch (error) {
    console.error('获取文件内容失败:', error);
    ElMessage.error('获取文件内容失败');
    editorVisible.value = false;
  } finally {
    editorLoading.value = false;
  }
};

const handleSaveEditor = async () => {
  if (!editingFile.value) return;
  editorSaving.value = true;
  try {
    const result = await updateKnowledgeFile(editingFile.value, editorContent.value);
    if (result.success) {
      ElMessage.success(`文件 "${editingFile.value}" 已保存`);
      editorVisible.value = false;
      emit('change');
    } else {
      ElMessage.error(result.message || '保存失败');
    }
  } catch (error) {
    console.error('保存文件失败:', error);
    ElMessage.error('保存文件失败，请稍后重试');
  } finally {
    editorSaving.value = false;
  }
};

// ====== 新建文件 ======

const newFileVisible = ref(false);
const newFileName = ref('');
const newFileContent = ref('');
const newFileCreating = ref(false);

const handleNewFile = () => {
  newFileName.value = '';
  newFileContent.value = '';
  newFileVisible.value = true;
};

const handleCreateFile = async () => {
  const name = newFileName.value.trim();
  if (!name) {
    ElMessage.warning('请输入文件名');
    return;
  }
  const ext = name.includes('.') ? name.split('.').pop()?.toLowerCase() ?? '' : '';
  if (!['txt', 'md'].includes(ext)) {
    ElMessage.warning('仅支持 .txt 或 .md 格式的文件');
    return;
  }
  newFileCreating.value = true;
  try {
    const result = await createKnowledgeFile(name, newFileContent.value);
    if (result.success) {
      ElMessage.success(`文件 "${name}" 已创建`);
      newFileVisible.value = false;
      emit('change');
    } else {
      ElMessage.error(result.message || '创建失败');
    }
  } catch (error) {
    console.error('创建文件失败:', error);
    ElMessage.error('创建文件失败，请稍后重试');
  } finally {
    newFileCreating.value = false;
  }
};
</script>

<style scoped>
.knowledge-file-list {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 工具栏 */
.file-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.toolbar-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.file-table {
  width: 100%;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.file-table-header {
  display: grid;
  /* 名称(弹性) | 大小 | 时间 | 状态 | 操作 —— 总和不再超出容器 */
  grid-template-columns: minmax(0, 1fr) 70px minmax(0, 130px) 90px 80px;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-tertiary);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-body);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 1;
}

/* 空状态居中 */
.empty-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-table-row {
  display: grid;
  /* 与 header 同列宽，保持对齐 */
  grid-template-columns: minmax(0, 1fr) 70px minmax(0, 130px) 90px 80px;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.file-table-row:last-child {
  border-bottom: none;
}

.file-table-row:hover {
  background: var(--primary-50);
}

[data-theme='dark'] .file-table-row:hover {
  background: rgba(59, 130, 246, 0.08);
}

.col-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;             /* grid 单元格允许收缩 */
  overflow: hidden;
}

.col-name-clickable {
  cursor: pointer;
  color: var(--text-primary);
  transition: color var(--transition-fast);
}

.col-name-clickable:hover {
  color: var(--primary-600);
}

.col-name .el-icon {
  color: var(--primary-500);
  flex-shrink: 0;
  font-size: 16px;
}

.col-size {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.col-time {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-status {
  min-width: 0;
  overflow: hidden;
}

.col-action {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
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

/* 编辑器弹窗 */
.editor-content {
  min-height: 300px;
}

.editor-textarea {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.editor-textarea :deep(textarea) {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

/* 新建文件表单 */
.new-file-form {
  padding: var(--space-2) 0;
}
</style>