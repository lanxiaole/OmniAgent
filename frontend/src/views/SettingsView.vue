<template>
  <div class="settings-view">
    <h1 class="settings-title">设置</h1>
    <div class="settings-grid">
      <!-- 左侧列 -->
      <div class="settings-left">
        <StatusCards />
        <ModelManager />
        <WorkspaceManager />
      </div>

      <!-- 右侧列 -->
      <div class="settings-right">
        <ApiConfig />
        <AboutSection />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusCards from '@/components/settings/StatusCards.vue';
import ModelManager from '@/components/settings/ModelManager.vue';
import WorkspaceManager from '@/components/settings/WorkspaceManager.vue';
import AboutSection from '@/components/settings/AboutSection.vue';
import ApiConfig from '@/components/settings/ApiConfig.vue';
</script>

<style scoped>
.settings-view {
  padding: 32px 40px;
  height: 100%;
  overflow-y: auto;
}

.settings-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 28px;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.settings-left,
.settings-right {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
</style>