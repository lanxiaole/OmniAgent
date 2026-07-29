<template>
  <div class="app-logo" :class="{ collapsed }">
    <div class="logo-mark">
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2.5" />
        <circle cx="16" cy="16" r="6" fill="currentColor" />
        <path d="M16 2V8M16 24V30M2 16H8M24 16H30" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
      </svg>
    </div>
    <span v-if="!collapsed" class="logo-text">OmniAgent</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  collapsed?: boolean;
}

withDefaults(defineProps<Props>(), {
  collapsed: false,
});
</script>

<style scoped>
.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 14px;
  user-select: none;
}

.app-logo.collapsed {
  justify-content: center;
  padding: 0;
}

.logo-mark {
  width: 28px;
  height: 28px;
  color: var(--primary-600);
  flex-shrink: 0;
}

.app-logo:hover .logo-mark {
  color: var(--primary-500);
}

.logo-mark svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  white-space: nowrap;
}
</style>
