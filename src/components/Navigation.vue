<template>
  <aside 
    :class="[
      'fixed left-0 top-0 h-full w-56 transition-all duration-300 z-30',
      isDark ? 'bg-gray-900 border-r border-gray-700' : 'bg-white border-r border-gray-200'
    ]"
  >
    <!-- Logo 区域 -->
    <div class="flex items-center justify-between h-16 px-4 border-b" 
         :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <h1 :class="['text-lg font-bold', isDark ? 'text-white' : 'text-gray-900']">
        ComicForge
      </h1>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 overflow-y-auto py-4">
      <div class="px-2 space-y-1">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.path"
          :class="[
            'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap',
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
              'w-5 h-5 mr-2 flex-shrink-0',
              isActive(item.path) 
                ? '' 
                : isDark ? 'text-gray-400 group-hover:text-gray-300' : 'text-gray-400 group-hover:text-gray-500'
            ]" 
          />
          <span class="text-sm">{{ item.name }}</span>
        </router-link>
      </div>
    </nav>

    <!-- 主题切换按钮 -->
    <div class="p-3 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
      <button
        @click="toggleTheme"
        :class="[
          'w-full flex items-center justify-center px-3 py-2 rounded-lg transition-colors text-sm',
          isDark
            ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        <component 
          :is="isDark ? SunIcon : MoonIcon" 
          class="w-4 h-4 mr-2" 
        />
        <span class="text-xs">{{ isDark ? '浅色模式' : '夜间模式' }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import type { Component } from 'vue'
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  LightBulbIcon,
  CubeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon
} from '@heroicons/vue/24/outline'
import {
  MoonIcon,
  SunIcon
} from '@heroicons/vue/24/solid'

const route = useRoute()
const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore

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
