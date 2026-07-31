// workspace.ts - 工作区文件浏览 API 封装
// 提供目录树浏览和文件内容预览接口

// ====== 类型定义 ======

export interface WorkspaceNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified_at?: string;
}

export interface FileContent {
  content: string;
  path: string;
  size: number;
  encoding: string;
}

// ====== API 函数 ======

export const getWorkspaceTree = (path: string = ''): Promise<WorkspaceNode[]> => {
  const url = `/api/workspace/tree?path=${encodeURIComponent(path)}`;
  return fetch(url).then(r => r.json()).then(data => data.nodes || []);
};

export const getFileContent = (path: string): Promise<FileContent> => {
  const url = `/api/workspace/file?path=${encodeURIComponent(path)}`;
  return fetch(url).then(r => r.json());
};