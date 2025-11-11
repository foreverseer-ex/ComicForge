<template>
  <aside 
    :class="[
      'fixed left-0 top-0 h-full transition-all duration-300 z-30',
      isCollapsed ? 'w-16' : 'w-48',
      isDark ? 'bg-gray-900 border-r border-gray-700' : 'bg-white border-r border-gray-200'
    ]"
  >
    <!-- Logo 区域 -->
    <div class="flex items-center justify-between h-16 border-b" 
         :class="[
           isCollapsed ? 'px-2' : 'px-4',
           isDark ? 'border-gray-700' : 'border-gray-200'
         ]">
      <h1 v-if="!isCollapsed" :class="['text-lg font-bold', isDark ? 'text-white' : 'text-gray-900']">
        ComicForge
      </h1>
      <button
        @click="toggleCollapseFn"
        :class="[
          'p-1.5 rounded-lg transition-colors',
          isDark ? 'hover:bg-gray-800 text-gray-400 hover:text-white' : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
        ]"
        :title="isCollapsed ? '展开导航栏' : '折叠导航栏'"
      >
        <component :is="isCollapsed ? ChevronRightIcon : ChevronLeftIcon" class="w-5 h-5" />
      </button>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 overflow-y-auto py-4" :class="isCollapsed ? 'overflow-x-hidden' : ''">
      <div :class="isCollapsed ? 'px-1 space-y-1' : 'px-2 space-y-1'">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.path"
          :class="[
            'group relative flex items-center py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap',
            isCollapsed ? 'justify-center px-2' : 'px-3',
            !isConnected ? 'opacity-50 cursor-not-allowed pointer-events-none' : '',
            isActive(item.path)
              ? isDark 
                ? 'bg-blue-600 text-white' 
                : 'bg-blue-50 text-blue-700'
              : isDark
                ? 'text-gray-300 hover:bg-gray-800 hover:text-white'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <component 
            :is="item.icon" 
            :class="[
              'w-5 h-5 flex-shrink-0',
              isCollapsed ? '' : 'mr-2',
              isActive(item.path) 
                ? '' 
                : isDark ? 'text-gray-400 group-hover:text-gray-300' : 'text-gray-400 group-hover:text-gray-500'
            ]" 
          />
          <span v-if="!isCollapsed" class="text-sm">{{ item.name }}</span>
          <span v-if="isCollapsed" class="absolute left-full ml-2 px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 whitespace-nowrap"
                :class="isDark ? 'bg-gray-800 text-white' : 'bg-white text-gray-900 shadow-lg'">
            {{ item.name }}
          </span>
        </router-link>
      </div>
    </nav>

    <!-- 底部操作区域 -->
    <div class="border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <!-- 主题切换按钮 -->
      <div :class="isCollapsed ? 'px-2 pt-3 pb-1' : 'px-3 pt-3 pb-1'">
        <button
          @click="toggleTheme"
          :class="[
            'w-full flex items-center justify-center py-2 rounded-lg transition-colors text-sm',
            isCollapsed ? 'px-2' : 'px-3',
            isDark
              ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          <component 
            :is="isDark ? SunIcon : MoonIcon" 
            :class="['w-4 h-4', isCollapsed ? '' : 'mr-2']" 
          />
          <span v-if="!isCollapsed" class="text-xs">{{ isDark ? '浅色模式' : '夜间模式' }}</span>
        </button>
      </div>
      
      <!-- 隐私模式按钮 -->
      <div :class="isCollapsed ? 'px-2 pt-1 pb-1' : 'px-3 pt-1 pb-1'">
        <button
          @click="togglePrivacyMode"
          :class="[
            'w-full flex items-center justify-center py-2 rounded-lg transition-colors text-sm',
            isCollapsed ? 'px-2' : 'px-3',
            privacyMode
              ? isDark
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
              : isDark
                ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
          :title="privacyMode ? '隐私模式：已启用（点击关闭）' : '隐私模式：已关闭（点击启用）'"
        >
          <component 
            :is="privacyMode ? EyeSlashIcon : EyeIcon" 
            :class="['w-4 h-4', isCollapsed ? '' : 'mr-2']" 
          />
          <span v-if="!isCollapsed" class="text-xs">隐私模式</span>
        </button>
      </div>
      
      <!-- 已登录用户信息 -->
      <div :class="isCollapsed ? 'px-2 pt-1 pb-3' : 'px-3 pt-1 pb-3'">
        <button
          v-if="authStore.user"
          @click="copyToken"
          :class="[
            'w-full flex items-center py-2 rounded-lg transition-colors text-xs cursor-pointer',
            isCollapsed ? 'px-1 justify-center' : 'px-2 gap-2',
            isDark
              ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
          :title="isCollapsed ? authStore.user.username : '点击复制 Token'"
        >
          <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0"
               :class="isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'">
            {{ authStore.user.username?.[0]?.toUpperCase() || 'U' }}
          </div>
          <div v-if="!isCollapsed" class="flex-1 text-left truncate">
            <div class="font-medium">{{ authStore.user.username }}</div>
            <div class="text-[10px] opacity-70">{{ copied ? '已复制!' : '点击复制 Token' }}</div>
          </div>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '../stores/theme'
import { useConnectionStore } from '../stores/connection'
import { useNavigationStore } from '../stores/navigation'
import { useAuthStore } from '../stores/auth'
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'
import type { Component } from 'vue'
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  LightBulbIcon,
  CubeIcon,
  DocumentTextIcon,
  PaintBrushIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon
} from '@heroicons/vue/24/outline'
import {
  MoonIcon,
  SunIcon
} from '@heroicons/vue/24/solid'
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore

const connectionStore = useConnectionStore()
const { isConnected } = storeToRefs(connectionStore)
const { startChecking, stopChecking } = connectionStore

const navigationStore = useNavigationStore()
const { isCollapsed } = storeToRefs(navigationStore)
const { toggleCollapse: toggleCollapseFn } = navigationStore

const authStore = useAuthStore()
const copied = ref(false)

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)
const { togglePrivacyMode } = privacyStore

// 复制 token 到剪贴板（用于 FastAPI 后端调试）
const copyToken = async () => {
  if (authStore.accessToken) {
    try {
      await navigator.clipboard.writeText(authStore.accessToken)
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } catch (error) {
      console.error('复制失败:', error)
    }
  }
}

onMounted(() => {
  startChecking()
})

onUnmounted(() => {
  stopChecking()
})

interface NavigationItem {
  name: string
  path: string
  icon: Component
}

const navigation: NavigationItem[] = [
  { name: '项目管理', path: '/', icon: HomeIcon },
  { name: 'AI 对话', path: '/chat', icon: ChatBubbleLeftRightIcon },
  { name: '角色管理', path: '/actor', icon: UserGroupIcon },
  { name: '记忆管理', path: '/memory', icon: LightBulbIcon },
  { name: '模型管理', path: '/model', icon: CubeIcon },
  { name: '内容管理', path: '/content', icon: DocumentTextIcon },
  { name: '任务管理', path: '/task', icon: PaintBrushIcon },
  { name: '设置', path: '/settings', icon: Cog6ToothIcon },
  { name: '帮助', path: '/help', icon: QuestionMarkCircleIcon }
]

const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>
