<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="close"
    >
      <div
        :class="[
          'w-full max-w-3xl max-h-[90vh] rounded-lg shadow-xl flex flex-col',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 标题栏 -->
        <div 
          :class="[
            'flex items-center justify-between p-4 border-b',
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <h2 
            :class="[
              'text-xl font-bold',
              isDark ? 'text-white' : 'text-gray-900'
            ]"
          >
            为 {{ actorName }} 生成立绘
          </h2>
          <div class="flex items-center gap-2">
            <!-- AI 生成参数按钮 -->
            <button
              @click="generateWithAI"
              :disabled="generatingParams"
              :class="[
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
                generatingParams
                  ? isDark 
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : isDark
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-purple-500 hover:bg-purple-600 text-white'
              ]"
              title="使用 AI 自动生成绘图参数"
            >
              <svg v-if="!generatingParams" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <div v-else class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              {{ generatingParams ? 'AI 生成中...' : 'AI 生成参数' }}
            </button>
            <!-- 从剪切板粘贴参数按钮 -->
            <button
              @click="pasteFromClipboard"
              :class="[
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
                isDark
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              ]"
              title="从剪切板粘贴生成参数"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              粘贴参数
            </button>
            <button
              @click="close"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-300'
                  : 'hover:bg-gray-100 text-gray-600'
              ]"
              title="关闭"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-4">
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
                    :value="model.filename"
                    :disabled="!model.available"
                  >
                    {{ model.name }} {{ !model.available ? '(不可用)' : '' }}
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
                </label>
                <input
                  v-model.number="formData.width"
                  type="number"
                  min="64"
                  max="2048"
                  step="64"
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
                  高度
                </label>
                <input
                  v-model.number="formData.height"
                  type="number"
                  min="64"
                  max="2048"
                  step="64"
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

            <!-- 立绘标题和描述 -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                  立绘标题 *
                </label>
                <input
                  v-model="portraitTitle"
                  type="text"
                  placeholder="例如：角色立绘、战斗姿态"
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
                  立绘描述
                </label>
                <input
                  v-model="portraitDesc"
                  type="text"
                  placeholder="可选，描述这张立绘的特点"
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
                      :value="loraOption.filename"
                      :disabled="!loraOption.available"
                    >
                      {{ loraOption.name }} {{ !loraOption.available ? '(不可用)' : '' }}
                    </option>
                  </select>
                  <input
                    v-model.number="lora.weight"
                    type="number"
                    min="0"
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
          </div>
        </div>

        <!-- 底部按钮 -->
        <div 
          :class="[
            'flex items-center justify-end gap-3 p-4 border-t',
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <button
            @click="close"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            ]"
          >
            取消
          </button>
          <button
            @click="generate"
            :disabled="!canGenerate || generating"
            :class="[
              'px-6 py-2 rounded-lg font-medium transition-colors',
              !canGenerate || generating
                ? isDark
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            ]"
          >
            {{ generating ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import api from '../api'
import { showToast } from '../utils/toast'

interface Props {
  show: boolean
  actorName: string
  actorId: string
  projectId: string
}

interface LoraItem {
  name: string
  weight: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'generated'): void
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

// 表单数据
const formData = ref({
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
  vae: ''
})

const loras = ref<LoraItem[]>([])

// 立绘标题和描述
const portraitTitle = ref('')
const portraitDesc = ref('')

// 可用模型和 LoRA
const models = ref<any[]>([])
const availableLoras = ref<any[]>([])
const loadingModels = ref(false)
const loadingLoras = ref(false)
const generatingParams = ref(false)
const generating = ref(false)

// 是否可以生成
const canGenerate = computed(() => {
  return formData.value.model && formData.value.prompt.trim() && portraitTitle.value.trim()
})

// 加载模型列表
const loadModels = async () => {
  loadingModels.value = true
  try {
    // 从模型元数据服务获取模型列表
    const data = await api.get('/model-meta/checkpoint')
    models.value = Array.isArray(data) ? data : []
    
    // 自动选择第一个可用的模型
    if (models.value.length > 0 && !formData.value.model) {
      const availableModel = models.value.find(m => m.available)
      if (availableModel) {
        formData.value.model = availableModel.filename
      } else if (models.value.length > 0) {
        // 如果没有可用的，选择第一个
        formData.value.model = models.value[0].filename
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
    // 从模型元数据服务获取 LoRA 列表
    const data = await api.get('/model-meta/loras')
    availableLoras.value = Array.isArray(data) ? data : []
    
    // 统计可用和不可用的 LoRA
    const availableCount = availableLoras.value.filter(l => l.available).length
    const unavailableCount = availableLoras.value.length - availableCount
    
    console.log(`加载了 ${availableLoras.value.length} 个 LoRA（${availableCount} 可用，${unavailableCount} 不可用）`)
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
  generatingParams.value = true
  try {
    // TODO: 调用后端 API 生成参数
    // 暂时使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    formData.value.prompt = `1girl, solo, ${props.actorName}, beautiful detailed eyes, beautiful detailed face, high quality, masterpiece`
    
  } catch (error) {
    console.error('AI 生成参数失败:', error)
  } finally {
    generatingParams.value = false
  }
}

// 从剪切板粘贴参数
const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (!text.trim()) {
      showToast('剪切板为空', 'error')
      return
    }
    
    // 解析 JSON
    let params: any
    try {
      params = JSON.parse(text)
    } catch (error) {
      showToast('剪切板内容不是有效的 JSON 格式', 'error')
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
      formData.value.width = params.width
    }
    
    if (params.height !== undefined) {
      formData.value.height = params.height
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
      // 清空现有的 LoRA
      loras.value = []
      
      // 添加新的 LoRA
      for (const [name, weight] of Object.entries(params.loras)) {
        if (name && typeof weight === 'number') {
          loras.value.push({
            name: name,
            weight: weight
          })
        }
      }
    }
    
    showToast('参数已从剪切板粘贴', 'success')
  } catch (error: any) {
    console.error('粘贴参数失败:', error)
    if (error.name === 'NotAllowedError') {
      showToast('需要剪贴板访问权限', 'error')
    } else {
      showToast('粘贴参数失败: ' + (error.message || '未知错误'), 'error')
    }
  }
}

// 生成立绘
const generate = async () => {
  if (!canGenerate.value) return
  
  generating.value = true
  try {
    // 构建 LoRA 字典
    const lorasDict: Record<string, number> = {}
    loras.value.forEach(lora => {
      if (lora.name && lora.weight) {
        lorasDict[lora.name] = lora.weight
      }
    })
    
    // 步骤1: 调用生成 API，获取 job_id
    showToast('正在创建绘图任务...', 'info')
    const result = await api.post('/draw', null, {
      params: {
        project_id: props.projectId,
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
        loras: Object.keys(lorasDict).length > 0 ? JSON.stringify(lorasDict) : undefined
      }
    })
    
    if (!result?.job_id) {
      throw new Error('创建绘图任务失败：未返回 job_id')
    }
    
    // 步骤2: 从 job_id 添加立绘到 actor
    showToast('正在添加立绘任务...', 'info')
    await api.post(`/actor/${props.actorId}/add_portrait_from_job`, null, {
      params: {
        project_id: props.projectId,
        job_id: result.job_id,
        title: portraitTitle.value.trim(),
        desc: portraitDesc.value.trim() || undefined
      }
    })
    
    showToast('立绘生成任务已提交，完成后将自动添加到角色', 'success')
    
    emit('generated')
    close()
  } catch (error: any) {
    console.error('生成立绘失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    showToast('生成立绘失败: ' + errorMessage, 'error')
  } finally {
    generating.value = false
  }
}

const close = () => {
  // 重置表单
  portraitTitle.value = ''
  portraitDesc.value = ''
  formData.value = {
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
    vae: ''
  }
  loras.value = []
  emit('close')
}

// 监听对话框显示状态
watch(() => props.show, (newVal) => {
  if (newVal) {
    loadModels()
    loadLoras()
    // 初始化标题（如果为空）
    if (!portraitTitle.value) {
      portraitTitle.value = `${props.actorName} - 立绘`
    }
  }
})

onMounted(() => {
  if (props.show) {
    loadModels()
    loadLoras()
    // 初始化标题（如果为空）
    if (!portraitTitle.value) {
      portraitTitle.value = `${props.actorName} - 立绘`
    }
  }
})
</script>

