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
      绘图服务设置
    </h2>

    <div class="space-y-4">
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          绘图后端
        </label>
        <select
          :value="localBackend"
          @change="handleBackendChange"
          :class="[
            'w-full max-w-md px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        >
          <option value="sd_forge">SD-Forge (本地)</option>
          <option value="civitai">Civitai (云端)</option>
        </select>
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

const localBackend = ref(props.settings?.backend || 'sd_forge')

// 监听 settings 变化，同步本地状态
watch(() => props.settings?.backend, (newVal) => {
  if (newVal !== undefined) {
    localBackend.value = newVal
  }
}, { immediate: true })

// 处理后端选择变化
const handleBackendChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  localBackend.value = target.value
  emit('update', { backend: target.value })
}
</script>

