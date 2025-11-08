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
              titleColor || (isDark ? 'text-white' : 'text-gray-900')
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
          <!-- 警告图标（如果 type 为 danger） -->
          <div v-if="type === 'danger'" class="text-center mb-4">
            <svg class="w-12 h-12 mx-auto text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          
          <!-- 消息内容 -->
          <div v-if="message" class="text-sm mb-2">
            <p v-if="typeof message === 'string'">{{ message }}</p>
            <div v-else v-html="message"></div>
          </div>
          
          <!-- 列表内容（如果提供了 items） -->
          <div v-if="items && items.length > 0" class="mt-4">
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(item, index) in items" :key="index">{{ item }}</li>
            </ul>
          </div>
          
          <!-- 警告文本（如果 type 为 danger） -->
          <p v-if="type === 'danger' && warningText" class="text-sm text-red-600 font-bold text-center mt-4">
            {{ warningText }}
          </p>
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
              type === 'danger'
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : isDark
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
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
  type?: 'default' | 'danger'  // 对话框类型
  items?: string[]  // 列表项（用于显示操作将删除的内容）
  warningText?: string  // 警告文本（用于 danger 类型）
  titleColor?: string  // 标题颜色类
}

const props = withDefaults(defineProps<Props>(), {
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
</script>

