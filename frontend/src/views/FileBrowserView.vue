<template>
  <div class="view-container">
    <EmptyState
      icon="Folder"
      title="文件浏览器"
      description="这里将提供项目文件和目录的树形浏览、文件预览、新建和上传功能。当前为框架占位页面。"
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
