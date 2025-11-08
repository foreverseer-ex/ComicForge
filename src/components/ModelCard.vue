<template>
  <div
    :class="[
      'rounded-lg border-2 overflow-hidden cursor-pointer transition-all hover:shadow-lg flex flex-col',
      isDark 
        ? 'bg-gray-800 hover:border-gray-500' 
        : 'bg-white hover:border-gray-400'
    ]"
    :style="{ borderColor: borderColor }"
    @click="openDetail"
    @contextmenu.prevent="showContextMenu"
  >
    <!-- 预览图 -->
    <div 
      :class="[
        'relative w-full h-48 overflow-hidden flex items-center justify-center',
        isDark ? 'bg-gray-900' : 'bg-gray-100'
      ]"
    >
      <!-- 警告图标（如果文件不存在） -->
      <div
        v-if="showWarning"
        class="absolute top-2 right-2 bg-white/80 rounded-full p-1 z-10"
        title="本地文件不存在（仅元数据）"
      >
        <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      
      <!-- 偏好按钮（右上角） -->
      <button
        @click.stop="togglePreference"
        :class="[
          'absolute right-2 bg-white/80 rounded-full p-1.5 z-10 transition-all hover:bg-white hover:scale-110',
          showWarning ? 'top-10' : 'top-2',  // 如果有警告图标，向下移动
          preferenceColorClass
        ]"
        :title="preferenceTitle"
      >
        <HeartIconSolid v-if="model.preference === 'liked'" class="w-5 h-5" />
        <XMarkIcon v-else-if="model.preference === 'disliked'" class="w-5 h-5" />
        <HeartIcon v-else class="w-5 h-5" />
      </button>
      
      <img 
        v-if="previewImageUrl && !privacyMode && !imageLoading"
        :src="previewImageUrl"
        :alt="model.name"
        class="w-full h-full object-cover"
        @error="handleImageError"
      />
      <div 
        v-else-if="imageLoading && !privacyMode"
        class="flex flex-col items-center justify-center"
      >
        <div class="animate-spin rounded-full h-8 w-8 border-b-2" 
             :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
        <span :class="['text-xs mt-2', isDark ? 'text-gray-500' : 'text-gray-500']">
          加载中...
        </span>
      </div>
      <div v-else class="flex flex-col items-center justify-center">
        <svg class="w-16 h-16" :class="isDark ? 'text-gray-600' : 'text-gray-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span :class="['text-xs mt-2', isDark ? 'text-gray-500' : 'text-gray-500']">
          {{ privacyMode ? '隐私模式' : '无预览图' }}
        </span>
      </div>
    </div>

    <!-- 信息区域 -->
    <div class="px-3 pt-2 pb-2 flex flex-col" style="min-height: 60px;">
      <!-- 标题区域（固定高度，内容垂直居中） -->
      <div class="flex-1 flex items-center" style="min-height: 40px;">
        <h3 
          :class="[
            'text-sm font-bold line-clamp-2 w-full',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
          style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;"
          :title="versionName"
        >
          {{ versionName }}
        </h3>
      </div>

      <!-- 基础模型标签（贴底部） -->
      <div
        :class="[
          'px-2 py-1 rounded text-xs font-bold text-center text-white border border-white/30 mt-1'
        ]"
        :style="{ backgroundColor: borderColor }"
      >
        {{ displayBaseModel }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { HeartIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { HeartIcon as HeartIconSolid } from '@heroicons/vue/24/solid'
import { getImageUrl } from '../utils/imageUtils'
import api from '../api'
import { showToast } from '../utils/toast'

interface ModelMeta {
  model_id: number
  version_id: number
  filename: string
  name: string
  version: string
  version_name: string
  type: 'checkpoint' | 'lora' | 'vae'
  ecosystem: 'sd1' | 'sd2' | 'sdxl'
  base_model: string | null
  examples: any[]
  web_page_url: string | null
  preference?: 'liked' | 'neutral' | 'disliked'  // 模型偏好：喜欢、中性、不喜欢
}

interface Props {
  model: ModelMeta
  privacyMode?: boolean
  showWarning?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  privacyMode: false,
  showWarning: false
})

const emit = defineEmits<{
  (e: 'openDetail', model: ModelMeta): void
  (e: 'contextMenu', event: MouseEvent, model: ModelMeta): void
  (e: 'preferenceChanged', model: ModelMeta): void  // 偏好状态改变事件
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 基础模型颜色映射（与flet应用保持一致）
// 参考: src/api/constants/color.py BaseModelColor
// PINK_400, CYAN_400, PURPLE_300, BLUE_300, ORANGE_400
const baseModelColors: Record<string, string> = {
  // 大小写不敏感匹配
  'Pony': '#F472B6',      // PINK_400
  'pony': '#F472B6',
  'Illustrious': '#22D3EE',  // CYAN_400
  'illustrious': '#22D3EE',
  'NoobAI': '#C084FC',   // PURPLE_300
  'noobai': '#C084FC',
  'SDXL 1.0': '#93C5FD', // BLUE_300
  'sdxl 1.0': '#93C5FD',
  'SD 1.5': '#FB923C',   // ORANGE_400
  'sd 1.5': '#FB923C',
  // 其他可能的基础模型（映射到灰色）
  'Standard': '#6B7280',
  'standard': '#6B7280',
  'Flux': '#6B7280',
  'flux': '#6B7280',
  'SD3': '#6B7280',
  'sd3': '#6B7280',
}

const borderColor = computed(() => {
  const baseModel = props.model.base_model || ''
  if (!baseModel) return '#6B7280' // 默认灰色
  
  // 先尝试精确匹配
  if (baseModelColors[baseModel]) {
    return baseModelColors[baseModel]
  }
  
  // 再尝试大小写不敏感匹配
  const lowerBaseModel = baseModel.toLowerCase()
  for (const [key, color] of Object.entries(baseModelColors)) {
    if (key.toLowerCase() === lowerBaseModel) {
      return color
    }
  }
  
  return '#6B7280' // 默认灰色
})

const displayBaseModel = computed(() => {
  return props.model.base_model || '未知'
})

// 计算 version_name（如果后端没有提供）
const versionName = computed(() => {
  if (props.model.version_name) {
    return props.model.version_name
  }
  // 如果后端没有提供 version_name，则从 name 和 version 组合
  if (props.model.name && props.model.version) {
    return `${props.model.name}-${props.model.version}`
  }
  return props.model.name || props.model.version || ''
})

// 图片 URL（使用缓存）
const previewImageUrl = ref<string | null>(null)
const imageLoading = ref(true)

const rawImageUrl = computed(() => {
  if (!props.model.examples || props.model.examples.length === 0) return null
  const firstExample = props.model.examples[0]
  if (!firstExample?.url) return null
  return firstExample.url
})

// 加载图片 URL
const loadImageUrl = async () => {
  if (!rawImageUrl.value || props.privacyMode) {
    imageLoading.value = false
    return
  }

  imageLoading.value = true
  try {
    previewImageUrl.value = await getImageUrl(rawImageUrl.value)
  } catch (error) {
    console.error('加载图片失败:', error)
    previewImageUrl.value = null
  } finally {
    imageLoading.value = false
  }
}

// 监听模型变化，重新加载图片
watch(() => props.model.examples, () => {
  loadImageUrl()
}, { deep: true })

onMounted(() => {
  loadImageUrl()
})

const handleImageError = () => {
  // 图片加载失败处理
  previewImageUrl.value = null
}

const openDetail = () => {
  emit('openDetail', props.model)
}

const showContextMenu = (event: MouseEvent) => {
  emit('contextMenu', event, props.model)
}

// 计算偏好状态的颜色类
const preferenceColorClass = computed(() => {
  const pref = props.model.preference || 'neutral'
  if (pref === 'liked') return 'text-red-500'
  if (pref === 'disliked') return 'text-gray-600'
  return 'text-gray-400'
})

// 计算偏好状态的提示文本
const preferenceTitle = computed(() => {
  const pref = props.model.preference || 'neutral'
  if (pref === 'liked') return '已设为喜欢（点击切换）'
  if (pref === 'disliked') return '已设为不喜欢（点击切换）'
  return '中性（点击切换）'
})

// 切换偏好状态（循环：neutral -> liked -> disliked -> neutral）
const togglePreference = async () => {
  try {
    const currentPreference = props.model.preference || 'neutral'
    let newPreference: 'liked' | 'neutral' | 'disliked'
    
    // 循环切换：neutral -> liked -> disliked -> neutral
    if (currentPreference === 'neutral') {
      newPreference = 'liked'
    } else if (currentPreference === 'liked') {
      newPreference = 'disliked'
    } else {
      newPreference = 'neutral'
    }
    
    await api.patch(`/model-meta/${props.model.version_id}/preference`, null, {
      params: { preference: newPreference }
    })
    
    // 更新本地模型状态
    props.model.preference = newPreference
    
    // 通知父组件更新
    emit('preferenceChanged', props.model)
    
    const messages = {
      liked: '已设为喜欢',
      disliked: '已设为不喜欢',
      neutral: '已设为中性'
    }
    showToast(messages[newPreference], 'success')
  } catch (error: any) {
    console.error('设置偏好状态失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '设置失败'
    showToast(`❌ ${errorMsg}`, 'error')
  }
}
</script>

