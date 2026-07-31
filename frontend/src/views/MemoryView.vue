<template>
  <div class="view-container">
    <div class="memory-content">
      <!-- 统计卡片 + 操作按钮 -->
      <MemoryStats
        :count="displayMemories.length"
        @add="showAddInput = true"
        @clear="handleClearAll"
      />

      <!-- 搜索组件 -->
      <MemorySearch
        :searching="searchLoading"
        :is-searching="isSearching"
        @search="handleSearch"
        @clear="handleClearSearch"
      />

      <!-- 添加记忆输入区 -->
      <transition name="slide-fade">
        <div v-if="showAddInput" class="add-section">
          <el-input
            v-model="newContent"
            type="textarea"
            :rows="3"
            placeholder="输入一条记忆内容，例如：用户喜欢喝咖啡"
            maxlength="500"
            show-word-limit
            resize="none"
          />
          <div class="add-actions">
            <el-button @click="cancelAdd">取消</el-button>
            <el-button
              type="primary"
              :loading="adding"
              :disabled="!newContent.trim()"
              @click="handleAdd"
            >
              保存
            </el-button>
          </div>
        </div>
      </transition>

      <!-- 搜索结果提示 -->
      <div v-if="isSearching" class="search-hint">
        搜索 "{{ searchQuery }}" 共找到 {{ displayMemories.length }} 条结果
      </div>

      <!-- 记忆卡片列表 -->
      <div v-if="loading || searchLoading" class="loading-wrapper">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>{{ searchLoading ? '搜索中...' : '加载中...' }}</span>
      </div>
      <div v-else-if="displayMemories.length === 0" class="empty-wrapper">
        <EmptyState
          icon="Memo"
          :title="isSearching ? '未找到匹配的记忆' : '还没有记忆'"
          :description="isSearching ? '尝试使用其他关键词搜索。' : '还没有记住关于你的信息，试试在聊天中告诉 AI 你的喜好，或手动添加一条记忆。'"
        />
      </div>
      <div v-else class="memory-list">
        <MemoryCard
          v-for="mem in displayMemories"
          :key="mem.id"
          :memory="mem"
          @edit="handleEdit"
          @deleted="loadData"
        />
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
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { getMemoryList, addMemory, searchMemory, clearAllMemories } from '@/api/memory';
import type { MemoryItem } from '@/api/memory';
import EmptyState from '@/components/common/EmptyState.vue';
import MemoryStats from '@/components/memory/MemoryStats.vue';
import MemorySearch from '@/components/memory/MemorySearch.vue';
import MemoryCard from '@/components/memory/MemoryCard.vue';
import MemoryEditDialog from '@/components/memory/MemoryEditDialog.vue';

const memories = ref<MemoryItem[]>([]);
const loading = ref(true);
const showAddInput = ref(false);
const newContent = ref('');
const adding = ref(false);

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
      showAddInput.value = false;
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

const cancelAdd = () => {
  newContent.value = '';
  showAddInput.value = false;
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
  overflow: auto;
  background-color: var(--bg-body);
}

.memory-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6);
  width: 80%;
  max-width: 800px;
  margin: 0 auto;
}

/* 添加输入区 */
.add-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.add-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

/* 搜索结果提示 */
.search-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  padding: 0 var(--space-1);
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all var(--transition-normal);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
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
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

/* 记忆列表 */
.memory-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>