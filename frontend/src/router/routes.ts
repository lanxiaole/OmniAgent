// routes.ts - 路由配置表
// 集中管理 OmniAgent 控制台的所有页面路由
import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
    meta: {
      title: '对话',
      icon: 'ChatRound',
    },
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('@/views/KnowledgeView.vue'),
    meta: {
      title: '知识库',
      icon: 'Collection',
    },
  },
  {
    path: '/memory',
    name: 'memory',
    component: () => import('@/views/MemoryView.vue'),
    meta: {
      title: '记忆',
      icon: 'Brain',
    },
  },
  {
    path: '/files',
    name: 'files',
    component: () => import('@/views/FileBrowserView.vue'),
    meta: {
      title: '文件',
      icon: 'Folder',
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: {
      title: '设置',
      icon: 'Setting',
    },
  },
];
