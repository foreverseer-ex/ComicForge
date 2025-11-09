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
        v-else-if="firstExampleBlobUrl && !privacyMode"
        :src="firstExampleBlobUrl"
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
import api from '../api'

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

// 仅当“第一张 example 正在生成（image_path 为空）”时显示 loading
const hasGeneratingExample = computed(() => {
  if (!props.actor.examples || exampleCount.value === 0) return false
  const first = props.actor.examples[0]
  return !first?.image_path
})

const firstExampleImagePath = computed(() => {
  if (!props.actor.examples || exampleCount.value === 0) return null
  const firstExample = props.actor.examples[0]
  if (!firstExample?.image_path) return null
  return firstExample.image_path as string
})

const firstExampleBlobUrl = ref<string | null>(null)

const buildProtectedUrl = () => {
  if (!firstExampleImagePath.value) return ''
  const baseURL = getApiBaseURL()
  if (firstExampleImagePath.value.startsWith('http://') || firstExampleImagePath.value.startsWith('https://')) {
    return firstExampleImagePath.value
  }
  return `${baseURL}/actor/${props.actor.actor_id}/image?example_index=0&path=${encodeURIComponent(firstExampleImagePath.value)}`
}

const loadFirstBlob = async () => {
  firstExampleBlobUrl.value = null
  const full = buildProtectedUrl()
  if (!full) return
  try {
    const base = getApiBaseURL()
    if (full.startsWith(base) && /\/actor\/.+\/image/.test(full)) {
      const relative = full.replace(base, '')
      const resp = await api.get(relative, { responseType: 'blob' })
      firstExampleBlobUrl.value = URL.createObjectURL(resp as any)
    } else {
      firstExampleBlobUrl.value = full
    }
  } catch (e) {
    console.error('加载缩略图失败:', e)
    firstExampleBlobUrl.value = null
  }
}

// 图片重试相关状态
const imageRetryCount = ref(0)

// 带重试的图片URL
watch(firstExampleImagePath, async () => {
  imageRetryCount.value = 0
  await loadFirstBlob()
}, { immediate: true })

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 如果重试次数小于3，尝试重新加载
  if (imageRetryCount.value < 3) {
    imageRetryCount.value++
    setTimeout(async () => {
      await loadFirstBlob()
      if (img && firstExampleBlobUrl.value) {
        img.src = firstExampleBlobUrl.value
      }
    }, 500)
  } else {
    // 重试3次后仍然失败，隐藏图片
    console.error('图片加载失败，已重试3次:', buildProtectedUrl())
  }
}

const handleImageLoad = () => {
  // 图片加载成功，重置重试计数
  imageRetryCount.value = 0
}

// 监听第一张 example 的变化：仅当首图的 image_path 从空变为有值或路径发生变化时刷新缩略图
watch(
  () => props.actor.examples ? props.actor.examples[0]?.image_path : undefined,
  (newPath, oldPath) => {
    if (newPath && newPath !== oldPath) {
      imageRetryCount.value = 0
      loadFirstBlob()
    }
  }
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

