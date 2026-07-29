<template>
  <div class="view-container">
    <EmptyState
      icon="Collection"
      title="知识库管理"
      description="这里将展示个人知识库文档列表，支持上传、删除和检索测试。当前为框架占位页面。"
    />
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/common/EmptyState.vue';
</script>

<style scoped>
.view-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: var(--bg-body);
}
</style>
