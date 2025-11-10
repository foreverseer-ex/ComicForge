<template>
  <div class="space-y-4">
    <!-- 任务名称和描述 -->
    <div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          任务名称
        </label>
        <input
          v-model="formData.name"
          type="text"
          placeholder="可选"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        />
      </div>
      <div class="mt-4">
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          任务描述
        </label>
        <textarea
          v-model="formData.desc"
          rows="4"
          placeholder="可选，填写额外的生成要求..."
          :class="[
            'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        ></textarea>
        <!-- 附加信息（只读，可关闭） -->
        <div v-if="additionalInfo && showAdditionalInfo" class="mt-2 p-3 rounded-lg border relative" :class="isDark ? 'bg-gray-800 border-gray-600' : 'bg-gray-50 border-gray-200'">
          <button
            @click="showAdditionalInfo = false"
            :class="[
              'absolute top-2 right-2 p-1 rounded transition-colors',
              isDark
                ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-300'
                : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'
            ]"
            title="关闭附加信息"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div class="text-xs font-medium mb-1 pr-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
            附加信息（来自角色设定）：
          </div>
          <div class="text-sm whitespace-pre-wrap pr-6" :class="isDark ? 'text-gray-300' : 'text-gray-700'">
            {{ additionalInfo }}
          </div>
        </div>
      </div>
    </div>

    <!-- 批量大小 -->
    <div>
      <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
        批量大小
      </label>
      <div class="flex gap-2 flex-wrap">
        <label
          v-for="size in [1, 2, 4, 8]"
          :key="size"
          :class="[
            'flex-1 min-w-[60px] px-3 py-2 rounded-lg border cursor-pointer transition-colors text-center text-sm font-medium',
            formData.batch_size === size
              ? isDark
                ? 'bg-blue-600 border-blue-500 text-white'
                : 'bg-blue-600 border-blue-600 text-white'
              : isDark
                ? 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          <input
            v-model.number="formData.batch_size"
            type="radio"
            :value="size"
            class="hidden"
          />
          {{ size }}
        </label>
      </div>
      <p :class="['mt-1 text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
        生成图片的数量
      </p>
    </div>

    <!-- 基础模型选择 -->
    <div>
      <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
        基础模型 *
      </label>
      <select
        v-model="formData.model"
        :disabled="loadingModels"
        :class="[
          'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
          isDark
            ? 'bg-gray-700 border-gray-600 text-white'
            : 'bg-white border-gray-300 text-gray-900'
        ]"
      >
        <option value="" disabled>{{ loadingModels ? '加载中...' : '选择模型' }}</option>
        <option 
          v-for="model in models" 
          :key="model.filename" 
          :value="model.version_name"
          :disabled="!isModelAvailable(model)"
        >
          {{ model.version_name }} {{ !isModelAvailable(model) && drawBackend === 'sd_forge' ? '(不可用)' : '' }}
        </option>
      </select>
    </div>

    <!-- 提示词 -->
    <div>
      <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
        正向提示词 *
      </label>
      <textarea
        v-model="formData.prompt"
        rows="4"
        placeholder="描述要生成的内容..."
        :class="[
          'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
          isDark
            ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
            : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
        ]"
      ></textarea>
    </div>

    <!-- 负向提示词 -->
    <div>
      <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
        负向提示词
      </label>
      <textarea
        v-model="formData.negative_prompt"
        rows="2"
        placeholder="要避免的内容..."
        :class="[
          'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
          isDark
            ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
            : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
        ]"
      ></textarea>
    </div>

    <!-- 采样器和步数 -->
    <div class="grid grid-cols-3 gap-4">
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          采样器
        </label>
        <select
          v-model="formData.sampler"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          ]"
        >
          <option v-for="sampler in samplers" :key="sampler" :value="sampler">
            {{ sampler }}
          </option>
        </select>
      </div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          采样步数
        </label>
        <input
          v-model.number="formData.steps"
          type="number"
          min="1"
          max="150"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          ]"
        />
      </div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          CFG Scale
        </label>
        <input
          v-model.number="formData.cfg_scale"
          type="number"
          min="1"
          max="30"
          step="0.5"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          ]"
        />
      </div>
    </div>

    <!-- 尺寸和种子 -->
    <div class="grid grid-cols-3 gap-4">
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          宽度
          <span v-if="drawBackend === 'civitai'" :class="[isDark ? 'text-yellow-400' : 'text-yellow-600', 'text-xs ml-1']">
            (最大 1024)
          </span>
        </label>
        <input
          v-model.number="formData.width"
          type="number"
          min="64"
          :max="maxWidthHeight"
          step="64"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          ]"
        />
        <p v-if="formData.width > maxWidthHeight" :class="['mt-1 text-xs', isDark ? 'text-red-400' : 'text-red-600']">
          宽度超过限制（最大 {{ maxWidthHeight }}），使用 Civitai 后端时将被限制为 1024
        </p>
      </div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          高度
          <span v-if="drawBackend === 'civitai'" :class="[isDark ? 'text-yellow-400' : 'text-yellow-600', 'text-xs ml-1']">
            (最大 1024)
          </span>
        </label>
        <input
          v-model.number="formData.height"
          type="number"
          min="64"
          :max="maxWidthHeight"
          step="64"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          ]"
        />
        <p v-if="formData.height > maxWidthHeight" :class="['mt-1 text-xs', isDark ? 'text-red-400' : 'text-red-600']">
          高度超过限制（最大 {{ maxWidthHeight }}），使用 Civitai 后端时将被限制为 1024
        </p>
      </div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          随机种子
        </label>
        <input
          v-model.number="formData.seed"
          type="number"
          placeholder="-1 表示随机"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        />
      </div>
    </div>

    <!-- CLIP Skip 和 VAE -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          CLIP Skip
        </label>
        <input
          v-model.number="formData.clip_skip"
          type="number"
          min="1"
          max="12"
          placeholder="留空使用默认值"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        />
      </div>
      <div>
        <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
          VAE
        </label>
        <input
          v-model="formData.vae"
          type="text"
          placeholder="留空使用默认值"
          :class="[
            'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
          ]"
        />
      </div>
    </div>

    <!-- LoRA 列表 -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label :class="['text-sm font-medium', isDark ? 'text-gray-300' : 'text-gray-700']">
          LoRA 模型
        </label>
        <button
          @click="addLoraRow"
          :disabled="loadingLoras"
          :class="[
            'flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors',
            loadingLoras
              ? isDark ? 'bg-gray-700 text-gray-500' : 'bg-gray-200 text-gray-400'
              : isDark
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
          ]"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          添加 LoRA
        </button>
      </div>
      
      <div v-if="loras.length > 0" class="space-y-2">
        <div
          v-for="(lora, index) in loras"
          :key="index"
          class="flex items-center gap-2"
        >
          <select
            v-model="lora.name"
            :disabled="loadingLoras"
            :class="[
              'flex-1 px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            ]"
          >
            <option value="" disabled>{{ loadingLoras ? '加载中...' : '选择 LoRA' }}</option>
            <option 
              v-for="loraOption in availableLoras" 
              :key="loraOption.filename" 
              :value="loraOption.version_name"
              :disabled="!isModelAvailable(loraOption)"
            >
              {{ loraOption.version_name }} {{ !isModelAvailable(loraOption) && drawBackend === 'sd_forge' ? '(不可用)' : '' }}
            </option>
          </select>
          <input
            v-model.number="lora.weight"
            type="number"
            min="-2"
            max="2"
            step="0.1"
            placeholder="权重"
            :class="[
              'w-24 px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            ]"
          />
          <button
            @click="removeLora(index)"
            :class="[
              'p-2 rounded-lg transition-colors',
              isDark
                ? 'hover:bg-red-900/30 text-red-400'
                : 'hover:bg-red-50 text-red-600'
            ]"
            title="删除"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <p v-else :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
        暂未添加 LoRA
      </p>
    </div>

    <!-- 插槽：用于添加额外的字段（如立绘标题和描述） -->
    <slot name="extra-fields"></slot>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import api from '../api'
