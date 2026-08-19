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
      icon: 'Memo',
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
    component: () => import('@/components/layout/SettingsLayout.vue'),
    redirect: '/settings/status',
    meta: {
      title: '设置',
      icon: 'Setting',
    },
    children: [
      {
        path: 'status',
        name: 'settings-status',
        component: () => import('@/components/settings/StatusCards.vue'),
        meta: { title: '服务状态' },
      },
      {
        path: 'models',
        name: 'settings-models',
        component: () => import('@/components/settings/ModelManager.vue'),
        meta: { title: '模型管理' },
      },
      {
        path: 'workspace',
        name: 'settings-workspace',
        component: () => import('@/components/settings/WorkspaceManager.vue'),
        meta: { title: '工作区' },
      },
      {
        path: 'api',
        name: 'settings-api',
        component: () => import('@/components/settings/ApiConfig.vue'),
        meta: { title: 'API 配置' },
      },
      {
        path: 'scenarios',
        name: 'settings-scenarios',
        component: () => import('@/components/settings/ScenarioManager.vue'),
        meta: { title: '场景管理' },
      },
      {
        path: 'about',
        name: 'settings-about',
        component: () => import('@/components/settings/AboutSection.vue'),
        meta: { title: '关于' },
      },
      // 未匹配的子路由统一重定向到服务状态
      {
        path: ':pathMatch(.*)*',
        redirect: '/settings/status',
      },
    ],
  },
];
