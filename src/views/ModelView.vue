<template>
  <div class="space-y-4">
    <!-- 筛选和操作栏 -->
    <div class="flex flex-col md:flex-row md:items-center gap-3">
      <!-- 第一行：生态系统筛选器 -->
      <div class="flex items-center gap-2">
      <select
        v-model="ecosystemFilter"
        :class="[
          'flex-1 px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
          isDark
            ? 'bg-gray-700 border-gray-600 text-white'
            : 'bg-white border-gray-300 text-gray-900'
        ]"
        @change="saveFilters"
      >
        <option value="">生态系统：全部</option>
        <option value="sd1">sd1</option>
        <option value="sd2">sd2</option>
        <option value="sdxl">sdxl</option>
      </select>

        <!-- 清除筛选按钮（移动端显示在第一行） -->
        <button
          v-if="ecosystemFilter || baseModelFilter"
          @click="clearFilters"
          :class="[
            'p-2 rounded-lg transition-colors md:hidden',
            isDark
              ? 'hover:bg-gray-700 text-gray-400'
              : 'hover:bg-gray-100 text-gray-600'
          ]"
          title="清除筛选"
        >
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- 第二行：基础模型筛选器 -->
      <select
        v-model="baseModelFilter"
        :class="[
          'flex-1 px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
          isDark
            ? 'bg-gray-700 border-gray-600 text-white'
            : 'bg-white border-gray-300 text-gray-900'
        ]"
        @change="saveFilters"
      >
        <option value="">基础模型：全部</option>
        <option value="Pony">Pony</option>
        <option value="Illustrious">Illustrious</option>
        <option value="NoobAI">NoobAI</option>
        <option value="SDXL 1.0">SDXL 1.0</option>
        <option value="SD 1.5">SD 1.5</option>
        <option value="Standard">Standard</option>
        <option value="Flux">Flux</option>
        <option value="SD3">SD3</option>
      </select>

      <!-- 清除筛选按钮（桌面端显示） -->
      <button
        v-if="ecosystemFilter || baseModelFilter"
        @click="clearFilters"
        :class="[
          'p-2 rounded-lg transition-colors hidden md:block',
          isDark
            ? 'hover:bg-gray-700 text-gray-400'
            : 'hover:bg-gray-100 text-gray-600'
        ]"
        title="清除筛选"
      >
        <XMarkIcon class="w-5 h-5" />
      </button>

      <!-- 第三行：操作按钮 -->
      <div class="flex items-center gap-1 flex-wrap">
        <!-- 从 Civitai 导入 -->
        <button
          @click="showImportDialog = true"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
          ]"
          title="从 Civitai 导入模型"
        >
          <CloudArrowDownIcon class="w-5 h-5" />
        </button>

        <!-- 导出 AIR -->
        <button
          @click="exportAllAir"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark ? 'hover:bg-gray-700 text-gray-300' : 'hover:bg-gray-100 text-gray-600'
          ]"
          title="导出所有 AIR 到剪贴板"
        >
          <ClipboardDocumentIcon class="w-5 h-5" />
        </button>

        <!-- 清空元数据 -->
        <button
          @click="openClearConfirm"
          :class="[
            'p-2 rounded-lg transition-colors text-red-500',
            isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
          ]"
          title="清空所有模型元数据"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div 
      v-if="loading"
      class="flex justify-center items-center py-12"
    >
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" 
             :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
        <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
          加载中...
        </p>
      </div>
    </div>

    <!-- 内容区域 -->
    <div v-else class="space-y-8">
      <!-- Checkpoint 区域 -->
      <div>
        <h2 
          :class="[
            'text-2xl font-bold mb-4',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          Checkpoint ({{ filteredCheckpoints.length }})
        </h2>
        
        <div 
          v-if="filteredCheckpoints.length === 0"
          :class="[
            'text-center py-8 rounded-lg border',
            isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
          ]"
        >
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
            暂无 Checkpoint 模型
          </p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
          <ModelCard
            v-for="model in filteredCheckpoints"
            :key="model.version_id"
            :model="model"
            :privacy-mode="privacyMode"
            :show-warning="!checkModelFileExists(model)"
            @open-detail="openDetailDialog"
            @context-menu="showModelContextMenu"
            @preference-changed="handlePreferenceChanged"
          />
        </div>
      </div>

      <!-- 分隔线 -->
      <div :class="['border-t-2', isDark ? 'border-gray-700' : 'border-gray-300']"></div>

      <!-- LoRA 区域 -->
      <div>
        <h2 
          :class="[
            'text-2xl font-bold mb-4',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          LoRA ({{ filteredLoras.length }})
        </h2>
        
        <div 
          v-if="filteredLoras.length === 0"
          :class="[
            'text-center py-8 rounded-lg border',
            isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
          ]"
        >
          <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
            暂无 LoRA 模型
          </p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
          <ModelCard
            v-for="model in filteredLoras"
            :key="model.version_id"
            :model="model"
            :privacy-mode="privacyMode"
            :show-warning="!checkModelFileExists(model)"
            @open-detail="openDetailDialog"
            @context-menu="showModelContextMenu"
            @preference-changed="handlePreferenceChanged"
          />
        </div>
      </div>
    </div>

    <!-- 导入对话框 -->
    <Teleport to="body">
      <div
        v-if="showImportDialog"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showImportDialog = false"
      >
        <div
          :class="[
            'w-full max-w-2xl rounded-lg shadow-xl',
            'mx-4 md:mx-0', // 移动端添加左右边距
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
          ]"
          @click.stop
        >
          <!-- 对话框头部 -->
          <div class="flex items-center justify-between border-b p-4 md:p-6"
               :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <h2 :class="['text-lg md:text-xl font-bold', isDark ? 'text-white' : 'text-gray-900']">
              从 Civitai 导入模型
            </h2>
            <button
              @click="showImportDialog = false"
              :class="[
                'p-1 rounded-lg transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-white'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-900'
              ]"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>
          </div>
          
          <!-- 对话框内容 -->
          <div class="p-4 md:p-6">
            <p :class="['text-sm mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
              输入 Civitai 模型 AIR 标识符，自动获取并保存模型元数据
            </p>
            <p :class="['text-xs mb-2 font-bold', isDark ? 'text-gray-400' : 'text-gray-600']">
              支持多行输入，每行一个 AIR，无效行将自动忽略
            </p>
            <p :class="['text-xs mb-4', isDark ? 'text-gray-500' : 'text-gray-500']">
              格式：urn:air:{'{ecosystem}'}:{'{type}'}:civitai:{'{model_id}'}@{'{version_id}'}<br/>
              示例：urn:air:sd1:checkpoint:civitai:348620@390021
            </p>
            
            <!-- 下载图片选项 -->
            <label :class="['flex items-center gap-2 mb-3 cursor-pointer', isDark ? 'text-gray-300' : 'text-gray-700']">
              <input
                type="checkbox"
                v-model="downloadImages"
                :disabled="importing"
                :class="[
                  'w-4 h-4 rounded border-2 transition-all',
                  isDark
                    ? 'border-gray-600 bg-gray-700 checked:bg-blue-600 checked:border-blue-600'
                    : 'border-gray-300 bg-white checked:bg-blue-600 checked:border-blue-600',
                  importing && 'opacity-50 cursor-not-allowed'
                ]"
              />
              <span class="text-sm font-medium">
                同时下载示例图片
              </span>
              <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
                （不勾选则只导入元数据）
              </span>
            </label>
            
            <textarea
              v-model="importAirInput"
              rows="6"
              placeholder="每行一个 AIR..."
              :disabled="importing"
              :class="[
                'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                isDark
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
                importing && 'opacity-50 cursor-not-allowed'
              ]"
            ></textarea>
            
            <!-- 进度条 -->
            <div v-if="importing" class="mt-4">
              <div class="flex justify-between items-center mb-2">
                <span :class="['text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                  进度: {{ importProgress.current }} / {{ importProgress.total }}
                </span>
                <span :class="['text-sm font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">
                  {{ importProgress.percentage }}%
                </span>
              </div>
              <div 
                :class="[
                  'w-full h-2 rounded-full overflow-hidden',
                  isDark ? 'bg-gray-700' : 'bg-gray-200'
                ]"
              >
                <div
                  :class="[
                    'h-full transition-all duration-300',
                    importProgress.percentage === 100 ? 'bg-green-500' : 'bg-blue-500'
                  ]"
                  :style="{ width: `${importProgress.percentage}%` }"
                ></div>
              </div>
            </div>
            
            <!-- 状态信息 -->
            <p v-if="importStatus" :class="['text-sm mt-2', importStatusColor]">
              {{ importStatus }}
            </p>
            
            <!-- 错误列表 -->
            <div v-if="importErrors.length > 0" class="mt-4 max-h-32 overflow-y-auto">
              <p :class="['text-xs font-semibold mb-2', isDark ? 'text-red-400' : 'text-red-600']">
                错误详情：
              </p>
              <ul :class="['text-xs space-y-1', isDark ? 'text-red-300' : 'text-red-600']">
                <li v-for="(error, index) in importErrors.slice(0, 10)" :key="index" class="font-mono">
                  {{ error }}
                </li>
                <li v-if="importErrors.length > 10" :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-500']">
                  ... 还有 {{ importErrors.length - 10 }} 个错误
                </li>
              </ul>
            </div>
            
            <!-- 导入按钮 -->
            <button
              @click="batchImport"
              :disabled="importing || !importAirInput.trim()"
              :class="[
                'w-full mt-4 px-4 py-3 rounded-lg font-medium transition-colors',
                importing || !importAirInput.trim()
                  ? isDark
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              ]"
            >
              {{ importing ? '导入中...' : '批量导入' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>


    <!-- 清空确认对话框（仿照 shadcn Alert Dialog 交互） -->
    <Teleport to="body">
      <div
        v-if="showClearConfirm"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="cancelClear"
      >
        <div
          :class="[
            'w-full max-w-md rounded-lg shadow-xl',
            'mx-4 md:mx-0',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-4 md:p-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
            <h3 :class="['text-lg font-semibold', isDark ? 'text-white' : 'text-gray-900']">
              确认清空所有模型元数据
            </h3>
            <p :class="['mt-2 text-sm', isDark ? 'text-gray-300' : 'text-gray-600']">
              该操作不可恢复，将删除本地缓存的所有模型元数据信息。是否继续？
            </p>
          </div>
          <div class="p-4 md:p-6 flex justify-end gap-2">
            <button
              @click="cancelClear"
              :class="[
                'px-4 py-2 rounded-lg text-sm',
                isDark ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              ]"
            >
              取消
            </button>
            <button
              @click="confirmClear"
              :class="[
                'px-4 py-2 rounded-lg text-sm text-white',
                'bg-red-600 hover:bg-red-700'
              ]"
            >
              清空
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.show"
      @click.stop
      :style="{
        position: 'fixed',
        top: `${contextMenu.y}px`,
        left: `${contextMenu.x}px`,
        zIndex: 9999
      }"
      :class="[
        'min-w-[120px] rounded-lg shadow-lg border overflow-hidden',
        isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      ]"
    >
      <button
        @click="deleteModel"
        :class="[
          'w-full px-4 py-2 text-left text-sm hover:bg-red-500 hover:text-white transition-colors',
          isDark ? 'text-gray-300' : 'text-gray-700'
        ]"
      >
        删除元数据
      </button>
    </div>
    <!-- 页面级 Toaster：固定在右下角，避免遮挡右上角操作按钮 -->
    <Toaster position="bottom-right" />
  </div>

  <!-- 模型详情对话框 -->
  <ModelDetailDialog
    :model="detailModel"
    :privacy-mode="privacyMode"
    @close="detailModel = null"
    @model-updated="handleModelUpdated"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'
