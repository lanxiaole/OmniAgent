<template>
  <div class="memory-search">
    <div class="search-input-row">
      <el-input
        v-model="query"
        placeholder="搜索记忆内容..."
        clearable
        :prefix-icon="Search"
        @keyup.enter="handleSearch"
        @clear="handleClear"
      />
      <el-button
        type="primary"
        :icon="Search"
        :loading="searching"
        :disabled="!query.trim()"
        @click="handleSearch"
      >
        搜索
      </el-button>
      <el-button
        v-if="isSearching"
        :icon="Close"
        @click="handleClear"
      >
        清空搜索
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Search, Close } from '@element-plus/icons-vue';

interface Props {
  searching: boolean;
  isSearching: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  search: [query: string];
  clear: [];
}>();

const query = ref('');

const handleSearch = () => {
  const q = query.value.trim();
  if (!q) return;
  emit('search', q);
};

const handleClear = () => {
  query.value = '';
  emit('clear');
};
</script>

<style scoped>
.memory-search {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.search-input-row {
  display: flex;
  gap: var(--space-2);
}

.search-input-row .el-input {
  flex: 1;
}
</style>