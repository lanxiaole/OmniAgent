<template>
  <el-dropdown
    v-if="models.length > 1"
    @command="handleCommand"
    trigger="click"
    placement="top-end"
  >
    <button class="model-selector-btn">
      <span class="model-short">{{ currentModelShort }}</span>
      <el-icon size="12"><ArrowDown /></el-icon>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="model in models"
          :key="model.id"
          :command="model.id"
          :class="{ active: model.id === currentModelId }"
        >
          <span>{{ model.name }}</span>
          <el-icon v-if="model.id === currentModelId" size="14"><Check /></el-icon>
        </el-dropdown-item>
        <el-dropdown-item divided command="settings">
          <el-icon size="14"><Setting /></el-icon>
          <span>配置模型</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <button
    v-else-if="models.length === 1"
    class="model-selector-btn readonly"
    disabled
  >
    <span class="model-short">{{ models[0]?.name }}</span>
  </button>

  <button
    v-else
    class="model-selector-btn no-model"
    @click="goToSettings"
  >
    <span class="model-short">请先配置模型</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowDown, Check, Setting } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { useModelStore } from '@/stores/modelStore';

const router = useRouter();
const modelStore = useModelStore();

const { models, currentModelId, currentModel } = storeToRefs(modelStore);

const currentModelShort = computed(() => {
  return currentModel.value?.name || '选择模型';
});

const handleCommand = (command: string) => {
  if (command === 'settings') {
    router.push('/settings');
  } else {
    modelStore.selectModel(command);
  }
};

const goToSettings = () => {
  router.push('/settings');
};
</script>

<style scoped>
.model-selector-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.model-selector-btn:hover {
  border-color: var(--primary-500);
  color: var(--primary-500);
}

.model-selector-btn.readonly {
  cursor: default;
  opacity: 0.8;
}

.model-selector-btn.readonly:hover {
  border-color: var(--border-color);
  color: var(--text-primary);
}

.model-selector-btn.no-model {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.model-selector-btn.no-model:hover {
  color: var(--primary-500);
  border-color: var(--primary-500);
}

.model-short {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm);
  min-width: 160px;
}

:deep(.el-dropdown-menu__item.active) {
  color: var(--primary-500);
  font-weight: 600;
}

:deep(.el-dropdown-menu__item .el-icon) {
  margin-left: auto;
}
</style>