import { 
  XMarkIcon, CloudArrowDownIcon, 
  ClipboardDocumentIcon, 
  TrashIcon 
} from '@heroicons/vue/24/outline'
import ModelCard from '../components/ModelCard.vue'
import ModelDetailDialog from '../components/ModelDetailDialog.vue'
import api from '../api'
import { Toaster, toast } from 'vue-sonner'

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
  preference?: 'liked' | 'neutral' | 'disliked'  // 模型偏好：喜欢、中性、不喜欢
}

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
// const { selectedProjectId } = storeToRefs(projectStore)

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

// 状态
const loading = ref(false)
const checkpoints = ref<ModelMeta[]>([])
const loras = ref<ModelMeta[]>([])

// 筛选器
const ecosystemFilter = ref('')
const baseModelFilter = ref('')

// 对话框
const showImportDialog = ref(false)
const importAirInput = ref('')
const importStatus = ref('')
const importStatusColor = ref('')
const importing = ref(false)

// 清空确认弹窗
const showClearConfirm = ref(false)
const openClearConfirm = () => {
  showClearConfirm.value = true
}
const cancelClear = () => {
  showClearConfirm.value = false
}
const confirmClear = () => {
  // 先立即关闭对话框，再异步执行清空，避免阻塞 UI
  showClearConfirm.value = false
  void clearAllMetadata()
}

