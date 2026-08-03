<template>
  <div class="api-config-card">
    <div class="card-header">
      <h3 class="card-title">其他 API 配置</h3>
      <el-button v-if="hasChanges" type="primary" size="small" :loading="saving" @click="handleSaveAll">
        保存全部
      </el-button>
    </div>
    <div class="card-body">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="20"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <template v-else>
        <!-- Embedding 配置 -->
        <div class="config-section">
          <h4 class="section-title">Embedding 配置</h4>
          <div class="config-items">
            <div v-for="item in embeddingItems" :key="item.key" class="config-item">
              <label class="config-label">{{ item.label }}</label>
              <el-input
                v-if="item.type === 'password'"
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                :type="passwordVisible[item.key] ? 'text' : 'password'"
                show-password
                size="small"
                @input="onChange"
              />
              <el-input
                v-else
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                size="small"
                @input="onChange"
              />
              <p v-if="item.hint" class="config-hint">{{ item.hint }}</p>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- Tavily 配置 -->
        <div class="config-section">
          <h4 class="section-title">Tavily 搜索</h4>
          <div class="config-items">
            <div v-for="item in tavilyItems" :key="item.key" class="config-item">
              <label class="config-label">{{ item.label }}</label>
              <el-input
                v-if="item.type === 'password'"
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                :type="passwordVisible[item.key] ? 'text' : 'password'"
                show-password
                size="small"
                @input="onChange"
              />
              <el-select
                v-else-if="item.type === 'select'"
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                size="small"
                style="width: 100%"
                @change="onChange"
              >
                <el-option v-for="opt in item.options" :key="opt" :label="opt" :value="opt" />
              </el-select>
              <el-input-number
                v-else-if="item.type === 'number'"
                :model-value="Number(form[item.key])"
                :min="0"
                :max="20"
                size="small"
                style="width: 100%"
                @update:model-value="(val: number | null) => { form[item.key] = String(val ?? 0); onChange(); }"
              />
              <el-input
                v-else
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                size="small"
                @input="onChange"
              />
              <p v-if="item.hint" class="config-hint">{{ item.hint }}</p>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- 高德地图配置 -->
        <div class="config-section">
          <h4 class="section-title">高德地图</h4>
          <div class="config-items">
            <div v-for="item in amapItems" :key="item.key" class="config-item">
              <label class="config-label">{{ item.label }}</label>
              <el-input
                v-model="form[item.key]"
                :placeholder="item.placeholder"
                type="password"
                show-password
                size="small"
                @input="onChange"
              />
              <p v-if="item.hint" class="config-hint">{{ item.hint }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { getEnvConfig, updateEnvConfig } from '@/api/settings';
import type { EnvConfigItem } from '@/api/settings';

const loading = ref(true);
const saving = ref(false);
const items = ref<EnvConfigItem[]>([]);
const form = reactive<Record<string, string>>({});
const original = reactive<Record<string, string>>({});
const savedState = reactive<Record<string, boolean>>({}); // 各键是否已写入 .env
const passwordVisible = reactive<Record<string, boolean>>({});

const hasChanges = computed(() => {
  // 有值变更 或 存在未保存到 .env 的配置项（如默认值未持久化）
  return items.value.some(item =>
    form[item.key] !== original[item.key] || !savedState[item.key]
  );
});

const embeddingItems = computed(() =>
  items.value.filter(i => i.key.startsWith('EMBEDDING_'))
);

const tavilyItems = computed(() =>
  items.value.filter(i => i.key.startsWith('TAVILY_'))
);

const amapItems = computed(() =>
  items.value.filter(i => i.key.startsWith('AMAP_'))
);

const onChange = () => {
  // 响应式，hasChanges 会自动更新
};

const loadConfig = async () => {
  loading.value = true;
  try {
    const data = await getEnvConfig();
    items.value = data.items;
    for (const item of data.items) {
      form[item.key] = item.value;
      original[item.key] = item.value;
      savedState[item.key] = item.saved;
    }
  } catch {
    ElMessage.error('加载配置失败');
  } finally {
    loading.value = false;
  }
};

const handleSaveAll = async () => {
  // 保存所有配置项，确保 .env 文件中有完整记录
  // 避免默认值（如 EMBEDDING_BASE_URL）未写入 .env 导致运行时依赖代码回退逻辑
  saving.value = true;
  let successCount = 0;
  for (const item of items.value) {
    try {
      const val = String(form[item.key] ?? '');
      if (!val) continue; // 跳过空值
      await updateEnvConfig(item.key, val);
      original[item.key] = val;
      savedState[item.key] = true;
      successCount++;
    } catch {
      ElMessage.error(`保存 ${item.label} 失败`);
    }
  }
  saving.value = false;
  if (successCount > 0) {
    ElMessage.success(`已保存 ${successCount} 项配置`);
  }
};

onMounted(loadConfig);
</script>

<style scoped>
.api-config-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-body {
  padding: 20px 24px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--text-tertiary);
}

.config-section {
  padding: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.config-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.config-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 2px 0 0;
}
</style>