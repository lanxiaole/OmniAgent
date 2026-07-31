// knowledge.ts - 知识库 API 封装
// 提供知识库状态查询、文件管理、重建索引和检索测试等接口

// ====== 类型定义 ======

export interface KnowledgeStatus {
  total_files: number;
  total_chunks: number;
  last_build: string | null;
  hash_changed: boolean;
}

export interface KnowledgeFile {
  name: string;
  size: number;
  modified_at: string;
  is_indexed: boolean;
}

export interface SearchResultItem {
  content: string;
  metadata: {
    source: string;
    line?: number;
    section?: string;
    level?: number;
  };
}

export interface UploadResponse {
  success: boolean;
  message: string;
  filename: string;
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

/** 获取知识库概览状态 */
export const getKnowledgeStatus = (): Promise<KnowledgeStatus> => {
  return request<KnowledgeStatus>('/api/knowledge/status');
};

/** 获取知识库文件列表 */
export const getKnowledgeFiles = async (): Promise<KnowledgeFile[]> => {
  const data = await request<{ files: KnowledgeFile[] }>('/api/knowledge/files');
  return data.files ?? [];
};

/** 删除知识库文件 */
export const deleteKnowledgeFile = (filename: string): Promise<{ success: boolean; message: string }> => {
  return request<{ success: boolean; message: string }>(
    `/api/knowledge/files/${encodeURIComponent(filename)}`,
    { method: 'DELETE' },
  );
};

/** 强制重建向量库索引 */
export const rebuildKnowledge = (): Promise<{ success: boolean; message: string; chunks_added?: number }> => {
  return request<{ success: boolean; message: string; chunks_added?: number }>(
    '/api/knowledge/rebuild',
    { method: 'POST' },
  );
};

/** 检索测试（沙盒） */
export const searchKnowledge = (query: string, top_k: number = 3): Promise<SearchResultItem[]> => {
  return request<{ results: SearchResultItem[] }>('/api/knowledge/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k }),
  }).then(data => data.results ?? []);
};