// 右键菜单
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  model: null as ModelMeta | null
})

// 所有模型
const allModels = computed(() => [...checkpoints.value, ...loras.value])

// 筛选后的模型
const filteredCheckpoints = computed(() => {
  return filterModels(checkpoints.value)
})

const filteredLoras = computed(() => {
  return filterModels(loras.value)
})

// 筛选逻辑
const filterModels = (models: ModelMeta[]) => {
  let filtered = models
  
  if (ecosystemFilter.value) {
    filtered = filtered.filter(m => m.ecosystem === ecosystemFilter.value)
  }
  
  if (baseModelFilter.value) {
    // 大小写不敏感匹配
    filtered = filtered.filter(m => 
      m.base_model && m.base_model.toLowerCase() === baseModelFilter.value.toLowerCase()
    )
  }
  
  return filtered
}

// 加载模型
const loadModels = async () => {
  loading.value = true
  try {
    // 加载 Checkpoint
    const checkpointResponse = await api.get('/model-meta/checkpoint')
    const checkpointData = (checkpointResponse as any)?.data || checkpointResponse
    checkpoints.value = Array.isArray(checkpointData) ? checkpointData : []
    
    // 加载 LoRA
    const loraResponse = await api.get('/model-meta/loras')
    const loraData = (loraResponse as any)?.data || loraResponse
    loras.value = Array.isArray(loraData) ? loraData : []
    
  } catch (error) {
    console.error('加载模型失败:', error)
  } finally {
    loading.value = false
  }
}

