<template>
  <div 
    :class="[
      'shadow rounded-lg p-6',
      isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    ]"
  >
    <h2 
      :class="[
        'text-xl font-bold mb-4',
        isDark ? 'text-white' : 'text-gray-900'
      ]"
    >
      SD Forge 设置
    </h2>

    <div class="space-y-4">
      <!-- Base URL -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          SD Forge Base URL
        </label>
        <input
          :value="localBaseUrl"
          @blur="handleBaseUrlBlur"
          @keyup.enter="handleBaseUrlBlur"
          type="text"
          :class="[
            'w-full max-w-md px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- 安装目录 -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          SD Forge 安装目录
        </label>
        <input
          :value="localHome"
          @blur="handleHomeBlur"
          @keyup.enter="handleHomeBlur"
          type="text"
          :class="[
            'w-full max-w-md px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- Timeout 和 Generate Timeout -->
      <div class="flex gap-4 flex-wrap">
        <div class="flex-1 min-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            SD Forge 请求超时
          </label>
          <input
            :value="localTimeout"
            @blur="handleTimeoutBlur"
            @keyup.enter="handleTimeoutBlur"
            type="number"
            step="0.1"
            min="0"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
        </div>

        <div class="flex-1 min-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            SD Forge 生成超时
          </label>
          <input
            :value="localGenerateTimeout"
            @blur="handleGenerateTimeoutBlur"
            @keyup.enter="handleGenerateTimeoutBlur"
            type="number"
            step="0.1"
            min="0"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  settings: any
  isDark: boolean
}>()

const emit = defineEmits<{
  update: [updates: any]
}>()

const localBaseUrl = ref(props.settings?.base_url || '')
const localHome = ref(props.settings?.home || '')
const localTimeout = ref(String(props.settings?.timeout || 30.0))
const localGenerateTimeout = ref(String(props.settings?.generate_timeout || 120.0))

// 监听 settings 变化，同步本地状态
watch(() => props.settings, (newSettings) => {
  if (newSettings) {
    localBaseUrl.value = newSettings.base_url || ''
    localHome.value = newSettings.home || ''
    localTimeout.value = String(newSettings.timeout || 30.0)
    localGenerateTimeout.value = String(newSettings.generate_timeout || 120.0)
  }
}, { immediate: true, deep: true })

// 处理 Base URL
const handleBaseUrlBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localBaseUrl.value = target.value
  emit('update', { base_url: target.value.trim() })
}

// 处理安装目录
const handleHomeBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localHome.value = target.value
  emit('update', { home: target.value.trim() })
}

// 处理 Timeout
const handleTimeoutBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  if (!isNaN(value) && value > 0) {
    localTimeout.value = String(value)
    emit('update', { timeout: value })
  } else {
    target.value = localTimeout.value // 恢复原值
  }
}

// 处理 Generate Timeout
const handleGenerateTimeoutBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  if (!isNaN(value) && value > 0) {
    localGenerateTimeout.value = String(value)
    emit('update', { generate_timeout: value })
  } else {
    target.value = localGenerateTimeout.value // 恢复原值
  }
}
</script>

