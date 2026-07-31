// memory.ts - 用户记忆 API 封装
// 提供用户长期记忆的增删改查接口

// ====== 类型定义 ======

export interface MemoryItem {
  id: string;
  content: string;
  metadata: {
    created_at?: string;  // ISO 格式
    [key: string]: unknown;
  };
}

export interface MemoryListResponse {
  memories: MemoryItem[];
  total: number;
}

// ====== 工具函数 ======

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// ====== API 函数 ======

/** 获取所有用户记忆 */
export const getMemoryList = async (): Promise<MemoryItem[]> => {
  const data = await request<MemoryListResponse>('/api/memory/list');
  return data.memories || [];
};

/** 添加一条用户记忆 */
export const addMemory = (content: string): Promise<{ success: boolean; id?: string; message: string }> => {
  return request<{ success: boolean; id?: string; message: string }>('/api/memory/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
};

/** 搜索用户记忆 */
export const searchMemory = (query: string, top_k: number = 3): Promise<MemoryItem[]> => {
  return request<{ results: MemoryItem[] }>('/api/memory/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k }),
  }).then(data => data.results || []);
};

/** 更新指定记忆 */
export const updateMemory = (id: string, content: string): Promise<{ success: boolean; message: string }> => {
  return request<{ success: boolean; message: string }>(`/api/memory/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
};

/** 删除单条记忆 */
export const deleteMemory = (id: string): Promise<{ success: boolean; message: string }> => {
  return request<{ success: boolean; message: string }>(`/api/memory/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
};

/** 清空所有记忆 */
export const clearAllMemories = (): Promise<{ success: boolean; message: string }> => {
  return request<{ success: boolean; message: string }>('/api/memory/all', {
    method: 'DELETE',
  });
};