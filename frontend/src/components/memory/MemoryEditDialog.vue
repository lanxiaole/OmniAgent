<template>
  <el-dialog
    :model-value="modelValue"
    title="编辑记忆"
    width="560px"
    top="20vh"
    destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-input
      v-model="editContent"
      type="textarea"
      :rows="4"
      maxlength="500"
      show-word-limit
      resize="none"
      placeholder="输入新的记忆内容"
    />
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button
        type="primary"
        :loading="saving"
        :disabled="!editContent.trim()"
        @click="handleSave"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { updateMemory } from '@/api/memory';
import type { MemoryItem } from '@/api/memory';

interface Props {
  modelValue: boolean;
  memory: MemoryItem | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  saved: [];
}>();

const editContent = ref('');
const saving = ref(false);

// 当弹窗打开时，同步记忆内容到输入框
watch(() => props.modelValue, (visible) => {
  if (visible && props.memory) {
    editContent.value = props.memory.content;
  }
});

const handleSave = async () => {
  const content = editContent.value.trim();
  if (!content || !props.memory) return;

  saving.value = true;
  try {
    const result = await updateMemory(props.memory.id, content);
    if (result.success) {
      ElMessage.success('记忆更新成功');
      emit('update:modelValue', false);
      emit('saved');
    } else {
      ElMessage.error(result.message || '更新失败');
    }
  } catch (error) {
    console.error('更新记忆失败:', error);
    ElMessage.error('更新记忆失败，请稍后重试');
  } finally {
    saving.value = false;
  }
};
</script>