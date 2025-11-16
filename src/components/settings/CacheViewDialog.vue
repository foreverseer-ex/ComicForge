<template>
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="handleClose"
  >
    <div
      :class="[
        'max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col',
        isDark ? 'bg-gray-800' : 'bg-white'
      ]"
    >
      <!-- 标题栏 -->
      <div
        :class="[
          'flex items-center justify-between p-4 border-b',
          isDark ? 'border-gray-700' : 'border-gray-200'
        ]"
      >
        <h3
          :class="[
            'text-xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          {{ type === 'image' ? '图片缓存' : '文字缓存' }}
          <span
            :class="[
              'ml-2 text-sm font-normal',
              isDark ? 'text-gray-400' : 'text-gray-600'
            ]"
          >
            ({{ cacheSize }} 项)
          </span>
        </h3>
        <div class="flex items-center gap-2">
          <!-- 清空缓存按钮 -->
          <button
            @click="handleClearAll"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors text-sm',
              isDark
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-red-500 hover:bg-red-600 text-white'
            ]"
          >
            清空全部
          </button>
          <button
            @click="handleClose"
            :class="[
              'p-2 rounded-lg transition-colors',
              isDark
                ? 'hover:bg-gray-700 text-gray-400 hover:text-white'
                : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
            ]"
          >
            <XMarkIcon class="w-6 h-6" />
          </button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- 图片缓存网格显示 -->
        <div v-if="type === 'image'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div
            v-for="entry in imageEntries"
            :key="entry.key"
            :class="[
              'rounded-lg overflow-hidden border relative',
              isDark ? 'border-gray-700 bg-gray-700' : 'border-gray-200 bg-gray-50'
            ]"
          >
            <!-- 删除按钮 -->
            <button
              @click="handleDeleteEntry(entry.key)"
              :class="[
                'absolute top-2 right-2 z-10 p-1.5 rounded-full transition-colors',
                isDark
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-red-500 hover:bg-red-600 text-white'
              ]"
              title="删除此缓存"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
            <div
              class="aspect-square relative bg-gray-200 dark:bg-gray-700"
            >
              <img
                v-if="entry.blobUrl"
                :src="entry.blobUrl"
                :alt="entry.key"
                class="w-full h-full object-cover"
                @error="(e) => handleImageError(e, entry.key)"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center"
              >
                <span
                  :class="[
                    'text-xs text-center px-2',
                    isDark ? 'text-gray-500' : 'text-gray-400'
                  ]"
                >
                  图片不存在或已失效
                </span>
              </div>
            </div>
            <div
              :class="[
                'p-2 text-xs',
                isDark ? 'text-gray-300' : 'text-gray-700'
              ]"
            >
              <p class="truncate" :title="entry.key">{{ entry.key }}</p>
              <p
                :class="[
                  'mt-1',
                  isDark ? 'text-gray-500' : 'text-gray-500'
                ]"
              >
                {{ formatTimestamp(entry.timestamp) }}
              </p>
            </div>
          </div>
          <div
            v-if="imageEntries.length === 0"
            :class="[
              'col-span-full text-center py-8',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            暂无图片缓存
          </div>
        </div>

        <!-- 文字缓存列表显示 -->
        <div v-else class="space-y-0">
          <div
            v-for="(entry, index) in textEntries"
            :key="entry.key"
            class="w-full relative py-2"
          >
            <!-- 分割线（在顶部） -->
            <div
              v-if="index > 0"
              :class="[
                'absolute top-0 left-0 right-0 border-t',
                isDark ? 'border-gray-700' : 'border-gray-200'
              ]"
            ></div>
            <!-- 删除按钮（垂直居中） -->
            <button
              @click="handleDeleteEntry(entry.key)"
              :class="[
                'absolute top-1/2 -translate-y-1/2 right-0 p-1.5 rounded-full transition-colors z-10',
                isDark
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-red-500 hover:bg-red-600 text-white'
              ]"
              title="删除此缓存"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
            <!-- 第一行：Header信息（灰色） -->
            <div
              :class="[
                'flex items-center gap-3 pr-10 mb-1',
                isDark ? 'text-gray-400' : 'text-gray-500'
              ]"
            >
              <span class="text-sm font-medium">{{ entry.key }}</span>
              <span class="text-xs">
                段落索引: {{ entry.paragraphIndex }}
              </span>
              <span class="text-xs">
                {{ formatTimestamp(entry.timestamp) }}
              </span>
            </div>
            <!-- 第二行：内容（白色突出） -->
            <div class="pr-10">
              <p
                :class="[
                  'text-sm whitespace-pre-wrap line-clamp-2',
                  isDark ? 'text-white' : 'text-gray-900'
                ]"
              >
                {{ entry.paragraphContent?.content || '无内容' }}
              </p>
            </div>
          </div>
          <div
            v-if="textEntries.length === 0"
            :class="[
              'text-center py-8',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            暂无文字缓存
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { XMarkIcon, TrashIcon } from '@heroicons/vue/24/outline'
import { imageCache } from '../../utils/imageCache'
import { textCache } from '../../utils/textCache'
import { showToast } from '../../utils/toast'

const props = defineProps<{
  isDark: boolean
  type: 'image' | 'text'
}>()

const emit = defineEmits<{
  close: []
  refresh: []
}>()

// 刷新触发器（用于强制重新计算）
const refreshTrigger = ref(0)

// 计算缓存大小和条目
const cacheSize = computed(() => {
  return props.type === 'image' ? imageCache.size : textCache.size
})

const imageEntries = computed(() => {
  // 使用 refreshTrigger 来触发重新计算
  refreshTrigger.value
  // 只返回有有效 blobUrl 的条目
  return imageCache.getAllEntries().filter(entry => entry.blobUrl !== null)
})

const textEntries = computed(() => {
  // 使用 refreshTrigger 来触发重新计算
  refreshTrigger.value
  return textCache.getAllEntries()
})

// 格式化时间戳
const formatTimestamp = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 处理图片加载错误
const handleImageError = (event: Event, key: string) => {
  console.error('图片加载失败:', key, event)
  // 如果图片加载失败，可能是 blob URL 已失效，删除该缓存
  imageCache.delete(key)
  refreshTrigger.value++
  showToast('图片已失效，已自动删除缓存', 'warning')
}

// 删除单个缓存条目
const handleDeleteEntry = (key: string) => {
  if (props.type === 'image') {
    imageCache.delete(key)
    showToast('已删除图片缓存', 'success')
  } else {
    textCache.delete(key)
    showToast('已删除文字缓存', 'success')
  }
  // 触发刷新
  refreshTrigger.value++
  emit('refresh')
}

// 清空全部缓存
const handleClearAll = () => {
  if (confirm(`确定要清空所有${props.type === 'image' ? '图片' : '文字'}缓存吗？`)) {
    if (props.type === 'image') {
      const size = imageCache.size
      imageCache.clear()
      showToast(`已清空所有图片缓存（${size} 项）`, 'success')
    } else {
      const size = textCache.size
      textCache.clear()
      showToast(`已清空所有文字缓存（${size} 项）`, 'success')
    }
    // 触发刷新
    refreshTrigger.value++
    emit('refresh')
  }
}

// 关闭对话框
const handleClose = () => {
  emit('close')
}
</script>

