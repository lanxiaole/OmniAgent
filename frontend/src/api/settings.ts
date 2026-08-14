// settings.ts - 设置页 API 封装
// 提供 env 通用配置的读写接口及场景切换 API

import type { ScenarioPreset } from '@/types/settings';

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