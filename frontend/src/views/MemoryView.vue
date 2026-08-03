<template>
  <div class="view-container">
    <div class="memory-content">
      <!-- 左栏：统计 + 记忆列表 -->
      <div class="content-left">
        <!-- 统计卡片 -->
        <MemoryStats
          :count="displayMemories.length"
          @add="handleFocusAdd"
          @clear="handleClearAll"
        />

        <!-- 搜索结果提示（独立于加载/列表的显示逻辑） -->
        <div v-if="isSearching" class="search-hint">
          搜索 "{{ searchQuery }}" 共找到 {{ displayMemories.length }} 条结果
          <el-button text size="small" @click="handleClearSearch">清除搜索</el-button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading || searchLoading" class="loading-wrapper">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>{{ searchLoading ? '搜索中...' : '加载中...' }}</span>
        </div>

        <!-- 空状态 -->
        <div v-else-if="displayMemories.length === 0" class="empty-wrapper">
          <EmptyState
            icon="Memo"
            :title="isSearching ? '未找到匹配的记忆' : '还没有记忆'"
            :description="isSearching ? '尝试使用其他关键词搜索。' : '还没有记住关于你的信息，试试在聊天中告诉 AI 你的喜好，或手动添加一条记忆。'"
          />
        </div>

        <!-- 记忆卡片列表 -->
        <div v-else class="memory-list-wrapper">
          <div class="memory-list">
            <MemoryCard
              v-for="mem in displayMemories"
              :key="mem.id"
              :memory="mem"
              @edit="handleEdit"
              @deleted="loadData"
            />
          </div>
        </div>
      </div>

      <!-- 右栏：搜索 + 添加记忆 -->
      <div class="content-right">
        <div class="right-panel">
          <!-- 搜索 -->
          <MemorySearch
            :searching="searchLoading"
            :is-searching="isSearching"
            @search="handleSearch"
            @clear="handleClearSearch"
          />

          <!-- 添加记忆 -->
          <div class="add-section">
            <div class="add-header">
              <el-icon :size="16"><Plus /></el-icon>
              <span>添加记忆</span>
            </div>
            <el-input
              ref="addInputRef"
              v-model="newContent"
              type="textarea"
              :rows="4"
              placeholder="输入一条记忆内容，例如：用户喜欢喝咖啡"
              maxlength="500"
              show-word-limit
              resize="none"
            />
            <div class="add-actions">
              <el-button
                type="primary"
                :loading="adding"
                :disabled="!newContent.trim()"
                @click="handleAdd"
                style="width:100%"
              >
                保存记忆
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑记忆弹窗 -->
    <MemoryEditDialog
      v-model="editDialogVisible"
      :memory="editingMemory"
      @saved="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading, Plus } from '@element-plus/icons-vue';
import { getMemoryList, addMemory, searchMemory, clearAllMemories } from '@/api/memory';
import type { MemoryItem } from '@/api/memory';
import EmptyState from '@/components/common/EmptyState.vue';
import MemoryStats from '@/components/memory/MemoryStats.vue';
import MemorySearch from '@/components/memory/MemorySearch.vue';
import MemoryCard from '@/components/memory/MemoryCard.vue';
import MemoryEditDialog from '@/components/memory/MemoryEditDialog.vue';

const memories = ref<MemoryItem[]>([]);
const loading = ref(true);
const newContent = ref('');
const adding = ref(false);
const addInputRef = ref<InstanceType<typeof import('element-plus')['ElInput']> | null>(null);

// 搜索状态
const isSearching = ref(false);
const searchQuery = ref('');
const searchResults = ref<MemoryItem[]>([]);
const searchLoading = ref(false);

// 编辑弹窗状态
const editDialogVisible = ref(false);
const editingMemory = ref<MemoryItem | null>(null);

// 当前显示的列表（全部记忆 或 搜索结果）
const displayMemories = computed(() => {
  if (isSearching.value) {
    return [...searchResults.value].sort((a, b) => {
      const ta = a.metadata?.created_at || '';
      const tb = b.metadata?.created_at || '';
      return tb.localeCompare(ta);
    });
  }
  return [...memories.value].sort((a, b) => {
    const ta = a.metadata?.created_at || '';
    const tb = b.metadata?.created_at || '';
    return tb.localeCompare(ta);
  });
});

const loadData = async () => {
  loading.value = true;
  try {
    memories.value = await getMemoryList();
  } catch (error) {
    console.error('加载记忆列表失败:', error);
    ElMessage.error('加载记忆列表失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const handleAdd = async () => {
  const content = newContent.value.trim();
  if (!content) return;

  adding.value = true;
  try {
    const result = await addMemory(content);
    if (result.success) {
      ElMessage.success('记忆添加成功');
      newContent.value = '';
      await loadData();
    } else {
      ElMessage.error(result.message || '添加失败');
    }
  } catch (error) {
    console.error('添加记忆失败:', error);
    ElMessage.error('添加记忆失败，请稍后重试');
  } finally {
    adding.value = false;
  }
};

/** 顶部「添加记忆」按钮点击：聚焦右侧输入框 */
const handleFocusAdd = async () => {
  // 等待 DOM 更新后聚焦输入框
  await nextTick();
  addInputRef.value?.focus();
};

// 搜索
const handleSearch = async (query: string) => {
  searchQuery.value = query;
  searchLoading.value = true;
  isSearching.value = true;
  try {
    searchResults.value = await searchMemory(query);
  } catch (error) {
    console.error('搜索记忆失败:', error);
    ElMessage.error('搜索失败，请稍后重试');
  } finally {
    searchLoading.value = false;
  }
};

const handleClearSearch = () => {
  isSearching.value = false;
  searchQuery.value = '';
  searchResults.value = [];
};

// 编辑
const handleEdit = (id: string) => {
  // 在当前显示的记忆中查找
  const memory = displayMemories.value.find(m => m.id === id);
  if (!memory) return;
  editingMemory.value = memory;
  editDialogVisible.value = true;
};

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有记忆吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    );
    const result = await clearAllMemories();
    if (result.success) {
      ElMessage.success('所有记忆已清空');
      // 如果正在搜索，也清空搜索状态
      if (isSearching.value) {
        handleClearSearch();
      }
      await loadData();
    } else {
      ElMessage.error(result.message || '清空失败');
    }
  } catch {
    // 用户取消操作
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.view-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-body);
}

.memory-content {
  display: flex;
  gap: var(--space-6);
  padding: var(--space-6);
  width: 80%;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - var(--header-height));
}

.content-left {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.content-right {
  width: 420px;
  flex-shrink: 0;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  position: sticky;
  top: 0;
}

/* 搜索结果提示 */
.search-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  padding: 0 var(--space-1);
}

/* 添加记忆面板 */
.add-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.add-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--primary-600);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--border-color-light);
}

.add-header .el-icon {
  color: var(--primary-500);
}

.add-actions {
  display: flex;
  gap: var(--space-2);
}

/* 加载状态 */
.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-10);
  font-size: var(--text-lg);
  color: var(--text-tertiary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

/* 记忆列表容器 */
.memory-list-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>