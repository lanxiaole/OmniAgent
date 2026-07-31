<template>
  <div class="retrieval-tester">
    <h3 class="section-title">检索沙盒</h3>

    <!-- 搜索输入区 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="输入关键词检索知识库..."
        :prefix-icon="Search"
        clearable
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" :loading="searching" @click="handleSearch">
        {{ searching ? '搜索中...' : '搜索' }}
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="searching" v-loading="searching" class="loading-area" />

    <!-- 空状态：未搜索 -->
    <EmptyState
      v-else-if="!hasSearched"
      icon="Search"
      title="搜索知识库"
      description="输入关键词，检索知识库中的文档内容"
    />

    <!-- 空状态：无结果 -->
    <EmptyState
      v-else-if="hasSearched && searchResults.length === 0"
      icon="CircleClose"
      title="未找到相关内容"
      description="请尝试其他关键词"
    />

    <!-- 结果列表 -->
    <div v-else class="results-list">
      <div class="result-count">共找到 {{ searchResults.length }} 条结果</div>

      <div
        v-for="(item, index) in searchResults"
        :key="index"
        class="result-card"
      >
        <!-- 元数据标签 -->
        <div class="result-meta">
          <el-tag size="small" type="info" effect="plain">
            <el-icon :size="12"><Document /></el-icon>
            {{ item.metadata.source || '未知来源' }}
          </el-tag>
          <el-tag
            v-if="item.metadata.section"
            size="small"
            type="warning"
            effect="plain"
          >
            {{ item.metadata.section }}
          </el-tag>
          <el-tag
            v-if="item.metadata.line"
            size="small"
            type="success"
            effect="plain"
          >
            第 {{ item.metadata.line }} 行
          </el-tag>
        </div>

        <!-- 内容预览 -->
        <div class="result-content">
          <MarkdownRenderer :content="item.content" />
        </div>

        <!-- 操作按钮 -->
        <div class="result-actions">
          <el-button size="small" text @click="handleCopy(item.content)">
            <el-icon><CopyDocument /></el-icon>
            复制内容
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Search,
  Document,
  CopyDocument
} from '@element-plus/icons-vue';
import { searchKnowledge } from '@/api/knowledge';
import type { SearchResultItem } from '@/api/knowledge';
import { copyToClipboard } from '@/utils/markdown';
import MarkdownRenderer from '@/components/chat/MarkdownRenderer.vue';
import EmptyState from '@/components/common/EmptyState.vue';

const searchQuery = ref('');
const searchResults = ref<SearchResultItem[]>([]);
const searching = ref(false);
const hasSearched = ref(false);

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return;
  searching.value = true;
  hasSearched.value = true;
  try {
    searchResults.value = await searchKnowledge(searchQuery.value);
  } catch (error) {
    console.error('搜索失败:', error);
    ElMessage.error('搜索失败，请稍后重试');
  } finally {
    searching.value = false;
  }
};

const handleCopy = async (content: string) => {
  const ok = await copyToClipboard(content);
  if (ok) {
    ElMessage.success('内容已复制到剪贴板');
  } else {
    ElMessage.error('复制失败，请手动复制');
  }
};
</script>

<style scoped>
.retrieval-tester {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.search-bar {
  display: flex;
  gap: var(--space-3);
}

.search-bar .el-input {
  flex: 1;
}

.loading-area {
  min-height: 120px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.result-count {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.result-meta .el-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.result-content {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  max-height: 300px;
  overflow-y: auto;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-color);
}
</style>