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
      AI 大模型设置
    </h2>

    <div class="space-y-4">
      <!-- 提供商和模型选择 -->
      <div class="flex gap-4 flex-wrap">
        <div class="flex-1 min-w-[250px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            提供商
          </label>
          <select
            :value="localProvider"
            @change="handleProviderChange"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          >
            <option value="xai">xAI (Grok)</option>
            <option value="openai">OpenAI (GPT)</option>
            <option value="ollama">Ollama (本地)</option>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="google">Google (Gemini)</option>
            <option value="custom">自定义</option>
          </select>
        </div>

        <div class="flex-1 min-w-[350px]" v-if="showModelDropdown">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            模型
          </label>
          <select
            :value="localModel"
            @change="handleModelChange"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
            ]"
          >
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>
      </div>

      <!-- 自定义模型输入 -->
      <div v-if="!showModelDropdown">
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          自定义模型名称
        </label>
        <input
          :value="localModelCustom"
          @blur="handleModelCustomBlur"
          @keyup.enter="handleModelCustomBlur"
          type="text"
          placeholder="手动输入模型名称"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- API Key -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          API Key
        </label>
        <input
          :value="localApiKey"
          @blur="handleApiKeyBlur"
          @keyup.enter="handleApiKeyBlur"
          type="password"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- API Base URL -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          API Base URL
        </label>
        <input
          :value="localBaseUrl"
          @blur="handleBaseUrlBlur"
          @keyup.enter="handleBaseUrlBlur"
          type="text"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        />
      </div>

      <!-- Temperature 和 Timeout -->
      <div class="flex gap-4 flex-wrap">
        <div class="flex-1 min-w-[200px]">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            Temperature
          </label>
          <input
            :value="localTemperature"
            @blur="handleTemperatureBlur"
            @keyup.enter="handleTemperatureBlur"
            type="number"
            step="0.1"
            min="0"
            max="2"
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
            请求超时
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

      <!-- 开发者模式 -->
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          :checked="localDeveloperMode"
          @change="handleDeveloperModeChange"
          :class="[
              'w-4 h-4 rounded',
              isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
            ]"
        />
        <label 
          :class="[
            'text-sm font-medium',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          开发者模式
        </label>
      </div>

      <!-- 系统提示词 -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label 
            :class="[
              'text-sm font-medium',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            系统提示词
          </label>
          <button
            @click="handleResetSystemPrompt"
            :disabled="resetting"
            :class="[
              'px-3 py-1 text-xs rounded-lg transition-colors',
              isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700',
              resetting ? 'opacity-50 cursor-not-allowed' : ''
            ]"
          >
            {{ resetting ? '重置中...' : '重置为默认值' }}
          </button>
        </div>
        <textarea
          :value="localSystemPrompt"
          @blur="handleSystemPromptBlur"
          rows="5"
          :class="[
            'w-full max-w-3xl px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
          ]"
        ></textarea>
      </div>

      <!-- 对话总结周期 -->
      <div class="max-w-[200px]">
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700'
          ]"
        >
          对话总结周期
        </label>
        <input
          :value="localSummaryEpoch"
          @blur="handleSummaryEpochBlur"
          @keyup.enter="handleSummaryEpochBlur"
          type="number"
          min="2"
          max="1000"
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
import { ref, watch, computed } from 'vue'
import api from '../../api'

const props = defineProps<{
  settings: any
  isDark: boolean
}>()

const emit = defineEmits<{
  update: [updates: any]
}>()

// 模型列表（根据提供商）
const providerModels: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  xai: ['grok-code-fast-1', 'grok-4-fast-reasoning', 'grok-4-fast-non-reasoning'],
  ollama: ['llama3.1', 'qwen2.5', 'mistral', 'deepseek-r1', 'phi4'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
  google: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  custom: []
}

// Base URL 映射
const providerBaseUrls: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  xai: 'https://api.x.ai/v1',
  ollama: 'http://localhost:11434',
  anthropic: 'https://api.anthropic.com',
  google: 'https://generativelanguage.googleapis.com',
  custom: ''
}

