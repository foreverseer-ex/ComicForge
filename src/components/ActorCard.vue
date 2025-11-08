<template>
  <div 
    :class="[
      'rounded-lg border cursor-pointer transition-all hover:shadow-lg',
      isDark 
        ? 'bg-gray-800 border-gray-700 hover:border-gray-600' 
        : 'bg-white border-gray-200 hover:border-gray-300'
    ]"
    :style="{ borderColor: actor.color || '#808080' }"
    @click="openDetailDialog"
    @contextmenu.prevent="handleRightClick"
  >
    <!-- 缩略图区域 -->
    <div 
      :class="[
        'w-full h-32 rounded-t-lg overflow-hidden flex items-center justify-center',
        isDark ? 'bg-gray-900' : 'bg-gray-100'
      ]"
    >
      <!-- 生成中的 loading 状态 -->
      <div 
        v-if="hasGeneratingExample && !privacyMode" 
        class="flex flex-col items-center justify-center"
      >
        <div 
          class="animate-spin rounded-full h-8 w-8 border-b-2"
          :class="isDark ? 'border-blue-400' : 'border-blue-600'"
        ></div>
        <span :class="['text-xs mt-2', isDark ? 'text-gray-400' : 'text-gray-500']">
          生成中...
        </span>
      </div>
      <!-- 有图片时显示图片 -->
      <img 
        v-else-if="firstExampleImage && !privacyMode"
        :src="firstExampleImageWithRetry"
        :alt="actor.name"
        class="w-full h-full object-cover"
        @error="handleImageError"
        @load="handleImageLoad"
      />
      <!-- 无图片时的空状态 -->
      <div v-else class="flex flex-col items-center justify-center">
        <PhotoIcon class="w-12 h-12" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
        <span :class="['text-xs mt-1', isDark ? 'text-gray-500' : 'text-gray-500']">
          {{ privacyMode ? '隐私模式' : (exampleCount > 0 ? '点击查看' : '无立绘') }}
        </span>
      </div>
    </div>

    <!-- 信息区域 -->
    <div class="p-4 space-y-2">
      <!-- 名称和描述 -->
      <div>
        <h3 
          :class="[
            'text-lg font-semibold mb-1',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          {{ actor.name }}
        </h3>
        <p 
          :class="[
            'text-sm line-clamp-2',
            isDark ? 'text-gray-400' : 'text-gray-600'
          ]"
        >
          {{ actor.desc || '无描述' }}
        </p>
      </div>

      <!-- 分隔线 -->
      <div :class="['border-t', isDark ? 'border-gray-700' : 'border-gray-200']"></div>

      <!-- 统计信息 -->
      <div class="flex items-center gap-4 text-xs">
        <div class="flex items-center gap-1">
          <PhotoIcon class="w-4 h-4" :class="isDark ? 'text-blue-400' : 'text-blue-600'" />
          <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">
            {{ exampleCount }} 张立绘
          </span>
        </div>
        <div class="flex items-center gap-1">
          <TagIcon class="w-4 h-4" :class="isDark ? 'text-green-400' : 'text-green-600'" />
          <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">
            {{ tagCount }} 个标签
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { PhotoIcon, TagIcon } from '@heroicons/vue/24/outline'
import { getApiBaseURL } from '../utils/apiConfig'

interface Actor {
  actor_id: string
  project_id: string
  name: string
  desc: string
  color: string
  tags: Record<string, string>
  examples: any[]
}

interface Props {
  actor: Actor
  onDelete?: (actor: Actor) => void
  privacyMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  privacyMode: false
})

const emit = defineEmits<{
  (e: 'openDetail', actor: Actor): void
  (e: 'openExamples', actor: Actor): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const exampleCount = computed(() => props.actor.examples?.length || 0)
const tagCount = computed(() => Object.keys(props.actor.tags || {}).length)

// 检查是否有正在生成的立绘（image_path 为 null）
const hasGeneratingExample = computed(() => {
  if (!props.actor.examples || exampleCount.value === 0) return false
  return props.actor.examples.some((ex: any) => !ex.image_path)
})

const firstExampleImage = computed(() => {
  if (!props.actor.examples || exampleCount.value === 0) return null
  const firstExample = props.actor.examples[0]
  if (!firstExample?.image_path) return null  // image_path 为 None 时返回 null（不显示图片）
  
  const baseURL = getApiBaseURL()
  // 注意：image_path 可能是相对路径，需要根据实际情况处理
  // 如果是相对路径，需要通过 /file/actor-example 端点获取
  // 这里暂时保持原样，因为 image_path 可能已经是完整路径
  if (firstExample.image_path.startsWith('http://') || firstExample.image_path.startsWith('https://')) {
    return firstExample.image_path
  }
  // 如果是相对路径，需要通过actor-example端点
  // 但这里我们不知道example_index，所以暂时返回null
  // 实际上应该通过 /file/actor-example?actor_id=...&example_index=0 获取
  // 使用 image_path 作为缓存破坏参数，确保不同图片使用不同的 URL
  return `${baseURL}/file/actor-example?actor_id=${props.actor.actor_id}&example_index=0&path=${encodeURIComponent(firstExample.image_path)}`
})

// 图片重试相关状态
const imageRetryCount = ref(0)
const imageLoadKey = ref(0) // 用于强制重新加载图片
const imageTimestamp = ref(Date.now()) // 初始时间戳

// 带重试的图片URL
const firstExampleImageWithRetry = computed(() => {
  if (!firstExampleImage.value) return null
  // 添加时间戳和重试次数作为查询参数，避免浏览器缓存
  const separator = firstExampleImage.value.includes('?') ? '&' : '?'
  return `${firstExampleImage.value}${separator}_t=${imageTimestamp.value}&_retry=${imageRetryCount.value}&_key=${imageLoadKey.value}`
})

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 如果重试次数小于3，尝试重新加载
  if (imageRetryCount.value < 3) {
    imageRetryCount.value++
    imageLoadKey.value++
    imageTimestamp.value = Date.now() // 更新时间戳，强制重新加载
    // 强制重新加载图片
    setTimeout(() => {
      if (img && firstExampleImage.value) {
        img.src = firstExampleImageWithRetry.value || ''
      }
    }, 500) // 延迟500ms后重试
  } else {
    // 重试3次后仍然失败，隐藏图片
    console.error('图片加载失败，已重试3次:', firstExampleImage.value)
  }
}

const handleImageLoad = () => {
  // 图片加载成功，重置重试计数
  imageRetryCount.value = 0
  imageLoadKey.value = 0
}

// 监听 actor.examples 的变化，当 image_path 从 null 变为有值时，强制刷新图片
watch(
  () => props.actor.examples,
  (newExamples, oldExamples) => {
    // 检查是否有 example 的 image_path 从 null 变为有值
    if (newExamples && oldExamples) {
      const hadNullImage = oldExamples.some((ex: any) => !ex.image_path)
      const hasImageNow = newExamples.some((ex: any) => ex.image_path)
      
      // 如果之前有 null 的 image_path，现在有了，强制刷新图片
      if (hadNullImage && hasImageNow) {
        imageTimestamp.value = Date.now()
        imageLoadKey.value++
        imageRetryCount.value = 0
      }
    }
  },
  { deep: true }
)

const openDetailDialog = () => {
  emit('openDetail', props.actor)
}

const handleRightClick = () => {
  if (props.onDelete) {
    props.onDelete(props.actor)
  }
}
</script>

