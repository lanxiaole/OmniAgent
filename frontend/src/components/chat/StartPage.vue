<template>
  <div class="start-page">
    <!-- 品牌标识区 -->
    <div class="brand-area">
      <div class="brand-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="10" fill="var(--primary-500, #409eff)" />
          <path d="M12 20L18 26L28 14" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h1 class="brand-title">OmniAgent</h1>
      <p class="brand-slogan">选择你的工作场景，开始高效协作</p>
    </div>

    <!-- 场景卡片网格 -->
    <div class="scenario-grid">
      <ScenarioCard
        v-for="preset in visiblePresets"
        :key="preset.id"
        :scenario="preset"
        :active="activeScenarioId === preset.id"
        :disabled="switching"
        @select="handleScenarioSelect"
      />
    </div>

    <!-- 底部输入框 -->
    <div class="start-input-area">
      <div class="start-input-box" :class="{ focus: inputFocused }">
        <textarea
          ref="textareaRef"
          class="start-textarea"
          v-model="inputText"
          :placeholder="inputPlaceholder"
          rows="1"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
          @input="autoResize"
          @keydown="handleKeydown"
        />
        <div class="start-input-actions">
          <div class="action-left"></div>
          <div class="action-right">
            <button
              class="start-send-btn"
              :disabled="!inputText.trim()"
              @click="handleSend"
              type="button"
            >
              <span>开始对话</span>
              <el-icon :size="18"><Promotion /></el-icon>
            </button>
          </div>
        </div>
      </div>
      <p class="start-input-hint">
        OmniAgent 支持调用多种工具（查询天气、网络搜索、读写文件、执行代码、知识库检索等），生成内容请自行核实。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Promotion } from '@element-plus/icons-vue';
import ScenarioCard from './ScenarioCard.vue';
import { getScenarios, getCurrentScenario, switchScenario } from '@/api/settings';
import type { ScenarioPreset } from '@/types/settings';

const emit = defineEmits<{
  (e: 'send', message: string): void;
  (e: 'scenario-selected', scenarioId: string): void;
}>();

const presets = ref<ScenarioPreset[]>([]);
const activeScenarioId = ref('');
const loading = ref(false);
const switching = ref(false);
const inputText = ref('');
const inputFocused = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

// 仅展示启用显示偏好的场景（默认全部展示）
const visiblePresets = computed(() => presets.value.filter(p => p.display !== false));

const inputPlaceholder = computed(() => {
  if (activeScenarioId.value === 'default') {
    return '告诉 OmniAgent 你要做什么…';
  }
  const active = presets.value.find(p => p.id === activeScenarioId.value);
  if (active) {
    return `向${active.name}提问...`;
  }
  return '告诉 OmniAgent 你要做什么…';
});

const handleScenarioSelect = async (scenarioId: string) => {
  if (switching.value || activeScenarioId.value === scenarioId) return;

  switching.value = true;
  try {
    const result = await switchScenario(scenarioId);
    activeScenarioId.value = scenarioId;
    emit('scenario-selected', scenarioId);
    ElMessage.success(result.message);
    // 输入框自动获得焦点
    nextTick(() => {
      textareaRef.value?.focus();
    });
  } catch (e: any) {
    ElMessage.error(e?.detail || e?.message || '切换场景失败');
  } finally {
    switching.value = false;
  }
};

const handleSend = () => {
  const msg = inputText.value.trim();
  if (!msg) return;
  emit('send', msg);
  inputText.value = '';
};

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
};

const autoResize = async () => {
  await nextTick();
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  const next = Math.min(el.scrollHeight, 240);
  el.style.height = `${next}px`;
};

onMounted(async () => {
  loading.value = true;
  try {
    const [presetList, currentId] = await Promise.all([
      getScenarios(),
      getCurrentScenario(),
    ]);
    presets.value = presetList;
    activeScenarioId.value = currentId;
  } catch {
    ElMessage.error('加载场景配置失败');
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.start-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 24px;
  gap: 36px;
  overflow-y: auto;
}

/* 品牌区域 */
.brand-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary, #303133);
  margin: 0;
  letter-spacing: -0.5px;
}

.brand-slogan {
  font-size: 15px;
  color: var(--text-secondary, #909399);
  margin: 0;
}

/* 场景卡片网格（响应式，适配窗口宽度） */
.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  justify-content: center;
  width: 100%;
  max-width: 800px;
}

/* 底部输入框 */
.start-input-area {
  width: 100%;
  max-width: 720px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.start-input-box {
  width: 100%;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 10px 12px 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: all 180ms ease;
}

.start-input-box.focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08), 0 4px 16px rgba(37, 99, 235, 0.12);
}

.start-textarea {
  width: 100%;
  min-height: 28px;
  max-height: 240px;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-md);
  line-height: 1.65;
  padding: 6px 6px 8px;
}

.start-textarea::placeholder {
  color: var(--text-tertiary);
}

.start-input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 4px 2px 2px;
}

.action-left {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.action-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.start-send-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: var(--radius-full);
  border: 1px solid transparent;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.18);
}

.start-send-btn:hover {
  filter: brightness(1.04);
  transform: translateY(-0.5px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
}

.start-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
  filter: none;
}

.start-input-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  text-align: center;
}
</style>