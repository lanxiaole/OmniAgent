<template>
  <div class="memory-card">
    <!-- 记忆内容 -->
    <div class="memory-content" :class="{ expanded: expanded }">
      <p class="memory-text">{{ memory.content }}</p>
    </div>
    <button
      v-if="showExpand"
      class="expand-btn"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起' : '展开全部' }}
      <el-icon :size="12" :class="{ rotated: expanded }"><ArrowDown /></el-icon>
    </button>

    <!-- 底部信息栏 -->
    <div class="memory-footer">
      <div class="memory-time">
        <el-icon :size="14"><Clock /></el-icon>
        <span>{{ formattedTime }}</span>
      </div>
      <div class="memory-actions">
        <el-tooltip content="编辑" placement="top">
          <el-button text size="small" :icon="EditPen" @click="$emit('edit', memory.id)" />
        </el-tooltip>
        <el-tooltip content="删除" placement="top">
          <el-button text type="danger" size="small" :icon="Delete" @click="handleDelete" />
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Clock, EditPen, Delete, ArrowDown } from '@element-plus/icons-vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import type { MemoryItem } from '@/api/memory';
import { deleteMemory } from '@/api/memory';

interface Props {
  memory: MemoryItem;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  edit: [id: string];
  deleted: [];
}>();

const expanded = ref(false);
const showExpand = ref(false);

const formattedTime = computed(() => {
  if (!props.memory.metadata?.created_at) return '未知时间';
  try {
    const d = new Date(props.memory.metadata.created_at);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const minute = String(d.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
  } catch {
    return props.memory.metadata.created_at;
  }
});

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条记忆吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    const result = await deleteMemory(props.memory.id);
    if (result.success) {
      ElMessage.success('记忆已删除');
      emit('deleted');
    } else {
      ElMessage.error(result.message || '删除失败');
    }
  } catch {
    // 用户取消操作
  }
};

// 在挂载后检查内容是否需要展开按钮
onMounted(() => {
  // 简单判断：文本行数或字符数较多时显示展开
  if (props.memory.content.length > 120) {
    showExpand.value = true;
  }
});
</script>

<style scoped>
.memory-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.memory-card:hover {
  border-color: var(--border-color-hover);
  box-shadow: var(--shadow-sm);
}

.memory-content {
  padding: var(--space-4) var(--space-5);
  max-height: 80px;
  overflow: hidden;
  transition: max-height var(--transition-normal);
}

.memory-content.expanded {
  max-height: 600px;
  overflow-y: auto;
}

.memory-text {
  margin: 0;
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.expand-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px var(--space-5) 8px;
  font-size: var(--text-sm);
  color: var(--text-link);
  cursor: pointer;
  border: none;
  background: none;
  transition: color var(--transition-fast);
}

.expand-btn:hover {
  color: var(--primary-700);
}

.expand-btn .el-icon {
  transition: transform var(--transition-fast);
}

.expand-btn .el-icon.rotated {
  transform: rotate(180deg);
}

.memory-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-5);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-body);
}

.memory-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.memory-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
</style>