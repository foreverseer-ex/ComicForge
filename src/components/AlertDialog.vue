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
        <div :class="['border-b','px-4 py-3 md:px-6 md:py-4', isDark ? 'border-gray-700' : 'border-gray-200']">
          <AlertDialogTitle :class="['text-base md:text-lg font-semibold', isDark ? 'text-white' : 'text-gray-900']">
            {{ title }}
          </AlertDialogTitle>
          <AlertDialogDescription class="sr-only">{{ typeof message === 'string' ? message : '' }}</AlertDialogDescription>
        </div>

        <div :class="['px-4 py-3 md:px-6 md:py-4', isDark ? 'text-gray-300' : 'text-gray-700']">
          <p class="text-sm">{{ message }}</p>
        </div>

        <div :class="['flex items-center justify-end gap-3 border-t','px-4 py-3 md:px-6 md:py-4', isDark ? 'border-gray-700' : 'border-gray-200']">
          <AlertDialogAction as-child>
            <button
              @click="handleClose"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                isDark
                  ? 'bg-gray-700 hover:bg-gray-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
              ]"
            >
              确定
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
} from 'radix-vue'

interface Props {
  show: boolean
  title?: string
  message: string
}

withDefaults(defineProps<Props>(), {
  title: '提示'
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const handleClose = () => {
  emit('close')
}

const onUpdateOpen = (v: boolean) => {
  if (!v) emit('close')
}
</script>

