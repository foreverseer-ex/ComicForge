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
      <img 
        v-if="firstExampleImage"
        :src="firstExampleImage"
        :alt="actor.name"
        class="w-full h-full object-cover"
        @error="handleImageError"
      />
      <div v-else class="flex flex-col items-center justify-center">
        <PhotoIcon class="w-12 h-12" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
        <span :class="['text-xs mt-1', isDark ? 'text-gray-500' : 'text-gray-500']">
          {{ exampleCount > 0 ? '点击查看' : '无立绘' }}
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
import { computed } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { PhotoIcon, TagIcon } from '@heroicons/vue/24/outline'

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
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'openDetail', actor: Actor): void
  (e: 'openExamples', actor: Actor): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const exampleCount = computed(() => props.actor.examples?.length || 0)
const tagCount = computed(() => Object.keys(props.actor.tags || {}).length)

const firstExampleImage = computed(() => {
  if (!props.actor.examples || exampleCount.value === 0) return null
  const firstExample = props.actor.examples[0]
  if (!firstExample?.image_path) return null
  
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:7864'
  // 注意：image_path 可能是相对路径，需要根据实际情况处理
  // 如果是相对路径，需要通过 /file/actor-example 端点获取
  // 这里暂时保持原样，因为 image_path 可能已经是完整路径
  if (firstExample.image_path.startsWith('http://') || firstExample.image_path.startsWith('https://')) {
    return firstExample.image_path
  }
  // 如果是相对路径，需要通过actor-example端点
  // 但这里我们不知道example_index，所以暂时返回null
  // 实际上应该通过 /file/actor-example?actor_id=...&example_index=0 获取
  return `${baseURL}/file/actor-example?actor_id=${props.actor.actor_id}&example_index=0`
})

const handleImageError = () => {
  // 图片加载失败时，不显示图片
}

const openDetailDialog = () => {
  emit('openDetail', props.actor)
}

const handleRightClick = () => {
  if (props.onDelete) {
    props.onDelete(props.actor)
  }
}
</script>

