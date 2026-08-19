<template>
  <div class="scenario-manager">
    <!-- 头部：标题 + 操作按钮 -->
    <div class="manager-header">
      <h2 class="manager-title">场景管理</h2>
      <div class="manager-actions">
        <el-button :icon="Download" @click="triggerImport">导入场景</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建场景</el-button>
      </div>
    </div>

    <p class="manager-tip">场景决定 Agent 的系统提示词与可用工具；自定义场景可自由创建、编辑与分享。</p>

    <!-- 场景卡片网格 -->
    <div v-if="loading" class="manager-loading">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="scenarios.length === 0" class="manager-empty">
      <el-empty description="暂无场景，点击右上角“新建场景”创建" />
    </div>

    <div v-else class="scenario-grid">
      <div
        v-for="s in scenarios"
        :key="s.id"
        class="scenario-card"
        :class="{ system: s.is_system, active: s.id === activeId }"
        @click="setCurrent(s)"
      >
        <!-- 顶部：图标与标签 -->
        <div class="card-top">
          <div class="card-icon-area">
            <el-icon :size="26" class="card-icon">
              <component :is="iconComponent(s)" />
            </el-icon>
          </div>
          <div class="badges">
            <span v-if="s.is_system" class="badge badge-system" title="系统内置场景，仅供查看">系统</span>
            <span v-else class="badge badge-custom">自定义</span>
            <span v-if="s.id === activeId" class="badge badge-active">使用中</span>
          </div>
        </div>

        <!-- 名称与描述 -->
        <div class="card-info">
          <div class="card-name">{{ s.name }}</div>
          <div class="card-desc">{{ s.description || '暂无描述' }}</div>
        </div>

        <!-- 显示开关 -->
        <div class="card-display" @click.stop>
          <span class="display-label">启动页展示</span>
          <el-switch
            :model-value="s.display !== false"
            size="small"
            @change="(val: boolean | string | number) => toggleDisplay(s, !!val)"
          />
        </div>

        <!-- 操作按钮 -->
        <div class="card-actions" @click.stop>
          <el-button
            size="small"
            :icon="Switch"
            :disabled="s.id === activeId"
            @click="setCurrent(s)"
          >
            设为当前
          </el-button>
          <template v-if="!s.is_system">
            <el-button size="small" :icon="Edit" @click="openEdit(s)">编辑</el-button>
            <el-button size="small" :icon="CopyDocument" @click="duplicate(s)">复制</el-button>
          </template>
          <el-button size="small" :icon="Download" @click="doExport(s)">导出</el-button>
          <el-button
            v-if="!s.is_system"
            size="small"
            type="danger"
            plain
            :icon="Delete"
            @click="confirmDelete(s)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑表单对话框 -->
    <el-dialog
      v-model="formVisible"
      :title="editingId ? '编辑场景' : '新建场景'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="88px" label-position="left">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="请输入场景名称" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="图标">
          <div class="icon-picker">
            <button
              v-for="ic in iconOptions"
              :key="ic.value"
              type="button"
              class="icon-option"
              :class="{ selected: form.icon === ic.value }"
              @click="form.icon = ic.value"
            >
              <el-icon :size="18"><component :is="ic.icon" /></el-icon>
            </button>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="一句话描述该场景的用途" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="6"
            placeholder="设定 Agent 的身份、能力与行为准则…"
          />
        </el-form-item>
        <el-form-item label="启用工具">
          <div class="tool-config">
            <el-switch v-model="useAllTools" active-text="启用全部工具" />
            <template v-if="!useAllTools">
              <el-select
                v-model="form.enabled_tools"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择要启用的工具"
                style="width: 100%"
              >
                <el-option v-for="t in toolOptions" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </template>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteVisible" title="删除场景" width="420px">
      <p class="delete-text">
        确定要删除场景"{{ deletingTarget?.name ?? '' }}"吗？该操作不可恢复。
      </p>
      <template #footer>
        <el-button @click="deleteVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmDeleteAction">删除</el-button>
      </template>
    </el-dialog>

    <!-- 导入文件选择 -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".json,application/json"
      class="hidden-input"
      @change="handleImportFile"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Loading,
  Plus,
  Download,
  Switch,
  Edit,
  CopyDocument,
  Delete,
  ChatRound,
  Cpu,
  Search,
  EditPen,
  DataLine,
  Files,
  Star,
  Lightning,
} from '@element-plus/icons-vue';
import {
  getScenarios,
  getCurrentScenario,
  switchScenario,
  createScenario,
  updateScenario,
  deleteScenario,
  duplicateScenario,
  updateScenarioDisplay,
  importScenario,
  exportScenario,
} from '@/api/settings';
import type { ScenarioPreset, ScenarioForm } from '@/types/settings';

