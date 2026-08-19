// settings.ts - 设置页 API 封装
// 提供 env 通用配置的读写接口及场景切换 API

import type { ScenarioPreset, ScenarioForm } from '@/types/settings';

export interface EnvConfigItem {
  key: string;
  label: string;
  value: string;
  type: string;        // text / password / select / number
  placeholder: string;
  options: string[];
  hint: string;
  saved: boolean;      // 是否已写入 .env 文件
}

export interface EnvConfigResponse {
  items: EnvConfigItem[];
}

export const getEnvConfig = (): Promise<EnvConfigResponse> => {
  return fetch('/api/settings/env-config').then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const updateEnvConfig = (key: string, value: string): Promise<{ success: boolean; message: string }> => {
  return fetch('/api/settings/env-config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, value }),
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

// ==================== 场景切换 API ====================

export interface ScenariosResponse {
  presets: ScenarioPreset[];
}

export interface CurrentScenarioResponse {
  scenario_id: string;
}

export interface SwitchScenarioResponse {
  success: boolean;
  message: string;
}

/** 获取所有预设场景列表 */
export const getScenarios = (): Promise<ScenarioPreset[]> => {
  return fetch('/api/settings/scenarios').then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json().then((data: ScenariosResponse) => data.presets);
  });
};

/** 获取当前激活的场景 ID */
export const getCurrentScenario = (): Promise<string> => {
  return fetch('/api/settings/scenarios/current').then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json().then((data: CurrentScenarioResponse) => data.scenario_id);
  });
};

/** 切换到指定场景 */
export const switchScenario = (scenarioId: string): Promise<{ success: boolean; message: string }> => {
  return fetch('/api/settings/scenarios/switch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id: scenarioId }),
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

// ==================== 场景管理 API ====================

const handleRes = <T>(r: Response): Promise<T> => {
  if (!r.ok) return r.json().then(e => Promise.reject(e));
  return r.json();
};

/** 创建自定义场景 */
export const createScenario = (data: ScenarioForm): Promise<ScenarioPreset> => {
  return fetch('/api/settings/scenarios/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => handleRes<ScenarioPreset>(r));
};

/** 更新自定义场景 */
export const updateScenario = (id: string, data: ScenarioForm): Promise<ScenarioPreset> => {
  return fetch(`/api/settings/scenarios/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => handleRes<ScenarioPreset>(r));
};

/** 删除自定义场景 */
export const deleteScenario = (id: string): Promise<{ success: boolean; message: string }> => {
  return fetch(`/api/settings/scenarios/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  }).then(r => handleRes<{ success: boolean; message: string }>(r));
};

/** 复制自定义场景 */
export const duplicateScenario = (id: string): Promise<ScenarioPreset> => {
  return fetch(`/api/settings/scenarios/${encodeURIComponent(id)}/duplicate`, {
    method: 'POST',
  }).then(r => handleRes<ScenarioPreset>(r));
};

/** 更新场景显示状态 */
export const updateScenarioDisplay = (id: string, display: boolean): Promise<{ success: boolean; message: string }> => {
  return fetch(`/api/settings/scenarios/${encodeURIComponent(id)}/display`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display }),
  }).then(r => handleRes<{ success: boolean; message: string }>(r));
};

/** 导入场景 */
export const importScenario = (data: ScenarioPreset): Promise<ScenarioPreset> => {
  return fetch('/api/settings/scenarios/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => handleRes<ScenarioPreset>(r));
};

/** 导出场景 JSON 文本 */
export const exportScenario = async (id: string): Promise<ScenarioPreset> => {
  const res = await fetch(`/api/settings/scenarios/export/${encodeURIComponent(id)}`);
  if (!res.ok) return res.json().then(e => Promise.reject(e));
  return res.json();
};