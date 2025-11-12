<template>
  <Teleport to="body">
    <div
      v-if="visible && images.length > 0"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50"
      @click.self="close"
      @wheel.prevent="handleWheel"
    >
      <!-- 关闭按钮（始终可点击，即使在 loading 时） -->
      <button
        @click.stop="close"
        class="absolute top-4 right-4 z-50 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors pointer-events-auto"
        title="关闭 (ESC)"
      >
        <XMarkIcon class="w-6 h-6" />
      </button>

      <!-- 下载按钮 -->
      <button
        v-if="currentImageUrl"
        @click.stop="handleDownload"
        class="absolute top-4 right-16 md:right-20 z-50 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors pointer-events-auto"
        title="下载图片"
      >
        <ArrowDownTrayIcon class="w-5 h-5 md:w-6 md:h-6" />
      </button>

      <!-- 生成参数按钮 -->
      <button
        v-if="currentImageUrl && jobIds && jobIds.length > currentIndex"
        @click.stop="handleShowParams"
        class="absolute top-4 right-28 md:right-36 z-50 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors pointer-events-auto"
        title="查看生成参数"
      >
        <Cog6ToothIcon class="w-5 h-5 md:w-6 md:h-6" />
      </button>

      <!-- 左右切换按钮 -->
      <div class="absolute inset-0 pointer-events-none z-10">
        <!-- 左侧按钮（上一张） -->
        <button
          v-if="currentIndex > 0"
          @click="prevImage"
          class="absolute left-4 top-1/2 transform -translate-y-1/2 pointer-events-auto p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors"
          title="上一张 (←)"
        >
          <ChevronLeftIcon class="w-8 h-8" />
        </button>
        <!-- 右侧按钮（下一张） -->
        <button
          v-if="currentIndex < images.length - 1"
          @click="nextImage"
          class="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-auto p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors"
          title="下一张 (→)"
        >
          <ChevronRightIcon class="w-8 h-8" />
        </button>
      </div>

      <!-- 图片容器 -->
      <div
        class="relative w-full h-full flex items-center justify-center overflow-hidden"
        @mousedown="handleMouseDown"
      >
        <!-- 图片（隐私模式时隐藏） -->
        <img
          v-if="currentImageUrl && !loading && !privacyMode"
          v-show="!imageLoading"
          ref="imageElement"
          :src="currentImageUrl"
          :alt="`图片 ${currentIndex + 1}`"
          class="max-w-full max-h-full object-contain select-none"
          :style="{
            transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
            transition: isDragging ? 'none' : 'transform 0.3s ease-out'
          }"
          draggable="false"
          @load="handleImageLoad"
          @error="handleImageError"
        />
        <!-- 隐私模式占位符 -->
        <div
          v-if="privacyMode && !loading"
          class="flex flex-col items-center justify-center"
        >
          <PhotoIcon class="w-24 h-24 mb-4 text-white opacity-50" />
          <span class="text-white text-lg opacity-75">隐私模式</span>
        </div>
        <!-- Loading 状态 -->
        <div
          v-if="loading || imageLoading"
          class="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none"
        >
          <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-white"></div>
          <span class="text-white text-sm mt-4">加载中...</span>
        </div>
      </div>

      <!-- 图片索引指示器 -->
      <div
        v-if="images.length > 1"
        class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10 px-4 py-2 rounded-full bg-black bg-opacity-50 text-white text-sm"
      >
        {{ currentIndex + 1 }} / {{ images.length }}
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, ArrowDownTrayIcon, PhotoIcon, Cog6ToothIcon } from '@heroicons/vue/24/outline'
import { getImageUrl } from '../utils/imageUtils'
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'

interface Props {
  images?: string[]  // 图片 URL 数组（可选，用于兼容旧代码）
  initialIndex?: number  // 初始显示的图片索引
  visible: boolean  // 是否显示
  jobIds?: string[]  // 每个图片对应的 job_id 数组（可选）
  versionId?: number  // 模型版本 ID（用于模型示例图片）
  filenames?: string[]  // 每个图片对应的文件名数组（用于模型示例图片）
}

const props = withDefaults(defineProps<Props>(), {
  images: undefined,
  initialIndex: 0,
  visible: false,
  jobIds: undefined,
  versionId: undefined,
  filenames: undefined
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'show-params', jobId: string): void  // 显示生成参数对话框
}>()

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

const currentIndex = ref(props.initialIndex)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const imageUrls = ref<string[]>([])
const loading = ref(true)
const imageLoading = ref(true) // 图片实际加载状态
const imageElement = ref<HTMLImageElement | null>(null)
const lastLoadedKey = ref<string>('') // 记录上次加载的图片列表 key，用于避免重复加载

