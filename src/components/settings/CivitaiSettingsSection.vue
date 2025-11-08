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

      <!-- Timeout and Draw Timeout -->
      <div class="flex gap-4">
        <div class="max-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            Civitai 请求超时（秒）
          </label>
          <input
            :value="localTimeout"
            @blur="handleTimeoutBlur"
            @keyup.enter="handleTimeoutBlur"
            type="number"
            step="0.1"
            min="1"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
          <p 
            :class="[
              'mt-1 text-xs',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            默认 60秒
          </p>
        </div>

        <div class="max-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            绘图任务超时（秒）
          </label>
          <input
            :value="localDrawTimeout"
            @blur="handleDrawTimeoutBlur"
            @keyup.enter="handleDrawTimeoutBlur"
            type="number"
            min="60"
            max="3600"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
          <p 
            :class="[
              'mt-1 text-xs',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            范围：60-3600秒，默认 600秒（10分钟）
          </p>
        </div>
      </div>

      <!-- Parallel Workers -->
      <div class="max-w-[200px]">
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          并行下载线程数
        </label>
        <input
          :value="localParallelWorkers"
          @blur="handleParallelWorkersBlur"
          @keyup.enter="handleParallelWorkersBlur"
          type="number"
          min="1"
          max="10"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
        <p 
          :class="[
            'mt-1 text-xs',
            isDark ? 'text-gray-400' : 'text-gray-500'
          ]"
        >
          范围：1-10，默认 4
        </p>
      </div>

      <!-- Retry Count and Delay -->
      <div class="flex gap-4">
        <div class="max-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            API 重试次数
          </label>
          <input
            :value="localRetryCount"
            @blur="handleRetryCountBlur"
            @keyup.enter="handleRetryCountBlur"
            type="number"
            min="1"
            max="10"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
          <p 
            :class="[
              'mt-1 text-xs',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            范围：1-10，默认 5
          </p>
        </div>

        <div class="max-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            重试延迟（秒）
          </label>
          <input
            :value="localRetryDelay"
            @blur="handleRetryDelayBlur"
            @keyup.enter="handleRetryDelayBlur"
            type="number"
            step="0.1"
            min="0.1"
            max="60"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          />
          <p 
            :class="[
              'mt-1 text-xs',
              isDark ? 'text-gray-400' : 'text-gray-500'
            ]"
          >
            范围：0.1-60秒，默认 5秒
          </p>
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

const localApiToken = ref(props.settings?.api_token || '')
const localTimeout = ref(String(props.settings?.timeout || 60.0))
const localParallelWorkers = ref(String(props.settings?.parallel_workers || 4))
const localDrawTimeout = ref(String(props.settings?.draw_timeout || 600))
const localRetryCount = ref(String(props.settings?.retry_count || 5))
const localRetryDelay = ref(String(props.settings?.retry_delay || 5.0))

// 监听 settings 变化，同步本地状态
watch(() => props.settings, (newSettings) => {
  if (newSettings) {
    localApiToken.value = newSettings.api_token || ''
    localTimeout.value = String(newSettings.timeout || 60.0)
    localParallelWorkers.value = String(newSettings.parallel_workers || 4)
    localDrawTimeout.value = String(newSettings.draw_timeout || 600)
    localRetryCount.value = String(newSettings.retry_count || 5)
    localRetryDelay.value = String(newSettings.retry_delay || 5.0)
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

// 处理并行下载线程数
const handleParallelWorkersBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 1 && value <= 10) {
    localParallelWorkers.value = String(value)
    emit('update', { parallel_workers: value })
  } else {
    target.value = localParallelWorkers.value // 恢复原值
  }
}

// 处理重试次数
const handleRetryCountBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 1 && value <= 10) {
    localRetryCount.value = String(value)
    emit('update', { retry_count: value })
  } else {
    target.value = localRetryCount.value // 恢复原值
  }
}

// 处理重试延迟
const handleRetryDelayBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  if (!isNaN(value) && value >= 0.1 && value <= 60) {
    localRetryDelay.value = String(value)
    emit('update', { retry_delay: value })
  } else {
    target.value = localRetryDelay.value // 恢复原值
  }
}

// 处理绘图任务超时
const handleDrawTimeoutBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 60 && value <= 3600) {
    localDrawTimeout.value = String(value)
    emit('update', { draw_timeout: value })
  } else {
    target.value = localDrawTimeout.value // 恢复原值
  }
}
</script>

