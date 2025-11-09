<template>
  <div 
    :class="[
      'shadow rounded-lg p-6',
      isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    ]"
  >
    <h2 
      :class="[
        'text-xl font-bold mb-4',
        isDark ? 'text-white' : 'text-gray-900'
      ]"
    >
      前端设置
    </h2>

    <div class="space-y-4">
      <!-- 图片缓存数量 -->
      <div class="max-w-[200px]">
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          图片缓存数量
        </label>
        <input
          :value="localImageCacheSize"
          @blur="handleImageCacheSizeBlur"
          @keyup.enter="handleImageCacheSizeBlur"
          type="number"
          min="10"
          max="1000"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
        <p 
          :class="[
            'mt-1 text-xs',
            isDark ? 'text-gray-400' : 'text-gray-500'
          ]"
        >
          范围：10-1000，默认 100
        </p>
      </div>

      <!-- 清空图片缓存按钮 -->
      <div>
        <button
          @click="handleClearImageCache"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            isDark
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-red-500 hover:bg-red-600 text-white'
          ]"
        >
          清空图片缓存
        </button>
        <p 
          :class="[
            'mt-1 text-xs',
            isDark ? 'text-gray-400' : 'text-gray-500'
          ]"
        >
          清空当前内存中的图片缓存
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { updateImageCacheSize, imageCache } from '../../utils/imageCache'
import { showToast } from '../../utils/toast'

defineProps<{
  isDark: boolean
}>()

// 图片缓存数量 - 从 localStorage 读取
const localImageCacheSize = ref('100')

// 初始化图片缓存数量（从 localStorage 读取）
const initImageCacheSize = () => {
  const saved = localStorage.getItem('imageCacheSize')
  if (saved !== null) {
    const value = parseInt(saved)
    if (!isNaN(value) && value >= 10 && value <= 1000) {
      localImageCacheSize.value = String(value)
      updateImageCacheSize(value)
    }
  } else {
    // 使用默认值
    updateImageCacheSize(100)
  }
}

// 监听图片缓存数量变化，保存到 localStorage
watch(localImageCacheSize, (newVal) => {
  const value = parseInt(newVal)
  if (!isNaN(value) && value >= 10 && value <= 1000) {
    localStorage.setItem('imageCacheSize', String(value))
    updateImageCacheSize(value)
  }
})

// 处理图片缓存数量
const handleImageCacheSizeBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 10 && value <= 1000) {
    localImageCacheSize.value = String(value)
    localStorage.setItem('imageCacheSize', String(value))
    updateImageCacheSize(value)
  } else {
    target.value = localImageCacheSize.value // 恢复原值
  }
}

// 清空图片缓存
const handleClearImageCache = () => {
  const cacheSize = imageCache.size
  imageCache.clear()
  showToast(`已清空图片缓存（${cacheSize} 张图片）`, 'success')
}

// 组件挂载时初始化
onMounted(() => {
  initImageCacheSize()
})
</script>

