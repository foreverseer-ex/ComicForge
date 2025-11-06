<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="handleCancel"
    >
      <div
        :class="[
          'w-full max-w-md rounded-lg shadow-xl',
          'mx-4 md:mx-0', // 移动端添加左右边距
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 标题栏 -->
        <div
          :class="[
            'border-b',
            'px-4 py-3 md:px-6 md:py-4', // 移动端使用更小的内边距
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <h3
            :class="[
              'text-base md:text-lg font-semibold', // 移动端使用更小的字体
              isDark ? 'text-white' : 'text-gray-900'
            ]"
          >
            {{ title }}
          </h3>
        </div>

        <!-- 内容区域 -->
        <div
          :class="[
            'px-4 py-3 md:px-6 md:py-4', // 移动端使用更小的内边距
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          <p class="text-sm">{{ message }}</p>
        </div>

        <!-- 底部按钮 -->
        <div
          :class="[
            'flex items-center justify-end gap-3 border-t',
            'px-4 py-3 md:px-6 md:py-4', // 移动端使用更小的内边距
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <button
            @click="handleCancel"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
            ]"
          >
            {{ cancelText }}
          </button>
          <button
            @click="handleConfirm"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              isDark
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            ]"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'

interface Props {
  show: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认',
  confirmText: '确定',
  cancelText: '取消'
})

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

