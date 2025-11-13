<template>
  <Teleport to="body">
    <div
      v-if="model"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="close"
    >
      <div
        :class="[
          'w-full max-w-4xl max-h-[90vh] rounded-lg shadow-xl flex flex-col',
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
            {{ versionName }}
          </h2>
          <div class="flex items-center gap-2">
            <!-- 重置按钮 -->
            <button
              @click.stop="handleReset"
              :disabled="resetting"
              :class="[
                'p-2 rounded-lg transition-colors',
                resetting
                  ? 'opacity-50 cursor-not-allowed'
                  : isDark ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
              ]"
              title="重置：从 Civitai 重新下载元数据和图像"
            >
              <ArrowPathIcon v-if="!resetting" class="w-5 h-5" />
              <div v-else class="animate-spin rounded-full h-5 w-5 border-b-2" 
                   :class="isDark ? 'border-blue-400' : 'border-blue-600'"></div>
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
          <div class="space-y-6">
            <!-- 预览图展示区域 -->
            <div class="relative">
              <!-- 左右切换按钮 -->
              <div 
                v-if="exampleCount > 1"
                class="absolute inset-0 flex items-center justify-between pointer-events-none z-10"
              >
                <button
                  @click="prevExample"
                  :disabled="currentExampleIndex === 0"
                  :class="[
                    'pointer-events-auto p-2 rounded-full transition-colors ml-2',
                    currentExampleIndex === 0
                      ? 'bg-gray-900 bg-opacity-30 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                        : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="上一张"
                >
                  <ChevronLeftIcon class="w-6 h-6" />
                </button>
                <button
                  @click="nextExample"
                  :disabled="currentExampleIndex === exampleCount - 1"
                  :class="[
                    'pointer-events-auto p-2 rounded-full transition-colors mr-2',
                    currentExampleIndex === exampleCount - 1
                      ? 'bg-gray-900 bg-opacity-30 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                        : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="下一张"
                >
                  <ChevronRightIcon class="w-6 h-6" />
                </button>
              </div>
              
              <!-- 生成参数按钮组 -->
              <div 
                v-if="currentExample && currentExample.draw_args"
                class="absolute top-2 right-2 z-10 flex gap-2"
              >
                <!-- 复制生成参数按钮 -->
                <button
                  @click.stop="copyParams"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    isDark
                      ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                      : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="复制生成参数"
                >
                  <ClipboardIcon class="w-5 h-5" />
                </button>
                <!-- 查看生成参数按钮 -->
                <button
                  @click.stop="showParamsDialog = true"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    isDark
                      ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                      : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="查看生成参数"
                >
                  <InformationCircleIcon class="w-5 h-5" />
                </button>
              </div>
              
              <div 
                v-if="previewImageUrl && !imageLoading && !privacyMode"
                :class="[
                  'w-full h-96 rounded-lg overflow-hidden border flex items-center justify-center cursor-pointer',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
                @click="openImageGallery"
              >
                <img
                  :src="previewImageUrl"
                  :alt="model.name"
                  class="w-full h-full object-contain"
                  @error="handleImageError"
                />
              </div>
              <div 
                v-else-if="imageLoading && !privacyMode"
                :class="[
                  'w-full h-96 rounded-lg border flex flex-col items-center justify-center',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
              >
                <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
                     :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
                <span :class="['text-sm mt-4', isDark ? 'text-gray-500' : 'text-gray-500']">
                  加载中...
                </span>
              </div>
              <div 
                v-else
                :class="[
                  'w-full h-96 rounded-lg border flex flex-col items-center justify-center',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
              >
                <PhotoIcon class="w-16 h-16 mb-2" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
                <span :class="['text-sm', isDark ? 'text-gray-500' : 'text-gray-500']">
                  {{ privacyMode ? '隐私模式已启用' : '暂无预览图' }}
                </span>
              </div>
            </div>

            <!-- 基本信息 -->
            <div>
              <h3 
                :class="[
                  'text-lg font-semibold mb-3',
                  isDark ? 'text-white' : 'text-gray-900'
                ]"
              >
                基本信息
              </h3>
              <div class="space-y-3">
                <!-- 版本名称 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    版本名称:
                  </span>
                  <span :class="['text-sm flex-1 font-mono', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ versionName }}
                  </span>
                </div>

                <!-- 模型类型 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    模型类型:
                  </span>
                  <span :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ model.type }}
                  </span>
                </div>

                <!-- 生态系统 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    生态系统:
                  </span>
                  <span :class="['text-sm flex-1 uppercase', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ model.ecosystem }}
                  </span>
                </div>

                <!-- 基础模型 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    基础模型:
                  </span>
                  <span :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ model.base_model || '未知' }}
                  </span>
                </div>

                <!-- AIR 标识符 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    AIR 标识符:
                  </span>
                  <span :class="['text-sm flex-1 font-mono break-all', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ model.air || '无' }}
                  </span>
                </div>

                <!-- 网页链接 -->
                <div v-if="model.web_page_url" class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    网页链接:
                  </span>
                  <a
                    :href="model.web_page_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    :class="[
                      'text-sm flex-1 text-blue-500 hover:text-blue-600 underline break-all',
                      isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'
                    ]"
                  >
                    {{ model.web_page_url.length > 60 ? model.web_page_url.substring(0, 57) + '...' : model.web_page_url }}
                  </a>
                </div>

                <!-- 触发词 -->
                <div v-if="model.trained_words && model.trained_words.length > 0" class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    触发词:
                  </span>
                  <span :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ model.trained_words.join(', ') }}
                  </span>
                </div>

                <!-- 说明 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    说明:
                  </span>
                  <div class="flex-1 flex items-start gap-2">
                    <template v-if="isEditingDesc">
                      <textarea
                        v-model="editingDesc"
                        rows="3"
                        :class="[
                          'flex-1 px-2 py-1 rounded border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
                          isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
                        ]"
                        @keydown.ctrl.enter="saveDesc"
                        @keydown.meta.enter="saveDesc"
                        @keydown.esc="cancelEditDesc"
                        ref="descInputRef"
                      />
                      <div class="flex flex-col gap-1">
                        <button
                          @click="saveDesc"
                          :class="['text-green-500 hover:text-green-600']"
                          title="保存"
                        >
                          ✓
                        </button>
                        <button
                          @click="cancelEditDesc"
                          :class="['text-red-500 hover:text-red-600']"
                          title="取消"
                        >
                          ✗
                        </button>
                      </div>
                    </template>
                    <template v-else>
                      <span v-if="model.desc" :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        {{ model.desc }}
                      </span>
                      <span v-else :class="['text-sm flex-1', isDark ? 'text-gray-500' : 'text-gray-400']">
                        无
                      </span>
                      <button
                        @click="startEditDesc"
                        :class="[
                          'p-1 rounded hover:bg-gray-700 transition-colors',
                          isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
                        ]"
                        title="编辑"
                      >
                        <PencilIcon class="w-4 h-4" />
                      </button>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 生成参数对话框 -->
    <ModelParamsDialog
      v-if="showParamsDialog"
      :params="currentExample?.draw_args || null"
      @close="showParamsDialog = false"
    />
    
    <!-- 大图显示对话框 -->
    <ImageGalleryDialog
      :version-id="props.model?.version_id"
      :filenames="allExampleFilenames"
      :initial-index="galleryInitialIndex"
      :visible="showImageGallery"
      @close="showImageGallery = false"
    />
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :show="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      :items="confirmDialog.items"
      :warning-text="confirmDialog.warningText"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.show = false"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { 
  XMarkIcon, 
  PhotoIcon,
  PencilIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  ClipboardIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import { getImageUrl } from '../utils/imageUtils'
