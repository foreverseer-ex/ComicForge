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

        <!-- 模型选择：Ollama 始终显示下拉框，其他提供商如果有模型列表也显示下拉框 -->
        <div class="flex-1 min-w-[350px]" v-if="isOllama || (!isOllama && availableModels.length > 0)">
          <label 
            :class="[
              'block text-sm font-medium mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            模型
            <span v-if="loadingOllamaModels" class="text-xs text-gray-500 ml-2">(加载中...)</span>
            <span v-else-if="isOllama && availableModels.length === 0" class="text-xs text-red-500 ml-2">(未找到模型)</span>
          </label>
          <select
            :value="localModel"
            @change="handleModelChange"
            :disabled="loadingOllamaModels"
            :class="[
              'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500',
              loadingOllamaModels ? 'opacity-50 cursor-not-allowed' : ''
            ]"
          >
            <!-- 如果当前模型不在列表中，但用户已设置，显示当前模型（xai 提供商不允许，会强制使用默认值） -->
            <option v-if="localProvider !== 'xai' && localModel && !availableModels.includes(localModel)" :value="localModel" disabled>
              {{ localModel }} (不可用)
            </option>
            <!-- 显示可用模型列表 -->
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}{{ isRecommendedModel(model) ? ' (推荐)' : '' }}
            </option>
            <!-- 如果没有可用模型且不在加载中 -->
            <option v-if="availableModels.length === 0 && !loadingOllamaModels" value="" disabled>
              {{ isOllama ? '请确保 Ollama 服务正在运行并且已下载模型' : '暂无可用模型' }}
            </option>
          </select>
        </div>
      </div>

      <!-- 自定义模型输入：仅当不是 Ollama、不是 xai 且没有模型列表时显示 -->
      <div v-if="!isOllama && localProvider !== 'xai' && availableModels.length === 0">
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
            isDark ? 'text-gray-300' : 'text-gray-700',
            isApiKeyDisabled ? 'opacity-50' : ''
          ]"
        >
          API Key
          <span v-if="isApiKeyDisabled" class="text-xs text-gray-500 ml-2">(Ollama 不需要)</span>
        </label>
        <input
          :value="localApiKey"
          @blur="handleApiKeyBlur"
          @keyup.enter="handleApiKeyBlur"
          type="password"
          :disabled="isApiKeyDisabled"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500',
            isApiKeyDisabled ? 'opacity-50 cursor-not-allowed' : ''
          ]"
        />
      </div>

      <!-- API Base URL -->
      <div>
        <label 
          :class="[
            'block text-sm font-medium mb-2',
            isDark ? 'text-gray-300' : 'text-gray-700',
            isBaseUrlDisabled ? 'opacity-50' : ''
          ]"
        >
          API Base URL
          <span v-if="isBaseUrlDisabled" class="text-xs text-gray-500 ml-2">(Ollama 使用固定地址)</span>
        </label>
        <input
          :value="localBaseUrl"
          @blur="handleBaseUrlBlur"
          @keyup.enter="handleBaseUrlBlur"
          type="text"
          :disabled="isBaseUrlDisabled"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
              : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500',
            isBaseUrlDisabled ? 'opacity-50 cursor-not-allowed' : ''
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
          :disabled="isDeveloperModeDisabled"
          :class="[
              'w-4 h-4 rounded',
              isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300',
              isDeveloperModeDisabled ? 'opacity-50 cursor-not-allowed' : ''
            ]"
        />
        <label 
          :class="[
            'text-sm font-medium',
            isDark ? 'text-gray-300' : 'text-gray-700',
            isDeveloperModeDisabled ? 'opacity-50' : ''
          ]"
        >
          开发者模式
          <span v-if="isDeveloperModeDisabled" class="text-xs text-gray-500 ml-2">(Ollama 默认不使用)</span>
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
// 注意：xai 提供商只允许以下三个模型，且 grok-4-fast-non-reasoning 为默认推荐模型
const ollamaModels = ref<string[]>([]) // Ollama 模型列表（响应式）
const providerModels: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  xai: ['grok-4-fast-non-reasoning', 'grok-code-fast-1', 'grok-4-fast-reasoning'], // 推荐模型放在第一位
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
  google: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  custom: []
}

