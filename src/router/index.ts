import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
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
    path: '/task',
    name: 'Task',
    component: () => import('../views/TaskView.vue'),
    meta: { title: '任务管理' }
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
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录', public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const isPublic = (to.meta as any)?.public === true
  if (!isPublic && !auth.isAuthenticated) {
    if (to.name !== 'Login') return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  if (to.name === 'Login' && auth.isAuthenticated) {
    return next({ name: 'Home' })
  }
  next()
})

export default router