import { showToast } from '../utils/toast'

interface Props {
  // 用于 AI 生成参数的上下文信息（如角色名称）
  contextInfo?: string
  // 附加信息（只读，显示在任务描述下方）
  additionalInfo?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'submit', data: {
    name?: string
    desc?: string
    model: string
    prompt: string
    negative_prompt: string
    sampler_name: string
    steps: number
    cfg_scale: number
    width: number
    height: number
    seed: number
    clip_skip?: number
    vae?: string
    loras: Record<string, number>
    batch_size?: number
  }): void
  (e: 'generate-params'): void
  (e: 'paste-params', params: any): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 采样器列表
const samplers = [
  'DPM++ 2M Karras',
  'DPM++ SDE Karras',
  'Euler a',
  'Euler',
  'LMS',
  'Heun',
  'DPM2',
  'DPM2 a',
  'DPM++ 2S a',
  'DPM++ 2M',
  'DPM++ SDE',
  'DPM fast',
  'DPM adaptive',
  'LMS Karras',
  'DPM2 Karras',
  'DPM2 a Karras',
  'DPM++ 2S a Karras',
]

interface LoraItem {
  name: string
  weight: number
}

// 表单数据
const formData = ref({
  name: '',
  desc: '',
  model: '',
  prompt: '',
  negative_prompt: 'worst quality, lowres, bad anatomy, extra fingers, deformed, blurry',
  sampler: 'DPM++ 2M Karras',
  steps: 30,
  cfg_scale: 7.0,
  width: 1024,
  height: 1024,
  seed: -1,
  clip_skip: 2,
  vae: '',
  batch_size: 1
})