import { showToast } from '../utils/toast'
import api from '../api'
import ModelParamsDialog from './ModelParamsDialog.vue'
import ImageGalleryDialog from './ImageGalleryDialog.vue'
import ConfirmDialog from './ConfirmDialog.vue'

interface ModelMeta {
  model_id: number
  version_id: number
  filename: string
  name: string
  version: string
  version_name: string
  type: 'checkpoint' | 'lora' | 'vae'
  ecosystem: 'sd1' | 'sd2' | 'sdxl'
  base_model: string | null
  desc?: string | null
  trained_words?: string[]
  examples: any[]
  web_page_url: string | null
  air: string
}

interface Props {
  model: ModelMeta | null
  privacyMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  privacyMode: false
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'model-updated'): void  // 模型更新后触发，用于刷新列表
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 计算 version_name
const versionName = computed(() => {
  if (!props.model) return ''
  if (props.model.version_name) {
    return props.model.version_name
  }
  if (props.model.name && props.model.version) {
    return `${props.model.name}-${props.model.version}`
  }
  return props.model.name || props.model.version || ''
})

// 当前example索引
const currentExampleIndex = ref(0)
const showParamsDialog = ref(false)
const showImageGallery = ref(false)
const galleryInitialIndex = ref(0)

// 确认对话框状态
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  type: 'default' as 'default' | 'danger',
  items: [] as string[],
  warningText: '',
  onConfirm: () => {}
})