// 当前图片 URL
const currentImageUrl = computed(() => {
  if (imageUrls.value.length === 0 || currentIndex.value >= imageUrls.value.length) {
    return ''
  }
  return imageUrls.value[currentIndex.value] || ''
})

// 图片数组（用于模板）
const images = computed(() => imageUrls.value)

// 加载所有图片 URL（使用缓存）
const loadImageUrls = async () => {
  // 优先使用 versionId + filenames 方式（模型示例图片）
  if (props.versionId && props.filenames && props.filenames.length > 0) {
    // 检查是否已经加载过相同的图片列表
    const currentImagesKey = `model:${props.versionId}:${props.filenames.join('|')}`
    if (lastLoadedKey.value === currentImagesKey && imageUrls.value.length > 0) {
      // 相同的图片列表，且已有缓存，直接使用
      loading.value = false
      return
    }
    
    loading.value = true
    // getImageUrl 已经处理了所有错误（包括 404），不会抛出错误，直接返回 null 表示图片不存在
    // 并行加载所有图片 URL（使用 version_id + filename）
    const urls = await Promise.all(
      props.filenames.map(filename => getImageUrl(props.versionId!, filename))
    )
    imageUrls.value = urls.filter((url): url is string => url !== null)
    lastLoadedKey.value = currentImagesKey
    loading.value = false
    return
  }
  
  // 兼容旧代码：使用 images 数组（如果有）
  if (props.images && props.images.length > 0) {
    // 检查是否已经加载过相同的图片列表
    const currentImagesKey = props.images.join('|')
    if (lastLoadedKey.value === currentImagesKey && imageUrls.value.length > 0) {
      // 相同的图片列表，且已有缓存，直接使用
      loading.value = false
      return
    }
    
    loading.value = true
    // 直接使用 images 数组（用于兼容旧代码，如角色立绘）
    imageUrls.value = props.images.filter((url): url is string => url !== null && url !== undefined)
    lastLoadedKey.value = currentImagesKey
    loading.value = false
    return
  }
  
  // 如果没有提供任何图片源，清空
  imageUrls.value = []
  loading.value = false
}

// 切换到上一张
const prevImage = () => {
  if (currentIndex.value > 0) {
    imageLoading.value = true
    currentIndex.value--
    resetTransform()
  }
}

// 切换到下一张
const nextImage = () => {
  if (currentIndex.value < imageUrls.value.length - 1) {
    imageLoading.value = true
    currentIndex.value++
    resetTransform()
  }
}

// 重置变换
const resetTransform = () => {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
}

// 处理滚轮缩放
const handleWheel = (event: WheelEvent) => {
  event.preventDefault()
  
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  const newScale = Math.max(0.5, Math.min(5, scale.value + delta))
  
  // 计算缩放中心点（鼠标位置）
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const centerX = event.clientX - rect.left - rect.width / 2
  const centerY = event.clientY - rect.top - rect.height / 2
  
  // 调整平移，使缩放围绕鼠标位置
  const scaleDiff = newScale - scale.value
  translateX.value -= centerX * scaleDiff * 0.5
  translateY.value -= centerY * scaleDiff * 0.5
  
  scale.value = newScale
}

// 处理鼠标按下（开始拖拽）
const handleMouseDown = (event: MouseEvent) => {
  // 允许在任何缩放状态下拖拽
  if (event.button !== 0) return  // 只响应左键
  
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - translateX.value,
    y: event.clientY - translateY.value
  }
  event.preventDefault()
  
  // 在文档级别添加事件监听器，以便在鼠标移出容器时也能响应
  document.addEventListener('mousemove', handleDocumentMouseMove)
  document.addEventListener('mouseup', handleDocumentMouseUp)
}

// 处理文档级别的鼠标移动（拖拽中）
const handleDocumentMouseMove = (event: MouseEvent) => {
  if (!isDragging.value) return
  
  translateX.value = event.clientX - dragStart.value.x
  translateY.value = event.clientY - dragStart.value.y
  event.preventDefault()
}

// 处理文档级别的鼠标释放（结束拖拽）
const handleDocumentMouseUp = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDocumentMouseMove)
  document.removeEventListener('mouseup', handleDocumentMouseUp)
}

// 处理图片加载完成
const handleImageLoad = () => {
  imageLoading.value = false
}

// 处理图片加载错误
const handleImageError = () => {
  console.error('图片加载失败:', currentImageUrl.value)
  imageLoading.value = false
}

