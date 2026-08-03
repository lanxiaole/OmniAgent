import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getModels, setDefaultModel } from '@/api/models';
import type { ModelConfigResponse } from '@/api/models';

export const useModelStore = defineStore('model', () => {
  const models = ref<ModelConfigResponse[]>([]);
  const currentModelId = ref<string | null>(null);
  const loading = ref(false);
  const switching = ref(false);

  const loadModels = async () => {
    loading.value = true;
    try {
      const data = await getModels();
      models.value = data.models;
      if (data.current_id) {
        currentModelId.value = data.current_id;
      } else if (models.value.length > 0) {
        const defaultModel = models.value.find(m => m.is_default);
        currentModelId.value = defaultModel?.id || models.value[0]?.id || null;
      }
    } finally {
      loading.value = false;
    }
  };

  const currentModel = computed(() =>
    models.value.find(m => m.id === currentModelId.value) || null
  );

  const selectModel = async (id: string) => {
    if (switching.value || id === currentModelId.value) return;
    switching.value = true;
    try {
      // 调用后端 API 切换默认模型，这会同步到 LLM_* 环境变量并重置 Agent
      await setDefaultModel(id);
      // 切换成功后，从后端刷新模型列表
      await loadModels();
    } catch (e) {
      console.error('切换模型失败:', e);
      // 切换失败时保持当前模型不变
    } finally {
      switching.value = false;
    }
  };

  return {
    models,
    currentModelId,
    currentModel,
    loading,
    switching,
    loadModels,
    selectModel,
  };
});