// 推荐的模型列表（用于显示"推荐"标签）
const recommendedModels: Record<string, string> = {
  xai: 'grok-4-fast-non-reasoning'
}

// 默认模型列表（当提供商变化时使用）
const defaultModels: Record<string, string> = {
  xai: 'grok-4-fast-non-reasoning'
}

// Base URL 映射
const providerBaseUrls: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  xai: 'https://api.x.ai/v1',
  ollama: 'http://127.0.0.1:11434',
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
const loadingOllamaModels = ref(false)

// 计算可用模型列表
const availableModels = computed(() => {
  // Ollama 使用响应式的模型列表
  if (localProvider.value === 'ollama') {
    return ollamaModels.value
  }
  return providerModels[localProvider.value] || []
})

// 判断是否为 Ollama 提供商
const isOllama = computed(() => {
  return localProvider.value === 'ollama'
})

// 判断是否禁用 API Key（Ollama 不需要）
const isApiKeyDisabled = computed(() => {
  return isOllama.value
})

// 判断是否禁用开发者模式（Ollama 默认不使用）
const isDeveloperModeDisabled = computed(() => {
  return isOllama.value
})

// 判断是否禁用 Base URL（Ollama 使用固定地址）
const isBaseUrlDisabled = computed(() => {
  return isOllama.value
})

// 判断模型是否为推荐模型
const isRecommendedModel = (model: string): boolean => {
  const recommended = recommendedModels[localProvider.value]
  return recommended === model
}

// 注意：showModelDropdown 已不再使用，改为在模板中直接判断
// 对于 Ollama，始终显示下拉框（从后端获取模型列表）
// 对于其他提供商，如果模型列表不为空，也显示下拉框

// 加载 Ollama 模型列表
const loadOllamaModels = async () => {
  if (!isOllama.value) {
    return
  }
  
  loadingOllamaModels.value = true
  try {
    // 使用当前配置的 base_url 或默认值
    const baseUrl = localBaseUrl.value || providerBaseUrls.ollama
    const response: any = await api.get('/settings/llm/ollama-models', {
      params: { base_url: baseUrl }
    })
    
    // API 响应拦截器已经返回 response.data，所以直接使用 response
    if (response.models && Array.isArray(response.models)) {
      // 更新响应式的模型列表
      ollamaModels.value = response.models
      
      // 如果模型列表已加载，但当前模型不在列表中，且当前模型为空，选择第一个模型
      if (response.models.length > 0 && !localModel.value) {
        localModel.value = response.models[0]
        emit('update', {
          provider: 'ollama',
          base_url: localBaseUrl.value,
          model: localModel.value
        })
      }
    } else {
      console.warn('Ollama 模型列表为空，请确保 Ollama 服务正在运行并且已下载模型')
      ollamaModels.value = []
    }
  } catch (error: any) {
    console.error('加载 Ollama 模型列表失败:', error)
    // 如果加载失败，清空模型列表（不使用方法默认值）
    ollamaModels.value = []
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    // 不显示 alert，只在控制台输出错误，让用户看到下拉框中的错误提示
    console.error('加载 Ollama 模型列表失败:', errorMessage)
  } finally {
    loadingOllamaModels.value = false
  }
}