// 保存筛选器
const saveFilters = () => {
  // TODO: 保存到 settings API
  console.log('筛选器已更改')
}

// 清除筛选器
const clearFilters = () => {
  ecosystemFilter.value = ''
  baseModelFilter.value = ''
  saveFilters()
}


// 导出所有 AIR
const exportAllAir = async () => {
  try {
    const airList = allModels.value.map(m => m.air)
    const airText = airList.join('\n')
    
    await navigator.clipboard.writeText(airText)
    toast.success(`已复制 ${airList.length} 个模型的 AIR 到剪贴板`)
  } catch (error) {
    console.error('导出 AIR 失败:', error)
    toast.error('导出失败')
  }
}

// 导入进度
const importProgress = ref({
  current: 0,
  total: 0,
  percentage: 0
})

// 导入错误列表
const importErrors = ref<string[]>([])

// 取消导入标志
const cancelImportFlag = ref(false)

// 是否下载图片（默认勾选）
const downloadImages = ref(true)

// 批量导入（前端并发控制）
const batchImport = async () => {
  const lines = importAirInput.value.split('\n').map(l => l.trim()).filter(l => l)
  
  if (lines.length === 0) {
    importStatus.value = '❌ 请输入模型 AIR 标识符'
    importStatusColor.value = 'text-red-600'
    return
  }
  
  importing.value = true
  cancelImportFlag.value = false
  importErrors.value = []
  importProgress.value = {
    current: 0,
    total: lines.length,
    percentage: 0
  }
  importStatus.value = `⏳ 开始导入 ${lines.length} 个模型...`
  importStatusColor.value = 'text-blue-600'
  
  let successCount = 0
  let failedCount = 0
  let skippedCount = 0
  
  // 获取最大并发数与后端超时设置
  let maxConcurrency = 4 // 默认值
  let civitaiTimeoutMs = 60000 // 默认与后端一致（后端默认60秒）
  try {
    const response = await api.get('/settings/civitai')
    const settings = (response as any)?.data || response
    maxConcurrency = settings?.parallel_workers || 4
    if (settings?.timeout) {
      const t = Number(settings.timeout)
      if (!Number.isNaN(t) && t > 0) civitaiTimeoutMs = Math.round(t * 1000)
    }
  } catch (error) {
    console.warn('获取并发数设置失败，使用默认值:', error)
  }
  
  // 并发导入函数
  const importSingleModel = async (air: string, _index: number, parallelDownload: boolean = false) => {
    if (cancelImportFlag.value) {
      return { success: false, air, error: '已取消' }
    }
    
    try {
      const response = await api.post(
        '/model-meta/import',
        {
          download_images: downloadImages.value,
          air: air,
          parallel_download: parallelDownload
        },
        { timeout: civitaiTimeoutMs }
      )
      
      const data = (response as any)?.data || response
      
      if (data.success) {
        if (data.skipped) {
          skippedCount++
          return { success: true, air, modelName: data.model_name, skipped: true }
        } else {
          successCount++
          
          // 如果有图片下载失败，显示警告信息
          if (data.failed_image_count > 0) {
            const errorMsg = `部分图片下载失败：${data.failed_image_count}/${data.total_image_count} 张图片未能下载`
            importErrors.value.push(`${air}: ${errorMsg}`)
          }
          
          return { success: true, air, modelName: data.model_name, skipped: false }
        }
      } else {
        failedCount++
        // 区分元数据下载失败和图片下载失败
        let errorMsg = data.error || '未知错误'
        if (!errorMsg.includes('部分图片下载失败')) {
          // 这是元数据下载失败
          errorMsg = '元数据下载失败：' + errorMsg
        }
        const fullErrorMsg = `${air}: ${errorMsg}`
        importErrors.value.push(fullErrorMsg)
        return { success: false, air, error: errorMsg }
      }
    } catch (error: any) {
      failedCount++
      let errorMsg = '网络错误'
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        // 请求超时 - 这是元数据下载失败
        errorMsg = '元数据下载超时，请检查网络连接或稍后重试'
      } else if (error.response?.data?.detail) {
        // 后端返回的错误信息
        const detail = error.response.data.detail
        if (detail.includes('网络连接失败') || detail.includes('请求超时')) {
          // 元数据下载失败
          errorMsg = '元数据下载失败：' + detail
        } else {
          errorMsg = detail
        }
      } else if (error.message) {
        errorMsg = error.message
      }
      const fullErrorMsg = `${air}: ${errorMsg}`
      importErrors.value.push(fullErrorMsg)
      return { success: false, air, error: errorMsg }
    } finally {
      // 更新进度
      importProgress.value.current++
      importProgress.value.percentage = Math.round(
        (importProgress.value.current / importProgress.value.total) * 100
      )
      const statusText = skippedCount > 0 
        ? `⏳ ${importProgress.value.current}/${importProgress.value.total} 已完成（成功: ${successCount}, 跳过: ${skippedCount}, 失败: ${failedCount}）`
        : `⏳ ${importProgress.value.current}/${importProgress.value.total} 已完成（成功: ${successCount}, 失败: ${failedCount}）`
      importStatus.value = statusText
    }
  }
  
  // 并发控制导入
  const importWithConcurrency = async () => {
    // 如果只有一行AIR，使用并行下载示例图片
    const useParallelDownload = lines.length === 1
    
    // 分批处理，每批最多 maxConcurrency 个
    for (let i = 0; i < lines.length; i += maxConcurrency) {
      if (cancelImportFlag.value) {
        break
      }
      
      const batch = lines.slice(i, i + maxConcurrency)
      const batchPromises = batch.map((air, batchIndex) => 
        importSingleModel(air, i + batchIndex, useParallelDownload)
      )
      
      await Promise.allSettled(batchPromises)
    }
  }
  
  try {
    await importWithConcurrency()
  } catch (error) {
    console.error('批量导入异常:', error)
  } finally {
    importing.value = false
    
    if (cancelImportFlag.value) {
      importStatus.value = '⚠️ 导入已取消'
      importStatusColor.value = 'text-orange-600'
    } else if (failedCount === 0) {
      const statusText = skippedCount > 0
        ? `✅ 成功导入 ${successCount} 个模型，跳过 ${skippedCount} 个已存在的模型`
        : `✅ 成功导入 ${successCount} 个模型`
      importStatus.value = statusText
      importStatusColor.value = 'text-green-600'
      // 导入成功后刷新模型列表
      await loadModels()
      // 导入完成后立即关闭对话框
          showImportDialog.value = false
          importAirInput.value = ''
          importStatus.value = ''
          importErrors.value = []
    } else if (successCount === 0) {
      importStatus.value = `❌ 全部导入失败（${failedCount} 个）`
      importStatusColor.value = 'text-red-600'
      // 全部失败时也关闭对话框
      showImportDialog.value = false
      importAirInput.value = ''
      importStatus.value = ''
      importErrors.value = []
    } else {
      const statusText = skippedCount > 0
        ? `⚠️ 成功 ${successCount} 个，跳过 ${skippedCount} 个，失败 ${failedCount} 个`
        : `⚠️ 成功 ${successCount} 个，失败 ${failedCount} 个`
      importStatus.value = statusText
      importStatusColor.value = 'text-orange-600'
      // 部分成功也刷新模型列表
      await loadModels()
      // 部分成功时也关闭对话框
      showImportDialog.value = false
      importAirInput.value = ''
      importStatus.value = ''
      importErrors.value = []
    }
  }
}

