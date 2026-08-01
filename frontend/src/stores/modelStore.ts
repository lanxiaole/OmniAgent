import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getModels } from '@/api/models';
import type { ModelConfigResponse } from '@/api/models';

export const useModelStore = defineStore('model', () => {
  const models = ref<ModelConfigResponse[]>([]);
  const currentModelId = ref<string | null>(null);
  const loading = ref(false);

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

  const selectModel = (id: string) => {
    currentModelId.value = id;
  };

  return {
    models,
    currentModelId,
    currentModel,
    loading,
    loadModels,
    selectModel,
  };
});