// 监听 settings 变化，同步本地状态
watch(() => props.settings, async (newSettings) => {
  if (newSettings) {
    const provider = newSettings.provider || 'xai'
    const prevProvider = localProvider.value
    localProvider.value = provider
    let model = newSettings.model || ''
    
    // 如果是 xai 提供商，检查模型是否在允许列表中
    if (provider === 'xai') {
      const allowedModels = providerModels.xai
      // 如果模型为空或不在允许列表中，使用默认值
      if (!model || !allowedModels.includes(model)) {
        model = defaultModels.xai || allowedModels[0]
        // 如果模型发生变化，需要更新设置
        if (model !== newSettings.model) {
          emit('update', { model })
        }
      }
    }
    
    localModel.value = model
    localApiKey.value = newSettings.api_key || ''
    localBaseUrl.value = newSettings.base_url || ''
    localTemperature.value = String(newSettings.temperature || 0.7)
    localTimeout.value = String(newSettings.timeout || 60.0)
    localDeveloperMode.value = newSettings.developer_mode ?? (provider !== 'ollama')
    localSystemPrompt.value = newSettings.system_prompt || ''
    localSummaryEpoch.value = String(newSettings.summary_epoch || 2)

    // 如果是 Ollama，始终加载模型列表（从后端获取）
    if (provider === 'ollama') {
      // 如果提供商发生变化，或者模型列表为空，重新加载
      if (prevProvider !== provider || ollamaModels.value.length === 0) {
        await loadOllamaModels()
      }
    }

    // 检查模型是否在可用列表中
    const models = availableModels.value
    if (provider === 'ollama') {
      // 对于 Ollama，如果模型在列表中，使用下拉框；否则使用自定义输入
      if (models && models.length > 0 && models.includes(localModel.value)) {
        localModelCustom.value = ''
      } else {
        // 如果模型不在列表中，但模型列表已加载，可能是用户自定义的模型名
        // 这种情况下，如果模型列表不为空，仍然显示下拉框，但当前模型不在选项中
        localModelCustom.value = localModel.value
      }
    } else {
      // 对于其他提供商（包括 xai），如果模型在列表中，使用下拉框
      if (models && models.includes(localModel.value)) {
        localModelCustom.value = ''
      } else {
        // xai 提供商不允许自定义模型，如果模型不在列表中，使用默认值
        if (provider === 'xai') {
          localModel.value = defaultModels.xai || models[0]
          localModelCustom.value = ''
          emit('update', { model: localModel.value })
        } else {
          localModelCustom.value = localModel.value
        }
      }
    }
  }
}, { immediate: true, deep: true })

// 处理提供商变化
const handleProviderChange = async (event: Event) => {
  const target = event.target as HTMLSelectElement
  localProvider.value = target.value
  localBaseUrl.value = providerBaseUrls[target.value] || ''
  
  // 如果是 Ollama，立即加载模型列表
  if (target.value === 'ollama') {
    // 先重置模型列表，然后加载
    ollamaModels.value = []
    await loadOllamaModels()
    // 加载完成后，如果有模型，选择第一个；否则清空
    const models = availableModels.value
    if (models && models.length > 0) {
      localModel.value = models[0]
      localModelCustom.value = ''
    } else {
      // 如果没有模型，保持当前模型或清空
      if (!localModel.value) {
        localModel.value = ''
        localModelCustom.value = ''
      }
    }
  } else if (target.value === 'xai') {
    // 对于 xai 提供商，只允许使用预定义的模型，默认使用推荐模型
    const models = availableModels.value
    const currentModel = localModel.value
    // 如果当前模型不在允许列表中，使用默认推荐模型
    if (!currentModel || !models.includes(currentModel)) {
      localModel.value = defaultModels.xai || models[0]
      localModelCustom.value = ''
    } else {
      localModelCustom.value = ''
    }
  } else {
    // 对于其他提供商，使用硬编码的模型列表
    const models = availableModels.value
    if (models && models.length > 0) {
      localModel.value = models[0]
      localModelCustom.value = ''
    } else {
      localModel.value = ''
      localModelCustom.value = ''
    }
  }
  
  // 如果是 Ollama，禁用 API Key 和开发者模式（但不清空值）
  const updates: any = {
    provider: target.value,
    base_url: localBaseUrl.value,
    model: localModel.value || localModelCustom.value
  }
  
  if (target.value === 'ollama') {
    // Ollama 默认不使用开发者模式，但保留 api_key 的值（只禁用输入框）
    updates.developer_mode = false
    localDeveloperMode.value = false
  }
  
  emit('update', updates)
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
const handleBaseUrlBlur = async (event: Event) => {
  // 如果 Base URL 被禁用（Ollama），不处理
  if (isBaseUrlDisabled.value) {
    return
  }
  
  const target = event.target as HTMLInputElement
  localBaseUrl.value = target.value
  
  // 如果是 Ollama，重新加载模型列表
  if (isOllama.value) {
    await loadOllamaModels()
  }
  
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
    // API 响应拦截器已经返回 response.data，所以直接使用 response
    const response: any = await api.post('/settings/llm/reset-system-prompt')
    localSystemPrompt.value = response.system_prompt
    emit('update', { system_prompt: response.system_prompt })
    alert('系统提示词已重置为默认值')
  } catch (error: any) {
    console.error('重置系统提示词失败:', error)
    alert('重置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    resetting.value = false
  }
}
</script>

