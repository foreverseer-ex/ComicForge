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
      Civitai 设置
    </h2>

    <div class="space-y-4">
      <!-- API Token -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          Civitai API Token
        </label>
        <input
          :value="localApiToken"
          @blur="handleApiTokenBlur"
          @keyup.enter="handleApiTokenBlur"
          type="password"
          :class="[
            'w-full max-w-md px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- Timeout -->
      <div class="max-w-[200px]">
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          Civitai 请求超时
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

const localApiToken = ref(props.settings?.api_token || '')
const localTimeout = ref(String(props.settings?.timeout || 30.0))

// 监听 settings 变化，同步本地状态
watch(() => props.settings, (newSettings) => {
  if (newSettings) {
    localApiToken.value = newSettings.api_token || ''
    localTimeout.value = String(newSettings.timeout || 30.0)
  }
}, { immediate: true, deep: true })

// 处理 API Token
const handleApiTokenBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localApiToken.value = target.value
  emit('update', { api_token: target.value.trim() || null })
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
</script>