// ==================== 状态 ====================
const scenarios = ref<ScenarioPreset[]>([]);
const activeId = ref('');
const loading = ref(true);
const switching = ref(false);
const saving = ref(false);
const deleting = ref(false);

// 表单
const formVisible = ref(false);
const editingId = ref<string | null>(null);
const form = reactive<ScenarioForm>({
  name: '',
  icon: 'ChatRound',
  description: '',
  system_prompt: '',
  enabled_tools: ['all'],
});
const useAllTools = ref(true);

// 删除
const deleteVisible = ref(false);
const deletingTarget = ref<ScenarioPreset | null>(null);

const fileInputRef = ref<HTMLInputElement | null>(null);

// ==================== 图标与选项 ====================
const iconMap: Record<string, any> = {
  ChatRound,
  Cpu,
  Search,
  EditPen,
  DataLine,
  Files,
  Star,
  Lightning,
};

const iconOptions = [
  { value: 'ChatRound', icon: ChatRound },
  { value: 'Cpu', icon: Cpu },
  { value: 'Search', icon: Search },
  { value: 'EditPen', icon: EditPen },
  { value: 'DataLine', icon: DataLine },
  { value: 'Files', icon: Files },
  { value: 'Star', icon: Star },
  { value: 'Lightning', icon: Lightning },
];

const toolOptions = [
  { value: 'get_current_time', label: '当前时间查询' },
  { value: 'get_weather', label: '天气查询' },
  { value: 'search_web', label: '联网搜索' },
  { value: 'read_webpage', label: '网页内容读取' },
  { value: 'search_knowledge', label: '知识库检索' },
  { value: 'save_user_memory', label: '保存记忆' },
  { value: 'recall_user_memory', label: '回忆记忆' },
  { value: 'list_user_memories', label: '列出记忆' },
  { value: 'delete_user_memory', label: '删除记忆' },
  { value: 'clear_user_memories', label: '清空记忆' },
  { value: 'read_file', label: '读取文件' },
  { value: 'write_file', label: '写入文件' },
  { value: 'list_directory', label: '列出目录' },
  { value: 'search_files', label: '搜索文件' },
  { value: 'execute_python', label: '执行代码' },
];

const iconComponent = (s: ScenarioPreset) => iconMap[s.icon] || ChatRound;

// ==================== 数据加载 ====================
const loadData = async () => {
  loading.value = true;
  try {
    const [list, current] = await Promise.all([getScenarios(), getCurrentScenario()]);
    scenarios.value = list;
    activeId.value = current;
  } catch {
    ElMessage.error('加载场景配置失败');
  } finally {
    loading.value = false;
  }
};

const errMsg = (e: any, fallback: string) => e?.detail || e?.message || fallback;

// ==================== 设为当前 ====================
const setCurrent = async (s: ScenarioPreset) => {
  if (switching.value || s.id === activeId.value) return;
  switching.value = true;
  try {
    const res = await switchScenario(s.id);
    activeId.value = s.id;
    ElMessage.success(res.message);
  } catch (e: any) {
    ElMessage.error(errMsg(e, '切换场景失败'));
  } finally {
    switching.value = false;
  }
};

// ==================== 显示开关 ====================
const toggleDisplay = async (s: ScenarioPreset, val: boolean) => {
  const prev = s.display !== false;
  s.display = val;
  try {
    const res = await updateScenarioDisplay(s.id, val);
    ElMessage.success(res.message);
  } catch (e: any) {
    s.display = prev;
    ElMessage.error(errMsg(e, '更新显示状态失败'));
  }
};

// ==================== 新建 / 编辑 ====================
const resetForm = () => {
  editingId.value = null;
  form.name = '';
  form.icon = 'ChatRound';
  form.description = '';
  form.system_prompt = '';
  form.enabled_tools = ['all'];
  useAllTools.value = true;
};

const openCreate = () => {
  resetForm();
  formVisible.value = true;
};

const openEdit = (s: ScenarioPreset) => {
  editingId.value = s.id;
  form.name = s.name;
  form.icon = s.icon || 'ChatRound';
  form.description = s.description || '';
  form.system_prompt = s.system_prompt || '';
  const tools = s.enabled_tools || [];
  useAllTools.value = tools.length === 1 && tools[0] === 'all';
  form.enabled_tools = useAllTools.value ? ['all'] : [...tools];
  formVisible.value = true;
};

