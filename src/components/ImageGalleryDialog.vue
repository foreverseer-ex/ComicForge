<template>
  <Teleport to="body">
    <div
      v-if="visible && images.length > 0"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50"
      @click.self="close"
      @wheel.prevent="handleWheel"
    >
      <!-- 关闭按钮 -->
      <button
        @click="close"
        class="absolute top-4 right-4 z-10 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors"
        title="关闭 (ESC)"
      >
        <XMarkIcon class="w-6 h-6" />
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
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
      >
        <img
          :src="currentImageUrl"
          :alt="`图片 ${currentIndex + 1}`"
          class="max-w-full max-h-full object-contain select-none"
          :style="{
            transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
            transition: isDragging ? 'none' : 'transform 0.3s ease-out'
          }"
          draggable="false"
          @error="handleImageError"
        />
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
import { getImageUrl } from '../utils/imageUtils'

interface Props {
  images: string[]  // 图片 URL 数组
  initialIndex?: number  // 初始显示的图片索引
  visible: boolean  // 是否显示
}

const props = withDefaults(defineProps<Props>(), {
  initialIndex: 0,
  visible: false
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const currentIndex = ref(props.initialIndex)
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const imageUrls = ref<string[]>([])
const loading = ref(true)

// 当前图片 URL
const currentImageUrl = computed(() => {
  if (imageUrls.value.length === 0 || currentIndex.value >= imageUrls.value.length) {
    return ''
  }
  return imageUrls.value[currentIndex.value] || ''
})

// 加载所有图片 URL
const loadImageUrls = async () => {
  if (props.images.length === 0) return
  
  loading.value = true
  try {
    const urls = await Promise.all(
      props.images.map(url => getImageUrl(url))
    )
    imageUrls.value = urls
  } catch (error) {
    console.error('加载图片失败:', error)
    imageUrls.value = []
  } finally {
    loading.value = false
  }
}

// 切换到上一张
const prevImage = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    resetTransform()
  }
}

// 切换到下一张
const nextImage = () => {
  if (currentIndex.value < props.images.length - 1) {
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
  if (scale.value <= 1) return  // 只有在放大时才能拖拽
  
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - translateX.value,
    y: event.clientY - translateY.value
  }
}

// 处理鼠标移动（拖拽中）
const handleMouseMove = (event: MouseEvent) => {
  if (!isDragging.value) return
  
  translateX.value = event.clientX - dragStart.value.x
  translateY.value = event.clientY - dragStart.value.y
}

// 处理鼠标释放（结束拖拽）
const handleMouseUp = () => {
  isDragging.value = false
}

// 处理图片加载错误
const handleImageError = () => {
  console.error('图片加载失败:', currentImageUrl.value)
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

// 关闭
const close = () => {
  resetTransform()
  emit('close')
}

// 监听 visible 变化
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    currentIndex.value = props.initialIndex
    resetTransform()
    loadImageUrls()
  } else {
    // 关闭时重置状态
    resetTransform()
    imageUrls.value = []
  }
})

// 监听 images 变化
watch(() => props.images, () => {
  if (props.visible) {
    loadImageUrls()
  }
}, { immediate: false })

// 监听 initialIndex 变化
watch(() => props.initialIndex, (newIndex) => {
  if (props.visible) {
    currentIndex.value = newIndex
    resetTransform()
  }
})

// 监听 currentIndex 变化，重新加载图片
watch(() => currentIndex.value, () => {
  if (imageUrls.value.length === 0 && props.visible) {
    loadImageUrls()
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  if (props.visible) {
    loadImageUrls()
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

