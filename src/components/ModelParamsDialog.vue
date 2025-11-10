<template>
  <Teleport to="body">
    <div
      v-if="params"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="close"
    >
      <div
        :class="[
          'w-full max-w-2xl max-h-[90vh] rounded-lg shadow-xl flex flex-col',
          'mx-4 md:mx-0', // 移动端添加左右边距
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 标题栏 -->
        <div
          :class="[
            'flex items-center justify-between border-b',
            'p-3 md:p-4', // 移动端使用更小的内边距
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <h2
            :class="[
              'text-lg md:text-xl font-bold', // 移动端使用更小的字体
              isDark ? 'text-white' : 'text-gray-900'
            ]"
          >
            {{ title }}
          </h2>
          <div class="flex items-center gap-2">
            <!-- 复制参数按钮 -->
            <button
              @click="copyParams"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-300'
                  : 'hover:bg-gray-100 text-gray-600'
              ]"
              title="复制参数（JSON）"
            >
              <ClipboardIcon class="w-5 h-5" />
            </button>
            <!-- 关闭按钮 -->
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
        <div class="flex-1 overflow-y-auto p-4 md:p-6">
          <div class="space-y-4">
            <!-- Job ID（如果提供） -->
            <div v-if="jobId">
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                Job ID
              </label>
              <div class="flex items-center gap-2">
                <div :class="['flex-1 px-3 py-2 rounded border font-mono text-sm', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                  {{ jobId }}
                </div>
                <button
                  @click="copyJobId"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    isDark
                      ? 'hover:bg-gray-700 text-gray-300'
                      : 'hover:bg-gray-100 text-gray-600'
                  ]"
                  title="复制 Job ID"
                >
                  <ClipboardIcon class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- 基础模型 -->
            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                基础模型
              </label>
              <div :class="['px-3 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                {{ params.model || '无' }}
              </div>
            </div>

            <!-- 正面提示词 -->
            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                正面提示词
              </label>
              <div :class="['px-3 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                {{ params.prompt || '无' }}
              </div>
            </div>

            <!-- 负面提示词 -->
            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                负面提示词
              </label>
              <div :class="['px-3 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                {{ params.negative_prompt || '无' }}
              </div>
            </div>

            <!-- 生成参数 -->
            <div>
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                生成参数
              </label>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">CFG Scale</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.cfg_scale ?? '无' }}
                  </div>
                </div>
                <div>
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">采样器</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.sampler || params.sampler_name || '无' }}
                  </div>
                </div>
                <div>
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">步数</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.steps ?? '无' }}
                  </div>
                </div>
                <div>
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">种子</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.seed ?? '无' }}
                  </div>
                </div>
                <div>
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">尺寸</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.width && params.height ? `${params.width}×${params.height}` : '无' }}
                  </div>
                </div>
                <div v-if="params.clip_skip">
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">CLIP Skip</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.clip_skip }}
                  </div>
                </div>
                <div v-if="params.vae">
                  <span :class="['text-xs text-gray-500', isDark ? 'text-gray-400' : 'text-gray-600']">VAE</span>
                  <div :class="['px-3 py-2 rounded border mt-1', isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-300 text-gray-900']">
                    {{ params.vae }}
                  </div>
                </div>
              </div>
            </div>

            <!-- LoRA 配置 -->
            <div v-if="params.loras !== undefined && params.loras !== null">
              <label :class="['block text-sm font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                LoRA 配置
              </label>
              <div v-if="params.loras && Object.keys(params.loras).length > 0" class="space-y-2">
                <div
                  v-for="(weight, name) in params.loras"
                  :key="name"
                  :class="['px-3 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-300']"
                >
                  <div class="flex items-center justify-between">
                    <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-900']">{{ name }}</span>
                    <span :class="['text-sm font-semibold', isDark ? 'text-gray-400' : 'text-gray-600']">{{ weight }}</span>
                  </div>
                </div>
              </div>
              <div v-else :class="['px-3 py-2 rounded border', isDark ? 'bg-gray-700 border-gray-600 text-gray-400' : 'bg-gray-50 border-gray-300 text-gray-500']">
                <span class="text-sm">无 LoRA</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { XMarkIcon, ClipboardIcon } from '@heroicons/vue/24/outline'
import { showToast } from '../utils/toast'

export interface DrawParams {
  model?: string
  prompt?: string
  negative_prompt?: string
  sampler?: string
  sampler_name?: string
  steps?: number
  cfg_scale?: number
  seed?: number
  width?: number
  height?: number
  clip_skip?: number
  vae?: string
  loras?: Record<string, number>
}

interface Props {
  params: DrawParams | null
  title?: string  // 可自定义标题
  jobId?: string  // Job ID（可选）
}

const props = withDefaults(defineProps<Props>(), {
  title: '生成参数'
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 复制 Job ID 到剪贴板
const copyJobId = async () => {
  if (!props.jobId) return
  
  try {
    await navigator.clipboard.writeText(props.jobId)
    showToast('Job ID 已复制到剪贴板', 'success')
  } catch (error) {
    console.error('复制失败:', error)
    showToast('复制失败，请重试', 'error')
  }
}

// 复制参数到剪贴板
const copyParams = async () => {
  if (!props.params) return
  
  try {
    // 构建符合 API 端点格式的参数对象
    // 参考: POST /draw/generate
    // 不包括 project_id, batch_id, save_images
    const apiParams: Record<string, any> = {}
    
    // 必填字段
    if (props.params.model) apiParams.model = props.params.model
    if (props.params.prompt) apiParams.prompt = props.params.prompt
    
    // 可选字段（只包含有值的）
    if (props.params.negative_prompt) apiParams.negative_prompt = props.params.negative_prompt
    else apiParams.negative_prompt = ""
    
    // 统一采样器字段名（API 使用 sampler_name）
    if (props.params.sampler) apiParams.sampler_name = props.params.sampler
    else if (props.params.sampler_name) apiParams.sampler_name = props.params.sampler_name
    else apiParams.sampler_name = "DPM++ 2M Karras"  // 默认值
    
    if (props.params.steps !== undefined) apiParams.steps = props.params.steps
    else apiParams.steps = 30  // 默认值
    
    if (props.params.cfg_scale !== undefined) apiParams.cfg_scale = props.params.cfg_scale
    else apiParams.cfg_scale = 7.0  // 默认值
    
    if (props.params.seed !== undefined) apiParams.seed = props.params.seed
    else apiParams.seed = -1  // 默认值
    
    if (props.params.width !== undefined) apiParams.width = props.params.width
    else apiParams.width = 1024  // 默认值
    
    if (props.params.height !== undefined) apiParams.height = props.params.height
    else apiParams.height = 1024  // 默认值
    
    if (props.params.clip_skip !== undefined) apiParams.clip_skip = props.params.clip_skip
    if (props.params.vae) apiParams.vae = props.params.vae
    if (props.params.loras && Object.keys(props.params.loras).length > 0) {
      apiParams.loras = props.params.loras
    }
    
    const jsonString = JSON.stringify(apiParams, null, 2)
    await navigator.clipboard.writeText(jsonString)
    
    // 使用 toast 显示成功提示
    showToast('参数已复制到剪贴板', 'success')
  } catch (error) {
    console.error('复制失败:', error)
    showToast('复制失败，请重试', 'error')
  }
}

const close = () => {
  emit('close')
}
</script>


