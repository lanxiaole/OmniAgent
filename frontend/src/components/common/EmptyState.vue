<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <el-icon :size="48" color="var(--text-tertiary)">
          <component :is="icon" />
        </el-icon>
      </slot>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-desc">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon?: string;
  title: string;
  description?: string;
}

withDefaults(defineProps<Props>(), {
  icon: 'Box',
});
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-10);
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: var(--radius-xl);
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  margin-bottom: var(--space-2);
}

.empty-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.empty-desc {
  font-size: var(--text-md);
  color: var(--text-tertiary);
  max-width: 400px;
  line-height: var(--leading-relaxed);
}
</style>