// 计算example数量
const exampleCount = computed(() => {
  return props.model?.examples?.length || 0
})

// 当前example
const currentExample = computed(() => {
  if (!props.model || !props.model.examples || currentExampleIndex.value >= props.model.examples.length) {
    return null
  }
  return props.model.examples[currentExampleIndex.value]
})

// 所有example的文件名数组（用于大图显示）
const allExampleFilenames = computed(() => {
  if (!props.model || !props.model.examples) return []
  return props.model.examples
    .map(ex => ex?.filename)
    .filter((filename): filename is string => filename !== undefined && filename !== null)
})

// 图片 URL
const previewImageUrl = ref<string | null>(null)
const imageLoading = ref(true)

// 加载图片 URL
const loadImageUrl = async () => {
  if (!currentExample.value || !props.model) {
    imageLoading.value = false
    previewImageUrl.value = null
    return
  }

  // 获取当前示例的 filename
  const filename = currentExample.value.filename
  if (!filename) {
    imageLoading.value = false
    previewImageUrl.value = null
    return
  }

  imageLoading.value = true
  // getImageUrl 已经处理了所有错误（包括 404），不会抛出错误，直接返回 null 表示图片不存在
  previewImageUrl.value = await getImageUrl(
    props.model.version_id,
    filename
  )
  imageLoading.value = false
}

// 切换到上一张example
const prevExample = () => {
  if (currentExampleIndex.value > 0) {
    currentExampleIndex.value--
    loadImageUrl()
  }
}

// 切换到下一张example
const nextExample = () => {
  if (currentExampleIndex.value < exampleCount.value - 1) {
    currentExampleIndex.value++
    loadImageUrl()
  }
}

// 监听模型变化，重新加载图片
watch(() => props.model, () => {
  if (props.model) {
    currentExampleIndex.value = 0
    showParamsDialog.value = false  // 切换模型时重置生成参数对话框状态
    editingDesc.value = ''  // 切换模型时重置编辑状态
    isEditingDesc.value = false
    loadImageUrl()
  }
}, { immediate: true })

// 监听example索引变化
watch(() => currentExampleIndex.value, () => {
  loadImageUrl()
})

const handleImageError = () => {
  previewImageUrl.value = null
  imageLoading.value = false
}

// 打开大图显示
const openImageGallery = () => {
  if (allExampleFilenames.value.length > 0) {
    // 设置初始索引为当前显示的example索引
    galleryInitialIndex.value = currentExampleIndex.value
    showImageGallery.value = true
  }
}

