<template>
  <div class="view-container">
    <EmptyState
      icon="Brain"
      title="记忆管理"
      description="这里将展示 AI 记住的用户信息，支持查看、编辑、删除和搜索。当前为框架占位页面。"
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
