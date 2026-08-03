// settings.ts - 设置页 API 封装
// 提供 env 通用配置的读写接口

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