const loras = ref<LoraItem[]>([])

// 可用模型和 LoRA
const models = ref<any[]>([])
const availableLoras = ref<any[]>([])
const loadingModels = ref(false)
const loadingLoras = ref(false)

// 附加信息显示状态
const showAdditionalInfo = ref(true)

// 绘图后端设置
const drawBackend = ref<'sd_forge' | 'civitai'>('civitai')

// 根据后端类型计算最大宽高限制
const maxWidthHeight = computed(() => {
  return drawBackend.value === 'civitai' ? 1024 : 2048
})

// 计算是否可以提交
const canSubmit = computed(() => {
  const isValidSize = formData.value.width <= maxWidthHeight.value && 
                      formData.value.height <= maxWidthHeight.value &&
                      formData.value.width >= 64 && 
                      formData.value.height >= 64
  return formData.value.model.trim() !== '' && 
         formData.value.prompt.trim() !== '' &&
         isValidSize
})

// 加载绘图后端设置
const loadDrawSettings = async () => {
  try {
    const response = await api.get('/settings/draw')
    const settings = (response as any)?.data || response
    drawBackend.value = settings?.backend || 'civitai'
  } catch (error) {
    console.error('加载绘图设置失败:', error)
    drawBackend.value = 'civitai'
  }
}

// 判断模型是否可用（Civitai 后端时所有模型都可用）
const isModelAvailable = (model: any) => {
  if (drawBackend.value === 'civitai') {
    return true
  }
  return model.available !== false
}

// 加载模型列表
const loadModels = async () => {
  loadingModels.value = true
  try {
    const data = await api.get('/model-meta/checkpoint')
    models.value = Array.isArray(data) ? data : []
    
    // 自动选择第一个可用的模型
    if (models.value.length > 0 && !formData.value.model) {
      const availableModel = models.value.find(m => isModelAvailable(m))
      if (availableModel) {
        formData.value.model = availableModel.version_name
      } else if (models.value.length > 0) {
        formData.value.model = models.value[0].version_name
      }
    }
  } catch (error: any) {
    console.error('加载模型列表失败:', error)
    models.value = []
  } finally {
    loadingModels.value = false
  }
}

// 加载 LoRA 列表
const loadLoras = async () => {
  loadingLoras.value = true
  try {
    const data = await api.get('/model-meta/loras')
    availableLoras.value = Array.isArray(data) ? data : []
  } catch (error: any) {
    console.error('加载 LoRA 列表失败:', error)
    availableLoras.value = []
  } finally {
    loadingLoras.value = false
  }
}

// 添加 LoRA 行
const addLoraRow = () => {
  loras.value.push({
    name: '',
    weight: 1.0
  })
}

// 删除 LoRA
const removeLora = (index: number) => {
  loras.value.splice(index, 1)
}

// AI 生成参数
const generateWithAI = async () => {
  emit('generate-params')
}

