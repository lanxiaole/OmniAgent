<template>
  <div class="settings-view">
    <h1 class="settings-title">设置</h1>
    <div class="settings-content">
      <StatusCards />
      <ModelManager />
      <WorkspaceManager />
      <AboutSection />
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusCards from '@/components/settings/StatusCards.vue';
import ModelManager from '@/components/settings/ModelManager.vue';
import WorkspaceManager from '@/components/settings/WorkspaceManager.vue';
import AboutSection from '@/components/settings/AboutSection.vue';
</script>

<style scoped>
.settings-view {
  padding: 24px 32px;
  max-width: 900px;
  margin: 0 auto;
  height: 100%;
  overflow-y: auto;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>