// 监听对话框打开，自动读取剪贴板
watch(showImportDialog, async (newVal) => {
  if (newVal) {
    // 对话框打开时，等待DOM更新后自动读取剪贴板
    await nextTick()
    loadFromClipboard()
  }
})

// 取消导入（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _cancelImport = () => {
  if (importing.value) {
    cancelImportFlag.value = true
    importStatus.value = '⚠️ 正在取消导入...'
    importStatusColor.value = 'text-orange-600'
  } else {
    showImportDialog.value = false
    importAirInput.value = ''
    importStatus.value = ''
    importErrors.value = []
  }
}

// 从剪贴板读取 AIR
const loadFromClipboard = async () => {
  try {
    const clipboardText = await navigator.clipboard.readText()
    if (!clipboardText) {
      importStatus.value = '❌ 剪贴板为空'
      importStatusColor.value = 'text-red-600'
      return
    }
    
    // 按行切分
    const lines = clipboardText.split('\n').map(line => line.trim()).filter(line => line)
    
    if (lines.length === 0) {
      importStatus.value = '❌ 剪贴板内容为空'
      importStatusColor.value = 'text-red-600'
      return
    }
    
    // AIR 格式正则表达式：urn:air:{ecosystem}:{type}:civitai:{model_id}@{version_id}
    const airPattern = /^urn:air:([\w]+):([\w]+):civitai:(\d+)@(\d+)$/
    
    // 过滤出有效的 AIR
    const validAirs: string[] = []
    for (const line of lines) {
      if (airPattern.test(line)) {
        validAirs.push(line)
      }
    }
    
    if (validAirs.length === 0) {
      importStatus.value = '❌ 剪贴板中没有找到有效的 AIR 标识符'
      importStatusColor.value = 'text-red-600'
      return
    }
    
    // 自动填充到输入框
    importAirInput.value = validAirs.join('\n')
    importStatus.value = `✅ 从剪贴板解析到 ${validAirs.length} 个有效 AIR`
    importStatusColor.value = 'text-green-600'
    
    // 3秒后清除状态提示
    setTimeout(() => {
      if (importStatus.value.includes('✅ 从剪贴板解析到')) {
        importStatus.value = ''
      }
    }, 3000)
    
  } catch (error: any) {
    console.error('读取剪贴板失败:', error)
    importStatus.value = '❌ 读取剪贴板失败，请确保已授予剪贴板权限'
    importStatusColor.value = 'text-red-600'
  }
}

