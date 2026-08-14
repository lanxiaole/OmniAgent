<template>
  <div class="scenario-selector">
    <div class="scenario-header">
      <span class="scenario-label">场景模式</span>
      <el-tooltip
        content="切换场景将影响后续新建会话的提示词和可用工具，当前对话不受影响"
        placement="top"
      >
        <el-icon class="hint-icon"><WarningFilled /></el-icon>
      </el-tooltip>
    </div>
    <div class="scenario-options">
      <div
        v-for="preset in presets"
        :key="preset.id"
        class="scenario-option"
        :class="{ active: currentScenarioId === preset.id, disabled: switching }"
        @click="handleSwitch(preset.id)"
      >
        <el-tooltip :content="preset.description" placement="top" :show-after="300">
          <div class="scenario-content">
            <el-icon :size="22" class="scenario-icon">
              <component :is="iconMap[preset.icon] || ChatRound" />
            </el-icon>
            <span class="scenario-name">{{ preset.name }}</span>
          </div>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  ChatRound,
  Cpu,
  Search,
  EditPen,
  WarningFilled,
} from '@element-plus/icons-vue';
import { getScenarios, getCurrentScenario, switchScenario } from '@/api/settings';
import type { ScenarioPreset } from '@/types/settings';

const presets = ref<ScenarioPreset[]>([]);
const currentScenarioId = ref('');
const loading = ref(false);
const switching = ref(false);

// 图标映射表
const iconMap: Record<string, any> = {
  ChatRound,
  Cpu,
  Search,
  EditPen,
};

const handleSwitch = async (scenarioId: string) => {
  if (switching.value || currentScenarioId.value === scenarioId) return;

  switching.value = true;
  try {
    const result = await switchScenario(scenarioId);
    currentScenarioId.value = scenarioId;
    ElMessage.success(result.message);
  } catch (e: any) {
    ElMessage.error(e?.detail || e?.message || '切换场景失败');
  } finally {
    switching.value = false;
  }
};

onMounted(async () => {
  loading.value = true;
  try {
    const [presetList, currentId] = await Promise.all([
      getScenarios(),
      getCurrentScenario(),
    ]);
    presets.value = presetList;
    currentScenarioId.value = currentId;
  } catch {
    ElMessage.error('加载场景配置失败');
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.scenario-selector {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 20px 24px;
  border: 1px solid var(--border-color, #e4e7ed);
}

.scenario-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
}

.scenario-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.hint-icon {
  color: var(--text-secondary, #909399);
  font-size: 14px;
  cursor: pointer;
}

.scenario-options {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.scenario-option {
  flex: 1;
  min-width: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e4e7ed);
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-color, #f5f7fa);
  user-select: none;
}

.scenario-option:hover {
  border-color: var(--el-color-primary, #409eff);
  color: var(--el-color-primary, #409eff);
  background: var(--el-color-primary-light-9, #ecf5ff);
}

.scenario-option.active {
  border-color: var(--el-color-primary, #409eff);
  background: var(--el-color-primary-light-9, #ecf5ff);
  color: var(--el-color-primary, #409eff);
}

.scenario-option.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.scenario-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scenario-icon {
  flex-shrink: 0;
}

.scenario-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}
</style>