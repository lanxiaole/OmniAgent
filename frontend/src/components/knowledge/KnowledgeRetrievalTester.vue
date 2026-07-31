<template>
  <div class="retrieval-tester">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <el-icon :size="18" color="var(--primary-500)"><Compass /></el-icon>
        <span>探索知识库</span>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="card-body">
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
      <div v-else-if="!hasSearched" class="empty-state-wrapper">
        <EmptyState
          title="开始探索"
          description="输入关键词，检索知识库中的文档内容"
        >
          <template #icon>
            <el-icon :size="48" color="var(--text-tertiary)">
              <Compass />
            </el-icon>
          </template>
        </EmptyState>
      </div>

      <!-- 空状态：无结果 -->
      <div v-else-if="hasSearched && searchResults.length === 0" class="empty-state-wrapper">
        <EmptyState
          icon="CircleClose"
          title="未找到相关内容"
          description="请尝试其他关键词"
        />
      </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Search,
  Document,
  CopyDocument,
  Compass,
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
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-body);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--primary-600);
}

.card-body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.search-bar {
  display: flex;
  gap: var(--space-3);
}

.search-bar .el-input {
  flex: 1;
}

.loading-area {
  flex: 1;
  min-height: 0;
}

.empty-state-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
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
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.result-card:hover {
  border-color: rgba(59, 130, 246, 0.2);
  box-shadow: 0 1px 6px rgba(59, 130, 246, 0.06);
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