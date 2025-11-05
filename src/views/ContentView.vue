<template>
  <div class="space-y-6">
    <!-- 页面标题栏 -->
    <div 
      :class="[
        'flex items-center justify-between gap-4 pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <div class="flex items-center gap-4">
        <DocumentTextIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          内容管理
        </h1>
      </div>
    </div>

    <!-- 内容区域 -->
    <div>
      <!-- 无项目状态 -->
      <div 
        v-if="!selectedProjectId"
        class="h-full flex items-center justify-center py-20"
      >
        <div 
          :class="[
            'text-center rounded-lg border p-8',
            isDark 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          ]"
        >
          <svg 
            class="w-16 h-16 mx-auto mb-4"
            :class="isDark ? 'text-gray-600' : 'text-gray-400'"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            请先创建一个项目
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            在主页创建项目后，才能管理内容
          </p>
        </div>
      </div>

      <!-- 加载状态 -->
      <div 
        v-else-if="loading"
        class="flex justify-center items-center py-12"
      >
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" 
               :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
            加载中...
          </p>
        </div>
      </div>

      <!-- 内容区域 -->
      <div 
        v-else
        class="space-y-6"
      >
        <!-- 章节导航和内容编辑器占位 -->
        <div 
          :class="[
            'rounded-lg border p-6',
            isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          ]"
        >
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
            章节导航和内容编辑器（待实现）
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { selectedProjectId } = storeToRefs(projectStore)

const loading = ref(false)

onMounted(() => {
  // 加载内容的逻辑待实现
})
</script>
