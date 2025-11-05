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
        <CubeIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          模型管理
        </h1>
      </div>
      
      <div class="flex items-center gap-2">
        <button
          @click="refreshModels"
          :disabled="loading"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
            loading
              ? isDark
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          ]"
        >
          <ArrowPathIcon class="w-5 h-5" :class="loading ? 'animate-spin' : ''" />
          刷新
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div 
      v-if="loading"
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
    <div v-else class="space-y-6">
      <!-- 筛选和操作区域 -->
      <div 
        :class="[
          'rounded-lg border p-4',
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        ]"
      >
        <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
          筛选和操作工具栏（待实现）
        </p>
      </div>

      <!-- 空状态 -->
      <div 
        v-if="models.length === 0"
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
          <CubeIcon 
            class="w-16 h-16 mx-auto mb-4"
            :class="isDark ? 'text-gray-600' : 'text-gray-400'"
          />
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            暂无模型
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            点击"刷新"按钮扫描本地模型，或从 Civitai 导入模型元数据
          </p>
        </div>
      </div>

      <!-- 模型列表 -->
      <div 
        v-else
        class="space-y-4"
      >
        <!-- 模型卡片占位 -->
        <div
          v-for="model in models"
          :key="model.model_id"
          :class="[
            'rounded-lg border p-6 transition-shadow hover:shadow-md',
            isDark 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          ]"
        >
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
            模型卡片 - {{ model.name }}（待实现）
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { CubeIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const loading = ref(false)
const models = ref<any[]>([])

const refreshModels = async () => {
  loading.value = true
  try {
    // 刷新模型的逻辑待实现
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟加载
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 加载模型列表的逻辑待实现
})
</script>