// 下载当前图片
const handleDownload = async () => {
  if (!currentImageUrl.value) return
  
  try {
    // 使用 fetch 下载图片
    const response = await fetch(currentImageUrl.value)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    
    // 从 jobIds 中获取 job_id，或者从 URL 中提取，如果都没有则使用默认名称
    let jobId: string | undefined = 'image'
    if (props.jobIds && props.jobIds.length > currentIndex.value) {
      // 优先使用 jobIds 中的 job_id
      jobId = props.jobIds[currentIndex.value]
    } else {
      // 尝试从 URL 中提取 job_id（仅当 URL 是有效的 HTTP URL 时）
      try {
        // 检查是否是 blob URL，blob URL 不能直接用 new URL() 构造
        if (currentImageUrl.value.startsWith('blob:')) {
          // blob URL，无法解析，使用默认名称或索引
          jobId = `image_${currentIndex.value + 1}`
        } else {
          // 尝试解析为 URL
          const url = new URL(currentImageUrl.value)
          jobId = url.searchParams.get('job_id') || `image_${currentIndex.value + 1}`
        }
      } catch (urlError) {
        // URL 解析失败，使用索引作为后备
        jobId = `image_${currentIndex.value + 1}`
      }
    }
    
    link.download = `job_${jobId}.png`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  } catch (error) {
    console.error('下载图片失败:', error)
    alert('下载失败，请重试')
  }
}

// 显示生成参数对话框
const handleShowParams = () => {
  if (props.jobIds && props.jobIds.length > currentIndex.value) {
    const jobId: string | undefined = props.jobIds[currentIndex.value]
    if (jobId) {
      emit('show-params', jobId)
    }
  }
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  if (!props.visible) return
  
  switch (event.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      prevImage()
      break
    case 'ArrowRight':
      nextImage()
      break
    case '+':
    case '=':
      event.preventDefault()
      scale.value = Math.min(5, scale.value + 0.1)
      break
    case '-':
      event.preventDefault()
      scale.value = Math.max(0.5, scale.value - 0.1)
      break
    case '0':
      resetTransform()
      break
  }
}

// 关闭（可打断加载）
const close = () => {
  resetTransform()
  // 清理事件监听器
  if (isDragging.value) {
    isDragging.value = false
    document.removeEventListener('mousemove', handleDocumentMouseMove)
    document.removeEventListener('mouseup', handleDocumentMouseUp)
  }
  // 中断加载状态
  loading.value = false
  imageLoading.value = false
  emit('close')
}

// 监听 visible 变化
watch(() => props.visible, async (newVisible) => {
  if (newVisible) {
    currentIndex.value = props.initialIndex
    resetTransform()
    imageLoading.value = true
    await loadImageUrls()
    // 检查图片是否已在浏览器缓存中（已加载过的图片通常会立即完成）
    await nextTick()
    if (imageElement.value?.complete && imageElement.value.naturalWidth > 0) {
      // 图片已在浏览器缓存中，立即显示
      imageLoading.value = false
    }
    // 如果不在缓存中，等待 @load 事件触发
  } else {
    // 关闭时重置状态（但保留 imageUrls 以便下次快速打开）
    resetTransform()
    imageLoading.value = true
    // 不清空 imageUrls，保留缓存以便下次快速打开
  }
})

// 监听 images 变化（兼容旧代码）
watch(() => props.images, () => {
  if (props.visible) {
    loadImageUrls()
  }
}, { immediate: false })

// 监听 versionId 和 filenames 变化（模型示例图片）
watch(() => [props.versionId, props.filenames], () => {
  if (props.visible) {
    loadImageUrls()
  }
}, { immediate: false, deep: true })

// 监听 initialIndex 变化
watch(() => props.initialIndex, (newIndex) => {
  if (props.visible) {
    imageLoading.value = true
    currentIndex.value = newIndex
    resetTransform()
  }
})

// 监听 currentIndex 变化，检查图片是否已在浏览器缓存中
watch(() => currentIndex.value, async () => {
  imageLoading.value = true
  if (imageUrls.value.length === 0 && props.visible) {
    await loadImageUrls()
  }
  // 检查图片是否已在浏览器缓存中（已加载过的图片通常会立即完成）
  await nextTick()
  if (imageElement.value?.complete && imageElement.value.naturalWidth > 0) {
    // 图片已在浏览器缓存中，立即显示
    imageLoading.value = false
  }
  // 如果不在缓存中，等待 @load 事件触发
})

onMounted(async () => {
  window.addEventListener('keydown', handleKeyDown)
  if (props.visible) {
    await loadImageUrls()
    // 检查图片是否已在浏览器缓存中
    await nextTick()
    if (imageElement.value?.complete && imageElement.value.naturalWidth > 0) {
      imageLoading.value = false
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  // 清理鼠标事件监听器
  if (isDragging.value) {
    isDragging.value = false
    document.removeEventListener('mousemove', handleDocumentMouseMove)
    document.removeEventListener('mouseup', handleDocumentMouseUp)
  }
})
</script>

