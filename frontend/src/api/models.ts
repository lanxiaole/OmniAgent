// models.ts - 模型管理 API 封装
// 提供模型配置的 CRUD 操作接口

// ====== 类型定义 ======

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model: string;
  is_default: boolean;
}

export interface ModelConfigResponse {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  api_key_masked: string;
  model: string;
  is_default: boolean;
}

export interface ModelListResponse {
  models: ModelConfigResponse[];
  current_id: string | null;
}

export interface ModelTestRequest {
  base_url: string;
  api_key: string;
  model: string;
}

// ====== API 函数 ======

export const getModels = (): Promise<ModelListResponse> => {
  return fetch('/api/models').then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const addModel = (data: Partial<ModelConfig>): Promise<ModelConfigResponse> => {
  return fetch('/api/models', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const updateModel = (id: string, data: Partial<ModelConfig>): Promise<ModelConfigResponse> => {
  return fetch(`/api/models/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const deleteModel = (id: string): Promise<{ success: boolean; message: string }> => {
  return fetch(`/api/models/${id}`, {
    method: 'DELETE',
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const setDefaultModel = (id: string): Promise<{ success: boolean; message: string }> => {
  return fetch(`/api/models/${id}/default`, {
    method: 'POST',
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};

export const testModelConnection = (config: ModelTestRequest): Promise<{ success: boolean; message: string }> => {
  return fetch('/api/models/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(e));
    return r.json();
  });
};