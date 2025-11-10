<template>
  <div class="flex flex-wrap gap-3">
    <div
      v-for="(image, index) in images"
      :key="index"
      class="flex flex-col gap-2"
    >
      <!-- 图片卡片 -->
      <div
        class="relative w-56 h-56 rounded-md overflow-hidden border cursor-pointer group"
        :class="[
          isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white',
          isSelected(image.id) ? (isDark ? 'ring-2 ring-blue-500' : 'ring-2 ring-blue-600') : ''
        ]"
        @click="handleImageClick(index)"
      >
        <!-- 加载中占位 -->
        <div
          v-if="!image.imageUrl"
          class="w-full h-full flex items-center justify-center"
        >
          <div
            class="animate-spin rounded-full h-6 w-6 border-b-2"
            :class="isDark ? 'border-blue-500' : 'border-blue-600'"
          ></div>
        </div>

        <!-- 图片 -->
        <img
          v-else
          :src="image.imageUrl"
          :alt="`Image ${image.id}`"
          class="w-full h-full object-cover"
        />
      </div>

      <!-- 选用按钮 -->
      <button
        @click.stop="toggleImport(image.id)"
        class="w-56 px-4 py-2 rounded-md flex items-center justify-center gap-2 transition-colors font-medium text-sm"
        :class="
          isSelected(image.id)
            ? isDark
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-green-500 hover:bg-green-600 text-white'
            : isDark
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-blue-500 hover:bg-blue-600 text-white'
        "
      >
        <span v-if="isSelected(image.id)">✓ 已选用</span>
        <span v-else>选用</span>
      </button>
    </div>
  </div>

  <!-- 使用通用大图组件 -->
  <ImageGalleryDialog
    :images="imageUrls"
    :initial-index="previewIndex"
    :visible="showGallery"
    @close="closePreview"
  />
</template>

<script setup lang="ts">
import { ref, watch, inject, computed } from 'vue'
import ImageGalleryDialog from './ImageGalleryDialog.vue'

const isDark = inject('isDark', ref(false))

interface ImageItem {
  id: string // 唯一标识符
  imageUrl?: string // 图片URL，undefined表示加载中
  metadata?: Record<string, any> // 额外元数据（如 actorId, jobId 等）
}

const props = defineProps<{
  images: ImageItem[]
  mode?: 'single' | 'multiple'
  initialSelected?: string[] // 初始选中的 id 列表
}>()

const emit = defineEmits<{
  select: [id: string, metadata?: Record<string, any>]
  unselect: [id: string, metadata?: Record<string, any>]
  selectionChange: [selectedIds: string[]]
}>()


const selectedJobIds = ref<Set<string>>(new Set(props.initialSelected || []))
const showGallery = ref(false)
const previewIndex = ref(0)

// 从 images 中提取图片 URL 列表（不过滤，保持索引一致）
const imageUrls = computed(() => {
  return props.images.map(img => img.imageUrl || '')
})

// 监听 initialSelected 变化
watch(
  () => props.initialSelected,
  (newVal) => {
    if (newVal) {
      selectedJobIds.value = new Set(newVal)
    }
  },
  { immediate: true }
)

const isSelected = (id: string): boolean => {
  return selectedJobIds.value.has(id)
}

const handleImageClick = (index: number) => {
  // 打开大图预览
  previewIndex.value = index
  showGallery.value = true
}

const toggleImport = (id: string) => {
  const wasSelected = selectedJobIds.value.has(id)
  const image = props.images.find(img => img.id === id)
  const metadata = image?.metadata

  if (props.mode === 'single') {
    // 单选模式：清空其他选择
    selectedJobIds.value.clear()
    if (!wasSelected) {
      selectedJobIds.value.add(id)
      emit('select', id, metadata)
    } else {
      emit('unselect', id, metadata)
    }
  } else {
    // 多选模式：切换选中状态
    if (wasSelected) {
      selectedJobIds.value.delete(id)
      emit('unselect', id, metadata)
    } else {
      selectedJobIds.value.add(id)
      emit('select', id, metadata)
    }
  }

  emit('selectionChange', Array.from(selectedJobIds.value))
}

const closePreview = () => {
  showGallery.value = false
}
</script>
