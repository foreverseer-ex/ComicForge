<template>
  <div class="space-y-6">
    <div 
      :class="[
        'shadow rounded-lg p-6',
        isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
      ]"
    >
      <h2 
        :class="[
          'text-2xl font-bold mb-4',
          isDark ? 'text-white' : 'text-gray-900'
        ]"
      >
        模型管理
      </h2>
      <p 
        :class="[
          isDark ? 'text-gray-300' : 'text-gray-600'
        ]"
      >
        模型管理页面 - 待实现
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)
</script>
