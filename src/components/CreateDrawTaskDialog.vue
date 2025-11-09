<template>
  <DialogRoot :open="show" @update:open="onUpdateOpen">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 z-50" />
      <DialogContent
        :class="[
          'fixed z-50 w-full max-w-3xl max-h-[90vh] rounded-lg shadow-xl flex flex-col top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
          'mx-4 md:mx-0',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <DialogTitle class="sr-only">{{ title }}</DialogTitle>
        <DialogDescription class="sr-only">创建或选择绘图任务，并配置绘图参数</DialogDescription>
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
            <!-- AI 生成参数按钮 -->
            <button
              @click="handleGenerateWithAI"
              :disabled="generatingParams"
              :class="[
                'p-2 rounded-lg transition-colors',
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
              <BoltIcon v-if="!generatingParams" class="w-5 h-5" />
              <div v-else class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            </button>
            <!-- 从剪切板粘贴参数按钮 -->
            <button
              @click="handlePasteFromClipboard"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              ]"
              title="从剪切板粘贴生成参数"
            >
              <ClipboardIcon class="w-5 h-5" />
            </button>
            <!-- 切换到已有任务选择按钮 -->
            <button
              v-if="showSwitchToJobs"
              @click="$emit('switch-to-jobs')"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'bg-orange-600 hover:bg-orange-700 text-white'
                  : 'bg-orange-500 hover:bg-orange-600 text-white'
              ]"
              title="从已有任务选择图像"
            >
              <PhotoIcon class="w-5 h-5" />
            </button>
            <button
              @click="handleClose"
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
        <div class="flex-1 overflow-y-auto no-scrollbar p-4 md:p-6">
          <DrawTaskForm
            ref="drawFormRef"
            :context-info="contextInfo"
            :additional-info="additionalInfo"
            @submit="handleSubmit"
            @generate-params="handleGenerateParams"
            @paste-params="handlePasteParams"
          >
            <!-- 插槽：用于添加额外的字段（如立绘标题和描述） -->
            <template #extra-fields>
              <slot name="extra-fields"></slot>
            </template>
          </DrawTaskForm>
        </div>

        <!-- 底部按钮 -->
        <div 
          :class="[
            'flex items-center justify-end gap-3 border-t',
            'p-3 md:p-4', // 移动端使用更小的内边距
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <button
            @click="handleSubmitClick"
            :disabled="!canSubmit || submitting || generatingParams"
            :class="[
              'w-full px-6 py-2 rounded-lg font-medium transition-colors',
              !canSubmit || submitting || generatingParams
                ? isDark
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            ]"
          >
            {{ submitting ? submitButtonLoadingText : submitButtonText }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { XMarkIcon, BoltIcon, ClipboardIcon, PhotoIcon } from '@heroicons/vue/24/outline'
import api from '../api'
import { showToast } from '../utils/toast'
import DrawTaskForm from './DrawTaskForm.vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription } from 'radix-vue'

interface Props {
  show: boolean
  title?: string
  contextInfo?: string // 用于 AI 生成参数的上下文信息（如角色名称）
  submitButtonText?: string
  submitButtonLoadingText?: string
  showCancel?: boolean
  showSwitchToJobs?: boolean // 是否显示切换到已有任务选择的按钮
  onSubmit?: (data: any) => Promise<void> // 自定义提交处理函数
  initialName?: string // 初始任务名称
  initialDesc?: string // 初始任务描述
  projectId?: string // 项目ID（可选），用于立绘生成时查询角色信息
  additionalInfo?: string // 附加信息（只读，显示在任务描述下方）
}

const props = withDefaults(defineProps<Props>(), {
  title: '新建绘图任务',
  submitButtonText: '创建任务',
  submitButtonLoadingText: '创建中...',
  showCancel: false,
  showSwitchToJobs: false
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
  (e: 'submitted'): void
  (e: 'switch-to-jobs'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const drawFormRef = ref<InstanceType<typeof DrawTaskForm> | null>(null)
const generatingParams = ref(false)
const submitting = ref(false)

const canSubmit = computed(() => {
  return drawFormRef.value?.canSubmit ?? false
})

// AI 生成参数
const handleGenerateWithAI = async () => {
  if (!drawFormRef.value) return
  generatingParams.value = true
  try {
    // 获取当前任务名称和描述
    const name = drawFormRef.value.formData?.name || ''
    const desc = drawFormRef.value.formData?.desc || ''
    
    // 名称允许为空：当为空时使用占位“角色立绘”
    const effectiveName = name.trim() || '角色立绘'
    
    // 调用后端 API 生成参数
    const requestBody: any = {
      name: effectiveName,
      desc: desc || undefined
    }
    
    // 如果是立绘生成（提供了 projectId），传递 project_id 参数
    if (props.projectId) {
      requestBody.project_id = props.projectId
    }
    
    const response = await api.post('/llm/generate-draw-params', requestBody)
    
    // 后端现在直接返回 DrawArgs 对象
    const params = response.data || response
    
    if (params && drawFormRef.value.formData) {
      // 回填所有参数
      drawFormRef.value.formData.model = params.model || ''
      drawFormRef.value.formData.prompt = params.prompt || ''
      drawFormRef.value.formData.negative_prompt = params.negative_prompt || drawFormRef.value.formData.negative_prompt
      // DrawArgs 使用 sampler 字段，不是 sampler_name
      drawFormRef.value.formData.sampler = params.sampler || drawFormRef.value.formData.sampler
      drawFormRef.value.formData.steps = params.steps || drawFormRef.value.formData.steps
      drawFormRef.value.formData.cfg_scale = params.cfg_scale || drawFormRef.value.formData.cfg_scale
      drawFormRef.value.formData.width = params.width || drawFormRef.value.formData.width
      drawFormRef.value.formData.height = params.height || drawFormRef.value.formData.height
      drawFormRef.value.formData.seed = params.seed !== undefined ? params.seed : drawFormRef.value.formData.seed
      if (params.clip_skip !== undefined) {
        drawFormRef.value.formData.clip_skip = params.clip_skip
      }
      if (params.vae) {
        drawFormRef.value.formData.vae = params.vae
      }
      
      // 处理 LoRA
      if (params.loras && typeof params.loras === 'object') {
        // 清空现有 LoRA
        if (drawFormRef.value.loras) {
          drawFormRef.value.loras.splice(0)
        }
        // 添加新的 LoRA
        for (const [loraName, weight] of Object.entries(params.loras)) {
          if (drawFormRef.value.addLoraRow) {
            // 添加新行并设置值
            drawFormRef.value.addLoraRow()
            const lastIndex = drawFormRef.value.loras.length - 1
            if (lastIndex >= 0 && drawFormRef.value.loras[lastIndex]) {
              drawFormRef.value.loras[lastIndex].name = loraName
              drawFormRef.value.loras[lastIndex].weight = weight as number
            }
          }
        }
      }
      
      showToast('AI 已生成参数', 'success')
    }
  } catch (error: any) {
    console.error('AI 生成参数失败:', error)
    showToast('AI 生成参数失败: ' + (error.response?.data?.detail || error.message || '未知错误'), 'error')
  } finally {
    generatingParams.value = false
  }
}

// 处理通用组件的 generate-params 事件
const handleGenerateParams = () => {
  handleGenerateWithAI()
}

// 处理通用组件的 paste-params 事件
const handlePasteParams = (result: any) => {
  if (result.error) {
    showToast(result.error, 'error')
  } else {
    showToast('参数已从剪切板粘贴', 'success')
  }
}

// 从剪切板粘贴参数
const handlePasteFromClipboard = async () => {
  if (!drawFormRef.value) return
  await drawFormRef.value.pasteFromClipboard()
}

// 提交表单（由 DrawTaskForm 触发）
const handleSubmit = async (data: any) => {
  // 如果有自定义提交处理函数，使用它
  if (props.onSubmit) {
    submitting.value = true
    try {
      await props.onSubmit(data)
      emit('submitted')
    } catch (error) {
      throw error
    } finally {
      submitting.value = false
    }
  } else {
    // 否则触发 submit 事件，由父组件处理
    emit('submit', data)
  }
}

// 点击提交按钮
const handleSubmitClick = async () => {
  if (!canSubmit.value || submitting.value || !drawFormRef.value) {
    return
  }
  
  // 调用 DrawTaskForm 的 handleSubmit
  drawFormRef.value.handleSubmit()
}

const handleClose = () => {
  // 重置表单
  if (drawFormRef.value) {
    drawFormRef.value.resetForm()
  }
  emit('close')
}

const onUpdateOpen = (v: boolean) => {
  if (!v) {
    handleClose()
  }
}

// 监听初始值变化，确保表单值被设置
watch([() => props.initialName, () => props.initialDesc], async () => {
  if (props.show && drawFormRef.value?.formData) {
    await nextTick()
    if (props.initialName !== undefined) {
      drawFormRef.value.formData.name = props.initialName
    }
    if (props.initialDesc !== undefined) {
      drawFormRef.value.formData.desc = props.initialDesc
    }
  }
}, { immediate: true })

// 监听对话框显示状态
watch(() => props.show, async (newVal) => {
  if (newVal) {
    // 等待下一个 tick，确保 DrawTaskForm 组件已完全初始化
    await nextTick()
    
    if (drawFormRef.value) {
      drawFormRef.value.loadDrawSettings()
      drawFormRef.value.loadModels()
      drawFormRef.value.loadLoras()
      
      // 再次等待，确保表单数据已加载
      await nextTick()
      
      // 设置初始任务名称和描述
      if (props.initialName !== undefined && drawFormRef.value.formData) {
        drawFormRef.value.formData.name = props.initialName
      }
      if (props.initialDesc !== undefined && drawFormRef.value.formData) {
        drawFormRef.value.formData.desc = props.initialDesc
      }
    }
  }
})

onMounted(async () => {
  if (props.show) {
    // 等待下一个 tick，确保 DrawTaskForm 组件已完全初始化
    await nextTick()
    
    if (drawFormRef.value) {
      drawFormRef.value.loadDrawSettings()
      drawFormRef.value.loadModels()
      drawFormRef.value.loadLoras()
      
      // 再次等待，确保表单数据已加载
      await nextTick()
      
      // 设置初始任务名称和描述
      if (props.initialName !== undefined && drawFormRef.value.formData) {
        drawFormRef.value.formData.name = props.initialName
      }
      if (props.initialDesc !== undefined && drawFormRef.value.formData) {
        drawFormRef.value.formData.desc = props.initialDesc
      }
    }
  }
})

</script>

<style scoped>
/* 隐藏滚动条但保持可滚动 */
.no-scrollbar {
  -ms-overflow-style: none; /* IE 和旧版 Edge */
  scrollbar-width: none;    /* Firefox */
}
.no-scrollbar::-webkit-scrollbar {
  display: none;            /* Chrome/Safari/新 Edge */
}
</style>
