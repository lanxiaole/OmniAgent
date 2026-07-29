<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <main class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from './AppSidebar.vue';
import AppHeader from './AppHeader.vue';
</script>

<style scoped>
.app-layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-body);
}

.app-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

.app-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

/* 页面切换动画 */
.page-enter-active,
.page-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
