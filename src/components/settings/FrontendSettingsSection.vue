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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { updateImageCacheSize } from '../../utils/imageCache'

const props = defineProps<{
  settings: any
  isDark: boolean
}>()

const emit = defineEmits<{
  update: [updates: any]
}>()

const localImageCacheSize = ref(String(props.settings?.image_cache_size || 100))

// 监听 settings 变化，同步本地状态
watch(() => props.settings, (newSettings) => {
  if (newSettings) {
    localImageCacheSize.value = String(newSettings.image_cache_size || 100)
  }
}, { immediate: true, deep: true })

// 处理图片缓存数量
const handleImageCacheSizeBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 10 && value <= 1000) {
    localImageCacheSize.value = String(value)
    emit('update', { image_cache_size: value })
    // 更新图片缓存大小
    updateImageCacheSize(value)
  } else {
    target.value = localImageCacheSize.value // 恢复原值
  }
}
</script>