// 本地状态
const localProvider = ref(props.settings?.provider || 'xai')
const localModel = ref(props.settings?.model || '')
const localModelCustom = ref('')
const localApiKey = ref(props.settings?.api_key || '')
const localBaseUrl = ref(props.settings?.base_url || '')
const localTemperature = ref(String(props.settings?.temperature || 0.7))
const localTimeout = ref(String(props.settings?.timeout || 60.0))
const localDeveloperMode = ref(props.settings?.developer_mode ?? true)
const localSystemPrompt = ref(props.settings?.system_prompt || '')
const localSummaryEpoch = ref(String(props.settings?.summary_epoch || 2))
const resetting = ref(false)

// 计算可用模型列表
const availableModels = computed(() => {
  return providerModels[localProvider.value] || []
})

// 判断是否显示模型下拉框
const showModelDropdown = computed(() => {
  const models = availableModels.value
  return models.length > 0 && models.includes(localModel.value)
})

// 监听 settings 变化，同步本地状态
watch(() => props.settings, (newSettings) => {
  if (newSettings) {
    localProvider.value = newSettings.provider || 'xai'
    localModel.value = newSettings.model || ''
    localApiKey.value = newSettings.api_key || ''
    localBaseUrl.value = newSettings.base_url || ''
    localTemperature.value = String(newSettings.temperature || 0.7)
    localTimeout.value = String(newSettings.timeout || 60.0)
    localDeveloperMode.value = newSettings.developer_mode ?? true
    localSystemPrompt.value = newSettings.system_prompt || ''
    localSummaryEpoch.value = String(newSettings.summary_epoch || 2)

    // 检查模型是否在推荐列表中
    const models = availableModels.value
    if (models && models.includes(localModel.value)) {
      localModelCustom.value = ''
    } else {
      localModelCustom.value = localModel.value
    }
  }
}, { immediate: true, deep: true })

// 处理提供商变化
const handleProviderChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  localProvider.value = target.value
  localBaseUrl.value = providerBaseUrls[target.value] || ''
  
  const models = availableModels.value
  if (models && models.length > 0) {
    localModel.value = models[0]
    localModelCustom.value = ''
  } else {
    localModel.value = ''
    localModelCustom.value = ''
  }
  
  emit('update', {
    provider: target.value,
    base_url: localBaseUrl.value,
    model: localModel.value || localModelCustom.value
  })
}

// 处理模型变化
const handleModelChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  localModel.value = target.value
  localModelCustom.value = ''
  emit('update', { model: target.value })
}

// 处理自定义模型
const handleModelCustomBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localModelCustom.value = target.value
  emit('update', { model: target.value.trim() })
}

// 处理 API Key
const handleApiKeyBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localApiKey.value = target.value
  emit('update', { api_key: target.value })
}

// 处理 Base URL
const handleBaseUrlBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  localBaseUrl.value = target.value
  emit('update', { base_url: target.value.trim() })
}

// 处理 Temperature
const handleTemperatureBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseFloat(target.value)
  if (!isNaN(value) && value >= 0 && value <= 2) {
    localTemperature.value = String(value)
    emit('update', { temperature: value })
  } else {
    target.value = localTemperature.value // 恢复原值
  }
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

// 处理开发者模式
const handleDeveloperModeChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  localDeveloperMode.value = target.checked
  emit('update', { developer_mode: target.checked })
}

// 处理系统提示词
const handleSystemPromptBlur = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  localSystemPrompt.value = target.value
  emit('update', { system_prompt: target.value.trim() })
}

// 处理对话总结周期
const handleSummaryEpochBlur = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value)
  if (!isNaN(value) && value >= 2 && value <= 1000) {
    localSummaryEpoch.value = String(value)
    emit('update', { summary_epoch: value })
  } else {
    target.value = localSummaryEpoch.value // 恢复原值
  }
}

// 重置系统提示词
const handleResetSystemPrompt = async () => {
  if (!confirm('确定要重置系统提示词为默认值吗？')) {
    return
  }
  
  resetting.value = true
  try {
    const response = await api.post('/settings/llm/reset-system-prompt')
    localSystemPrompt.value = response.data.system_prompt
    emit('update', { system_prompt: response.data.system_prompt })
    alert('系统提示词已重置为默认值')
  } catch (error: any) {
    console.error('重置系统提示词失败:', error)
    alert('重置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    resetting.value = false
  }
}
</script>