const saveForm = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入场景名称');
    return;
  }
  const payload: ScenarioForm = {
    name: form.name.trim(),
    icon: form.icon,
    description: form.description.trim(),
    system_prompt: form.system_prompt,
    enabled_tools: useAllTools.value ? ['all'] : (form.enabled_tools.length ? [...form.enabled_tools] : ['all']),
  };
  saving.value = true;
  try {
    if (editingId.value) {
      await updateScenario(editingId.value, payload);
      ElMessage.success('场景已更新');
    } else {
      await createScenario(payload);
      ElMessage.success('场景已创建');
    }
    formVisible.value = false;
    loadData();
  } catch (e: any) {
    ElMessage.error(errMsg(e, editingId.value ? '更新场景失败' : '创建场景失败'));
  } finally {
    saving.value = false;
  }
};

// ==================== 复制 ====================
const duplicate = async (s: ScenarioPreset) => {
  try {
    await duplicateScenario(s.id);
    ElMessage.success('复制成功');
  } catch (e: any) {
    ElMessage.error(errMsg(e, '复制场景失败'));
  } finally {
    loadData();
  }
};

// ==================== 删除 ====================
const confirmDelete = (s: ScenarioPreset) => {
  deletingTarget.value = s;
  deleteVisible.value = true;
};

const confirmDeleteAction = async () => {
  if (!deletingTarget.value) return;
  deleting.value = true;
  try {
    const res = await deleteScenario(deletingTarget.value.id);
    ElMessage.success(res.message);
    if (activeId.value === deletingTarget.value.id) {
      activeId.value = 'default';
    }
    deleteVisible.value = false;
    loadData();
  } catch (e: any) {
    ElMessage.error(errMsg(e, '删除场景失败'));
  } finally {
    deleting.value = false;
  }
};

// ==================== 导出 ====================
const doExport = async (s: ScenarioPreset) => {
  try {
    const data = await exportScenario(s.id);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${s.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
    ElMessage.success('导出成功');
  } catch (e: any) {
    ElMessage.error(errMsg(e, '导出失败'));
  }
};

// ==================== 导入 ====================
const triggerImport = () => {
  fileInputRef.value?.click();
};

const handleImportFile = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    const text = await file.text();
    const json = JSON.parse(text) as ScenarioPreset;
    if (!json.name) {
      ElMessage.error('导入文件格式不正确：缺少场景名称');
      return;
    }
    if (json.is_system) {
      ElMessage.error('系统内置场景不可导入');
      return;
    }
    const created = await importScenario(json);
    ElMessage.success(`导入成功：${created.name}`);
    loadData();
  } catch (e: any) {
    ElMessage.error(errMsg(e, '导入场景失败'));
  } finally {
    input.value = '';
  }
};

onMounted(loadData);
</script>

<style scoped>
.scenario-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.manager-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.manager-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.manager-actions {
  display: flex;
  gap: 8px;
}

.manager-tip {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.manager-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-tertiary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.manager-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ========== 卡片网格（响应式） ========== */
.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  overflow-y: auto;
  padding-bottom: 8px;
}

.scenario-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: all 180ms ease;
  position: relative;
}

.scenario-card:hover {
  border-color: var(--primary-500);
  box-shadow: var(--shadow-sm);
}

.scenario-card.active {
  border: 2px solid var(--primary-500);
}

.scenario-card.system:hover {
  cursor: default;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-icon-area {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-500);
  background: var(--primary-50);
}

[data-theme='dark'] .card-icon-area {
  background: rgba(59, 130, 246, 0.15);
}

.card-icon {
  font-size: 24px;
}

.badges {
  display: flex;
  gap: 6px;
}

.badge {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
}

.badge-system {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

[data-theme='dark'] .badge-system {
  background: transparent;
}

.badge-custom {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-500);
}

.badge-active {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
}

.card-info {
  flex: 1;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid var(--border-color-light);
}

.display-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ========== 表单 ========== */
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.icon-option {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.icon-option:hover {
  border-color: var(--primary-500);
  color: var(--primary-500);
}

.icon-option.selected {
  border-color: var(--primary-500);
  background: var(--primary-50);
  color: var(--primary-500);
}

.tool-config {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.delete-text {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.hidden-input {
  display: none;
}
</style>