// 清空所有元数据
const clearAllMetadata = async () => {
  try {
    await api.delete('/model-meta/clear')
    toast.success('已清空所有模型元数据')
    await loadModels()
  } catch (error: any) {
    console.error('清空失败:', error)
    toast.error('清空失败: ' + (error?.response?.data?.detail || error?.message || '未知错误'))
  }
}

// 详情对话框
const detailModel = ref<ModelMeta | null>(null)

// 打开详情对话框
const openDetailDialog = (model: ModelMeta) => {
  detailModel.value = model
}

// 处理模型更新事件（重置后刷新列表）
const handleModelUpdated = async () => {
  await loadModels()
  toast.success('模型列表已刷新')
}

// 显示右键菜单
const showModelContextMenu = (event: MouseEvent, model: ModelMeta) => {
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    model: model
  }
}

// 删除模型
const deleteModel = async () => {
  if (!contextMenu.value.model) return
  
  try {
    // 调用删除 API
    await api.delete(`/model-meta/${contextMenu.value.model.version_id}`)
    contextMenu.value.show = false
    toast.success(`已删除: ${contextMenu.value.model.name}`)
    await loadModels()
  } catch (error: any) {
    console.error('删除失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '删除失败'
    toast.error(errorMsg)
    contextMenu.value.show = false
  }
}

// 检查模型文件是否存在
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const checkModelFileExists = (_model: ModelMeta) => {
  // TODO: 调用 API 检查
  return true
}

// 处理偏好状态改变
const handlePreferenceChanged = (model: ModelMeta) => {
  // 更新本地模型列表中的偏好状态
  const updateModelInList = (list: ModelMeta[]) => {
    const index = list.findIndex(m => m.version_id === model.version_id)
    if (index >= 0 && list[index]) {
      list[index].preference = model.preference
    }
  }
  
  updateModelInList(checkpoints.value)
  updateModelInList(loras.value)
}

// 点击外部关闭右键菜单
const handleClickOutside = () => {
  if (contextMenu.value.show) {
    contextMenu.value.show = false
  }
}

watch(() => contextMenu.value.show, (show) => {
  if (show) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onMounted(async () => {
  // 初始化 store
  projectStore.init()
  
  // 初始化隐私模式（从 store 中读取）
  privacyStore.initPrivacyMode()
  
  // 确保项目列表已加载
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  
  // 加载模型
  loadModels()
})
</script>