// 复制生成参数到剪贴板
const copyParams = async () => {
  if (!currentExample.value?.draw_args) return
  
  try {
    const params = currentExample.value.draw_args
    
    // 构建符合 API 端点格式的参数对象
    // 参考: POST /draw/generate
    // 不包括 project_id, batch_id, save_images
    const apiParams: Record<string, any> = {}
    
    // 必填字段
    if (params.model) apiParams.model = params.model
    if (params.prompt) apiParams.prompt = params.prompt
    
    // 可选字段（只包含有值的）
    if (params.negative_prompt) apiParams.negative_prompt = params.negative_prompt
    else apiParams.negative_prompt = ""
    
    // 统一采样器字段名（API 使用 sampler_name）
    if (params.sampler) apiParams.sampler_name = params.sampler
    else if (params.sampler_name) apiParams.sampler_name = params.sampler_name
    else apiParams.sampler_name = "DPM++ 2M Karras"  // 默认值
    
    if (params.steps !== undefined) apiParams.steps = params.steps
    else apiParams.steps = 30  // 默认值
    
    if (params.cfg_scale !== undefined) apiParams.cfg_scale = params.cfg_scale
    else apiParams.cfg_scale = 7.0  // 默认值
    
    if (params.seed !== undefined) apiParams.seed = params.seed
    else apiParams.seed = -1  // 默认值
    
    if (params.width !== undefined) apiParams.width = params.width
    else apiParams.width = 1024  // 默认值
    
    if (params.height !== undefined) apiParams.height = params.height
    else apiParams.height = 1024  // 默认值
    
    if (params.clip_skip !== undefined) apiParams.clip_skip = params.clip_skip
    if (params.vae) apiParams.vae = params.vae
    if (params.loras && Object.keys(params.loras).length > 0) {
      apiParams.loras = params.loras
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

// 编辑说明功能
const editingDesc = ref('')
const isEditingDesc = ref(false)
const descInputRef = ref<HTMLTextAreaElement | null>(null)

const startEditDesc = () => {
  editingDesc.value = props.model?.desc || ''
  isEditingDesc.value = true
  nextTick(() => {
    descInputRef.value?.focus()
  })
}

const saveDesc = async () => {
  if (!props.model) return
  
  try {
    // 调用 API 更新模型说明
    // 注意：api 拦截器已经返回了 response.data，所以 response 直接是数据对象
    const response = await api.patch(`/model-meta/${props.model.version_id}/desc`, { desc: editingDesc.value || null })
    
    // 更新本地数据
    if (props.model) {
      props.model.desc = response.desc
    }
    
    // 显示成功提示
    showToast('说明已保存', 'success')
    
    editingDesc.value = ''
    isEditingDesc.value = false
  } catch (error: any) {
    console.error('保存失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '保存失败'
    showToast(`保存失败: ${errorMsg}`, 'error')
  }
}

const cancelEditDesc = () => {
  editingDesc.value = ''
  isEditingDesc.value = false
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  // 如果对话框没有显示，不处理
  if (!props.model) return
  
  // 如果正在编辑说明，ESC 应该先取消编辑，而不是关闭对话框
  if (isEditingDesc.value) {
    if (event.key === 'Escape') {
      cancelEditDesc()
      event.preventDefault()
    }
    return
  }
  
  // 如果不在编辑状态，ESC 关闭对话框
  if (event.key === 'Escape') {
    close()
    event.preventDefault()
  }
}

// 监听键盘事件
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

const close = () => {
  showParamsDialog.value = false  // 关闭时重置生成参数对话框状态
  emit('close')
}


// 重置模型元数据
const resetting = ref(false)
const handleReset = () => {
  if (!props.model || resetting.value) return
  
  confirmDialog.value = {
    show: true,
    title: '确认重置',
    message: '确定要重置此模型的元数据吗？',
    type: 'default',
    items: ['将从 Civitai 重新下载元数据', '将重新下载所有示例图像'],
    warningText: '',
    onConfirm: async () => {
      confirmDialog.value.show = false
      resetting.value = true
      try {
        showToast('正在重置模型元数据...', 'info')
        
        // 调用重置 API
        const response = await api.post(`/model-meta/${props.model!.version_id}/reset`, null, {
          params: {
            parallel_download: false  // 串行下载，避免并发过多
          }
        })
        const responseData = (response as any)?.data || response
        
        if (responseData?.success) {
          showToast(`重置成功：${responseData.model_name}`, 'success')
          // 触发模型更新事件，让父组件刷新模型列表
          emit('model-updated')
          // 关闭对话框，让用户重新打开查看更新后的数据
          close()
        } else {
          throw new Error('重置失败')
        }
      } catch (error: any) {
        console.error('重置模型失败:', error)
        const errorMsg = error.response?.data?.detail || error.message || '重置失败，请重试'
        showToast(errorMsg, 'error')
      } finally {
        resetting.value = false
      }
    }
  }
}
</script>

