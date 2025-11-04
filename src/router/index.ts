import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '项目管理' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { title: 'AI 对话' }
  },
  {
    path: '/actor',
    name: 'Actor',
    component: () => import('../views/ActorView.vue'),
    meta: { title: '角色管理' }
  },
  {
    path: '/memory',
    name: 'Memory',
    component: () => import('../views/MemoryView.vue'),
    meta: { title: '记忆管理' }
  },
  {
    path: '/model',
    name: 'Model',
    component: () => import('../views/ModelView.vue'),
    meta: { title: '模型管理' }
  },
  {
    path: '/content',
    name: 'Content',
    component: () => import('../views/ContentView.vue'),
    meta: { title: '内容管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/help',
    name: 'Help',
    component: () => import('../views/HelpView.vue'),
    meta: { title: '帮助' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

