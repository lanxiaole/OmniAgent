<template>
  <!-- 场景管理：占位页面，后续开发 -->
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">场景管理</h2>
    </div>
    <EmptyState
      title="场景管理开发中"
      description="该功能正在规划设计中，敬请期待。"
    />
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/common/EmptyState.vue';
</script>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
</style>