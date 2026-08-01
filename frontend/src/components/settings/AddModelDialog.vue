<template>
  <el-dialog
    :model-value="visible"
    title="添加模型"
    width="520px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent
    >
      <!-- 模型名称 -->
      <el-form-item label="模型名称" prop="name">
        <el-input v-model="form.name" placeholder="例如：我的DeepSeek" />
      </el-form-item>

      <!-- 提供商 -->
      <el-form-item label="提供商" prop="provider">
        <el-select
          v-model="form.provider"
          placeholder="选择提供商"
          style="width: 100%"
          @change="onProviderChange"
        >
          <el-option label="DeepSeek" value="deepseek" />
          <el-option label="阿里云百炼" value="qwen" />
          <el-option label="OpenAI" value="openai" />
          <el-option label="自定义" value="custom" />
        </el-select>
      </el-form-item>

      <!-- Base URL -->
      <el-form-item label="Base URL" prop="base_url">
        <el-input v-model="form.base_url" placeholder="https://api.example.com/v1" />
      </el-form-item>

      <!-- API Key -->
      <el-form-item label="API Key" prop="api_key">
        <el-input
          v-model="form.api_key"
          type="password"
          placeholder="sk-..."
          show-password
        />
      </el-form-item>

      <!-- 模型名 -->
      <el-form-item label="模型" prop="model">
        <el-input v-model="form.model" placeholder="例如：deepseek-v4-flash" />
      </el-form-item>

      <!-- 设为默认 -->
      <el-form-item label="设为默认">
        <el-switch v-model="form.is_default" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { addModel } from '@/api/models';

const emit = defineEmits<{
  close: [];
  saved: [];
}>();

const props = defineProps<{
  visible: boolean;
}>();

const PROVIDER_TEMPLATES: Record<string, { base_url: string; model: string }> = {
  deepseek: {
    base_url: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
  },
  qwen: {
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen3.7-plus',
  },
  openai: {
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-4o',
  },
  custom: {
    base_url: '',
    model: '',
  },
};

interface FormData {
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model: string;
  is_default: boolean;
}

const formRef = ref<FormInstance>();
const saving = ref(false);

const form = reactive<FormData>({
  name: '',
  provider: '',
  base_url: '',
  api_key: '',
  model: '',
  is_default: false,
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入 API 地址', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
};

// 选择提供商时自动填充
const onProviderChange = (provider: string) => {
  const template = PROVIDER_TEMPLATES[provider];
  if (template) {
    form.base_url = template.base_url;
    form.model = template.model;
  }
};

const handleClose = () => {
  if (!saving.value) {
    resetForm();
    emit('close');
  }
};

const resetForm = () => {
  form.name = '';
  form.provider = '';
  form.base_url = '';
  form.api_key = '';
  form.model = '';
  form.is_default = false;
  formRef.value?.clearValidate();
};

const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;

  saving.value = true;
  try {
    await addModel({
      name: form.name,
      provider: form.provider,
      base_url: form.base_url,
      api_key: form.api_key,
      model: form.model,
    });
    ElMessage.success('模型添加成功');
    resetForm();
    emit('saved');
  } catch (e: any) {
    const detail = e?.detail || e?.message || '添加失败';
    ElMessage.error(detail);
  } finally {
    saving.value = false;
  }
};
</script>