<template>
  <div
    class="scenario-card"
    :class="{ active: active, disabled: disabled }"
    @click="handleClick"
  >
    <div class="card-icon">
      <el-icon :size="32">
        <component :is="iconComponent" />
      </el-icon>
    </div>
    <div class="card-name">{{ scenario.name }}</div>
    <div class="card-desc">{{ scenario.description }}</div>
    <div v-if="active" class="card-badge">已激活</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  ChatRound,
  Cpu,
  Search,
  EditPen,
} from '@element-plus/icons-vue';
import type { ScenarioPreset } from '@/types/settings';

const props = defineProps<{
  scenario: ScenarioPreset;
  active: boolean;
  disabled: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', scenarioId: string): void;
}>();

const iconMap: Record<string, any> = {
  ChatRound,
  Cpu,
  Search,
  EditPen,
};

const iconComponent = computed(() => {
  return iconMap[props.scenario.icon] || ChatRound;
});

const handleClick = () => {
  if (props.disabled) return;
  emit('select', props.scenario.id);
};
</script>

<style scoped>
.scenario-card {
  width: 180px;
  height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color, #e4e7ed);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 200ms ease;
  position: relative;
  user-select: none;
}

.scenario-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.10);
  border-color: var(--primary-500, #409eff);
}

.scenario-card.active {
  border: 2px solid var(--primary-500, #409eff);
  background: var(--primary-50, #ecf5ff);
}

.scenario-card.active:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.18);
}

.scenario-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.card-icon {
  color: var(--primary-500, #409eff);
  display: flex;
  align-items: center;
  justify-content: center;
}

.scenario-card.active .card-icon {
  color: var(--primary-500, #409eff);
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
  text-align: center;
}

.card-desc {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  text-align: center;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 11px;
  color: var(--primary-500, #409eff);
  background: var(--primary-100, #d9ecff);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
</style>