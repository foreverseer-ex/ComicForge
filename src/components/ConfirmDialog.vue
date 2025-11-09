<template>
  <AlertDialogRoot :open="show" @update:open="onUpdateOpen">
    <AlertDialogPortal>
      <AlertDialogOverlay class="fixed inset-0 bg-black/50 z-50" />
      <AlertDialogContent
        :class="[
          'fixed z-50 w-full max-w-md rounded-lg shadow-xl top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
          'mx-4 md:mx-0',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <!-- 标题栏 -->
        <div :class="['border-b','px-4 py-3 md:px-6 md:py-4', isDark ? 'border-gray-700' : 'border-gray-200']">
          <AlertDialogTitle :class="['text-base md:text-lg font-semibold', titleColor || (isDark ? 'text-white' : 'text-gray-900')]">
            {{ title }}
          </AlertDialogTitle>
          <AlertDialogDescription class="sr-only">{{ typeof message === 'string' ? message : '' }}</AlertDialogDescription>
        </div>

        <!-- 内容区域 -->
        <div :class="['px-4 py-3 md:px-6 md:py-4', isDark ? 'text-gray-300' : 'text-gray-700']">
          <div v-if="type === 'danger'" class="text-center mb-4">
            <svg class="w-12 h-12 mx-auto text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>

          <div v-if="message" class="text-sm mb-2">
            <p v-if="typeof message === 'string'">{{ message }}</p>
            <div v-else v-html="message"></div>
          </div>

          <div v-if="items && items.length > 0" class="mt-4">
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(item, index) in items" :key="index">{{ item }}</li>
            </ul>
          </div>

          <div v-if="$slots.extra" class="mt-3">
            <slot name="extra" />
          </div>

          <p v-if="type === 'danger' && warningText" class="text-sm text-red-600 font-bold text-center mt-4">
            {{ warningText }}
          </p>
        </div>

        <!-- 底部按钮 -->
        <div :class="['flex items-center justify-end gap-3 border-t','px-4 py-3 md:px-6 md:py-4', isDark ? 'border-gray-700' : 'border-gray-200']">
          <AlertDialogCancel as-child>
            <button
              @click="handleCancel"
              :class="['px-4 py-2 rounded-lg font-medium transition-colors', isDark ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900']"
            >
              {{ cancelText }}
            </button>
          </AlertDialogCancel>
          <AlertDialogAction as-child>
            <button
              @click="handleConfirm"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                type === 'danger' ? 'bg-red-600 hover:bg-red-700 text-white' : (isDark ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white')
              ]"
            >
              {{ confirmText }}
            </button>
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>

<script setup lang="ts">
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import {
  AlertDialogRoot,
  AlertDialogPortal,
  AlertDialogOverlay,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from 'radix-vue'

interface Props {
  show: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'default' | 'danger'  // 对话框类型
  items?: string[]  // 列表项（用于显示操作将删除的内容）
  warningText?: string  // 警告文本（用于 danger 类型）
  titleColor?: string  // 标题颜色类
}

withDefaults(defineProps<Props>(), {
  title: '确认',
  confirmText: '确定',
  cancelText: '取消',
  type: 'default'
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

const onUpdateOpen = (v: boolean) => {
  // 由父组件控制 show，当对话框尝试关闭时，通知父组件取消
  if (!v) emit('cancel')
}
</script>