// 从剪切板粘贴参数
const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (!text.trim()) {
      emit('paste-params', { error: '剪切板为空' })
      return
    }
    
    // 解析 JSON
    let params: any
    try {
      params = JSON.parse(text)
    } catch (error) {
      emit('paste-params', { error: '剪切板内容不是有效的 JSON 格式' })
      return
    }
    
    // 填充表单数据
    if (params.model) {
      formData.value.model = params.model
    }
    
    if (params.prompt) {
      formData.value.prompt = params.prompt
    }
    
    if (params.negative_prompt !== undefined) {
      formData.value.negative_prompt = params.negative_prompt || ''
    }
    
    // 处理采样器字段（API 使用 sampler_name，表单使用 sampler）
    if (params.sampler_name) {
      formData.value.sampler = params.sampler_name
    } else if (params.sampler) {
      formData.value.sampler = params.sampler
    }
    
    if (params.steps !== undefined) {
      formData.value.steps = params.steps
    }
    
    if (params.cfg_scale !== undefined) {
      formData.value.cfg_scale = params.cfg_scale
    }
    
    if (params.width !== undefined) {
      const width = params.width
      if (width > 1024) {
        formData.value.width = 1024
        showToast(`宽度已从 ${width} 调整为 1024`, 'info')
      } else {
        formData.value.width = width
      }
    }
    
    if (params.height !== undefined) {
      const height = params.height
      if (height > 1024) {
        formData.value.height = 1024
        showToast(`高度已从 ${height} 调整为 1024`, 'info')
      } else {
        formData.value.height = height
      }
    }
    
    if (params.seed !== undefined) {
      formData.value.seed = params.seed
    }
    
    if (params.clip_skip !== undefined) {
      formData.value.clip_skip = params.clip_skip
    }
    
    if (params.vae !== undefined) {
      formData.value.vae = params.vae || ''
    }
    
    // 处理 LoRA
    if (params.loras && typeof params.loras === 'object') {
      loras.value = []
      for (const [name, weight] of Object.entries(params.loras)) {
        if (name && typeof weight === 'number') {
          loras.value.push({
            name: name,
            weight: weight
          })
        }
      }
    }
    
    emit('paste-params', params)
  } catch (error: any) {
    if (error.name === 'NotAllowedError') {
      emit('paste-params', { error: '需要剪贴板访问权限' })
    } else {
      emit('paste-params', { error: error.message || '未知错误' })
    }
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    name: '',
    desc: '',
    model: '',
    prompt: '',
    negative_prompt: 'worst quality, lowres, bad anatomy, extra fingers, deformed, blurry',
    sampler: 'DPM++ 2M Karras',
    steps: 30,
    cfg_scale: 7.0,
    width: 1024,
    height: 1024,
    seed: -1,
    clip_skip: 2,
    vae: '',
    batch_size: 1
  }
  loras.value = []
  showAdditionalInfo.value = true // 重置附加信息显示状态
}

// 提交处理（由父组件调用）
const handleSubmit = () => {
  // 验证宽高限制
  if (formData.value.width > maxWidthHeight.value || formData.value.height > maxWidthHeight.value) {
    showToast(`宽高超过限制！使用 ${drawBackend.value === 'civitai' ? 'Civitai' : 'SD-Forge'} 后端时，最大尺寸为 ${maxWidthHeight.value}x${maxWidthHeight.value}`, 'error')
    return
  }
  
  if (formData.value.width < 64 || formData.value.height < 64) {
    showToast('宽高必须大于等于 64', 'error')
    return
  }
  
  // 构建 LoRA 字典
  const lorasDict: Record<string, number> = {}
  loras.value.forEach(lora => {
    if (lora.name && lora.weight) {
      lorasDict[lora.name] = lora.weight
    }
  })
  
  // 合并附加信息到任务描述（只有在显示附加信息时才合并）
  let finalDesc = formData.value.desc || ''
  if (props.additionalInfo && showAdditionalInfo.value) {
    if (finalDesc) {
      finalDesc = `${finalDesc}\n\n${props.additionalInfo}`
    } else {
      finalDesc = props.additionalInfo
    }
  }
  
  emit('submit', {
    name: formData.value.name || undefined,
    desc: finalDesc || undefined,
    model: formData.value.model,
    prompt: formData.value.prompt,
    negative_prompt: formData.value.negative_prompt,
    sampler_name: formData.value.sampler,
    steps: formData.value.steps,
    cfg_scale: formData.value.cfg_scale,
    width: formData.value.width,
    height: formData.value.height,
    seed: formData.value.seed,
    clip_skip: formData.value.clip_skip || undefined,
    vae: formData.value.vae || undefined,
    loras: lorasDict,
    batch_size: formData.value.batch_size || 1
  })
}

// 暴露表单数据和方法给父组件
defineExpose({
  formData,
  loras,
  generateWithAI,
  pasteFromClipboard,
  loadDrawSettings,
  loadModels,
  loadLoras,
  resetForm,
  handleSubmit,
  canSubmit,
  addLoraRow
})

onMounted(async () => {
  await loadDrawSettings()
  await loadModels()
  await loadLoras()
})

watch(() => drawBackend.value, () => {
  loadModels()
})

// 当 additionalInfo prop 变化时，重置显示状态
watch(() => props.additionalInfo, (newVal) => {
  // 如果有新的附加信息，显示它；如果没有，隐藏
  showAdditionalInfo.value = !!newVal
}, { immediate: true })

</script>

