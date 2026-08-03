<template>
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">模型管理</h2>
      <el-button type="primary" size="small" :icon="Plus" @click="showAddDialog = true">
        添加模型
      </el-button>
    </div>

    <div v-if="loading" class="card-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else-if="models.length === 0" class="card-empty">
      <p>暂无已配置的模型，点击上方按钮添加</p>
    </div>
    <div v-else class="model-list">
      <div
        v-for="model in models"
        :key="model.id"
        class="model-card"
      >
        <div class="model-header">
          <div class="model-info">
            <span class="model-name">{{ model.name }}</span>
            <el-tag v-if="model.is_default" size="small" type="success" class="default-tag">默认</el-tag>
          </div>
          <el-tag size="small" effect="plain" class="provider-tag">
            {{ providerLabel(model.provider) }}
          </el-tag>
        </div>

        <div class="model-details">
          <div class="detail-row">
            <span class="detail-label">API 地址</span>
            <span class="detail-value">{{ model.base_url }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">API Key</span>
            <span class="detail-value mono">{{ model.api_key_masked }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">模型</span>
            <span class="detail-value">{{ model.model }}</span>
          </div>
        </div>

        <div class="model-actions">
          <el-button
            v-if="!model.is_default"
            size="small"
            text
            type="primary"
            :loading="settingDefault === model.id"
            @click="handleSetDefault(model.id)"
          >
            设为默认
          </el-button>
          <el-button
            size="small"
            text
            type="warning"
            :loading="testingId === model.id"
            @click="handleTest(model)"
          >
            测试连接
          </el-button>
          <el-button
            size="small"
            text
            type="danger"
            :loading="deletingId === model.id"
            @click="handleDelete(model)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 添加模型对话框 -->
    <AddModelDialog
      v-if="showAddDialog"
      :visible="showAddDialog"
      @close="showAddDialog = false"
      @saved="onModelSaved"
    />

    <!-- 测试连接对话框 -->
    <el-dialog
      v-model="showTestDialog"
      title="测试模型连接"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form v-if="testingModel" label-width="80px">
        <el-form-item label="API 地址">
          <el-input v-model="testingModel.base_url" disabled />
        </el-form-item>
        <el-form-item label="模型名">
          <el-input v-model="testingModel.model" disabled />
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input
            v-model="testApiKey"
            type="password"
            placeholder="请输入完整的 API Key"
            show-password
          />
        </el-form-item>
      </el-form>
      <div v-if="testResult !== null" class="test-result" :class="testResult.success ? 'test-success' : 'test-fail'">
        <el-icon :size="18">
          <SuccessFilled v-if="testResult.success" />
          <WarningFilled v-else />
        </el-icon>
        <span>{{ testResult.message }}</span>
      </div>
      <template #footer>
        <el-button @click="showTestDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="testRunning"
          :disabled="!testApiKey.trim()"
          @click="runTest"
        >
          测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Loading, SuccessFilled, WarningFilled } from '@element-plus/icons-vue';
import {
  getModels,
  deleteModel,
  setDefaultModel,
  testModelConnection,
} from '@/api/models';
import type { ModelConfigResponse } from '@/api/models';
import { useModelStore } from '@/stores/modelStore';
import AddModelDialog from './AddModelDialog.vue';

const modelStore = useModelStore();

const models = ref<ModelConfigResponse[]>([]);
const loading = ref(true);
const settingDefault = ref<string | null>(null);
const deletingId = ref<string | null>(null);

// 测试连接状态
const showTestDialog = ref(false);
const testingModel = ref<ModelConfigResponse | null>(null);
const testApiKey = ref('');
const testRunning = ref(false);
const testResult = ref<{ success: boolean; message: string } | null>(null);
const testingId = ref<string | null>(null);

// 添加对话框
const showAddDialog = ref(false);

const PROVIDER_LABELS: Record<string, string> = {
  deepseek: 'DeepSeek',
  qwen: '阿里云百炼',
  openai: 'OpenAI',
  custom: '自定义',
};

const providerLabel = (provider: string) => PROVIDER_LABELS[provider] || provider;

const loadModels = async () => {
  loading.value = true;
  try {
    const data = await getModels();
    models.value = data.models;
  } catch (e) {
    console.error('加载模型列表失败:', e);
    ElMessage.error('加载模型列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSetDefault = async (id: string) => {
  settingDefault.value = id;
  try {
    await setDefaultModel(id);
    await loadModels();
    // 同步刷新聊天界面的模型选择器
    await modelStore.loadModels();
    ElMessage.success('默认模型已更新');
  } catch (e) {
    console.error('设置默认模型失败:', e);
    ElMessage.error('设置默认模型失败');
  } finally {
    settingDefault.value = null;
  }
};

const handleTest = (model: ModelConfigResponse) => {
  testingModel.value = model;
  testApiKey.value = '';
  testResult.value = null;
  testingId.value = model.id;
  showTestDialog.value = true;
};

const runTest = async () => {
  if (!testingModel.value || !testApiKey.value.trim()) return;

  testRunning.value = true;
  testResult.value = null;
  try {
    const result = await testModelConnection({
      base_url: testingModel.value.base_url,
      api_key: testApiKey.value,
      model: testingModel.value.model,
    });
    testResult.value = result;
  } catch (e) {
    testResult.value = { success: false, message: '请求失败: ' + String(e) };
  } finally {
    testRunning.value = false;
    testingId.value = null;
  }
};

const handleDelete = async (model: ModelConfigResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    );
  } catch {
    return;
  }

  deletingId.value = model.id;
  try {
    const result = await deleteModel(model.id);
    if (result.success) {
      ElMessage.success(`模型 "${model.name}" 已删除`);
      await loadModels();
    } else {
      ElMessage.error(result.message || '删除失败');
    }
  } catch (e) {
    console.error('删除模型失败:', e);
    ElMessage.error('删除模型失败');
  } finally {
    deletingId.value = null;
  }
};

const onModelSaved = () => {
  showAddDialog.value = false;
  loadModels();
  // 同步刷新聊天界面的模型选择器
  modelStore.loadModels();
};

onMounted(() => {
  loadModels();
});
</script>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--text-tertiary);
  font-size: 15px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 15px;
}

.model-list {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.model-card {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px 18px;
  transition: border-color var(--transition-fast);
}

.model-card:hover {
  border-color: var(--border-color-strong);
}

.model-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.default-tag {
  flex-shrink: 0;
}

.provider-tag {
  flex-shrink: 0;
}

.model-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.detail-label {
  color: var(--text-tertiary);
  min-width: 64px;
  flex-shrink: 0;
}

.detail-value {
  color: var(--text-secondary);
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono {
  font-family: var(--font-mono);
  font-size: 13px;
}

.model-actions {
  display: flex;
  gap: 4px;
  border-top: 1px solid var(--border-color-light);
  padding-top: 10px;
}

/* 测试结果样式 */
.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin-top: 12px;
  font-size: 14px;
}

.test-success {
  background: var(--success);
  color: white;
  opacity: 0.9;
}

.test-fail {
  background: var(--danger);
  color: white;
  opacity: 0.9;
}
</style>