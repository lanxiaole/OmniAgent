<template>
  <div class="view-container">
    <EmptyState
      icon="Setting"
      title="系统设置"
      description="这里将展示 Agent 配置、主题偏好、工具开关等设置项。当前为框架占位页面。"
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
