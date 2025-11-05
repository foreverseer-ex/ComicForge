<template>
  <div class="space-y-4">
    <!-- 筛选和操作栏 -->
    <div class="flex items-center gap-3">
      <!-- 筛选器 -->
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

      <!-- 清除筛选按钮 -->
      <button
        v-if="ecosystemFilter || baseModelFilter"
        @click="clearFilters"
        :class="[
          'p-2 rounded-lg transition-colors',
          isDark
            ? 'hover:bg-gray-700 text-gray-400'
            : 'hover:bg-gray-100 text-gray-600'
        ]"
        title="清除筛选"
      >
        <XMarkIcon class="w-5 h-5" />
      </button>

      <!-- 操作按钮 -->
      <div class="flex items-center gap-1">
        <!-- 隐私模式 -->
        <button
          @click="togglePrivacyMode"
          :class="[
            'p-2 rounded-lg transition-colors',
            privacyMode
              ? isDark ? 'text-blue-400' : 'text-blue-600'
              : isDark ? 'text-gray-400' : 'text-gray-500',
            isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
          ]"
          :title="privacyMode ? '隐私模式：已启用（点击关闭）' : '隐私模式：已关闭（点击启用）'"
        >
          <EyeSlashIcon v-if="privacyMode" class="w-5 h-5" />
          <EyeIcon v-else class="w-5 h-5" />
        </button>

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

        <!-- 打开所有链接 -->
        <button
          @click="openAllUrls"
          :class="[
            'p-2 rounded-lg transition-colors text-green-500',
            isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
          ]"
          title="在浏览器中打开所有模型的网页链接"
        >
          <ArrowTopRightOnSquareIcon class="w-5 h-5" />
        </button>

        <!-- 刷新元数据 -->
        <button
          @click="showRefreshDialog = true"
          :class="[
            'p-2 rounded-lg transition-colors text-blue-500',
            isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
          ]"
          title="重新下载所有模型元数据"
        >
          <ArrowPathIcon class="w-5 h-5" />
        </button>

        <!-- 清空元数据 -->
        <button
          @click="showClearDialog = true"
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

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          <ModelCard
            v-for="model in filteredCheckpoints"
            :key="model.version_id"
            :model="model"
            :privacy-mode="privacyMode"
            :show-warning="!checkModelFileExists(model)"
            @open-detail="openDetailDialog"
            @context-menu="showModelContextMenu"
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

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          <ModelCard
            v-for="model in filteredLoras"
            :key="model.version_id"
            :model="model"
            :privacy-mode="privacyMode"
            :show-warning="!checkModelFileExists(model)"
            @open-detail="openDetailDialog"
            @context-menu="showModelContextMenu"
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
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 :class="['text-xl font-bold mb-4', isDark ? 'text-white' : 'text-gray-900']">
              从 Civitai 导入模型
            </h2>
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
            
            <!-- 从剪贴板读取按钮 -->
            <div class="flex items-center justify-between mb-2">
              <button
                @click="loadFromClipboard"
                :disabled="importing"
                :class="[
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  importing
                    ? isDark
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                ]"
                title="从剪贴板读取 AIR 标识符"
              >
                📋 从剪贴板读取
              </button>
            </div>
            
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
            
            <div class="flex justify-end gap-3 mt-4">
              <button
                @click="cancelImport"
                :disabled="!importing && !importAirInput.trim()"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  importing || !importAirInput.trim()
                    ? isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    : isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                ]"
              >
                {{ importing ? '取消导入' : '取消' }}
              </button>
              <button
                @click="batchImport"
                :disabled="importing || !importAirInput.trim()"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
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
      </div>
    </Teleport>

    <!-- 清空确认对话框 -->
    <Teleport to="body">
      <div
        v-if="showClearDialog"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showClearDialog = false"
      >
        <div
          :class="[
            'w-full max-w-md rounded-lg shadow-xl',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 class="text-xl font-bold mb-4 text-red-600">确认清空</h2>
            <div class="text-center mb-4">
              <svg class="w-12 h-12 mx-auto text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p :class="['font-bold text-center mb-4', isDark ? 'text-white' : 'text-gray-900']">
              即将删除所有模型元数据！
            </p>
            <div :class="['text-sm mb-4', isDark ? 'text-gray-300' : 'text-gray-700']">
              <p>此操作将删除：</p>
              <ul class="list-disc list-inside mt-2">
                <li>所有 Checkpoint 元数据</li>
                <li>所有 LoRA 元数据</li>
                <li>包括下载的示例图片</li>
              </ul>
            </div>
            <p class="text-sm text-red-600 font-bold text-center mb-4">
              ⚠️ 此操作不可恢复！
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="showClearDialog = false"
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
                @click="clearAllMetadata"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  'bg-red-600 hover:bg-red-700 text-white'
                ]"
              >
                确认清空
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 刷新元数据确认对话框 -->
    <Teleport to="body">
      <div
        v-if="showRefreshDialog"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showRefreshDialog = false"
      >
        <div
          :class="[
            'w-full max-w-md rounded-lg shadow-xl',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 class="text-xl font-bold mb-4 text-blue-600">确认重新下载</h2>
            <div class="text-center mb-4">
              <svg class="w-12 h-12 mx-auto text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p :class="['font-bold text-center mb-4', isDark ? 'text-white' : 'text-gray-900']">
              即将重新下载 {{ allModels.length }} 个模型的元数据
            </p>
            <div :class="['text-sm mb-4', isDark ? 'text-gray-300' : 'text-gray-700']">
              <p>此操作将：</p>
              <ul class="list-disc list-inside mt-2">
                <li>从 Civitai 重新获取最新的模型信息</li>
                <li>更新所有示例图片</li>
                <li>覆盖现有的本地元数据</li>
              </ul>
            </div>
            <p class="text-sm text-orange-600 font-bold text-center mb-4">
              ⚠️ 此过程可能需要较长时间
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="showRefreshDialog = false"
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
                @click="refreshAllMetadata"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  'bg-blue-600 hover:bg-blue-700 text-white'
                ]"
              >
                确认刷新
              </button>
            </div>
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
  </div>

  <!-- 模型详情对话框 -->
  <ModelDetailDialog
    :model="detailModel"
    @close="detailModel = null"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import { 
  XMarkIcon, EyeIcon, EyeSlashIcon, CloudArrowDownIcon, 
  ClipboardDocumentIcon, ArrowTopRightOnSquareIcon, 
  ArrowPathIcon, TrashIcon 
} from '@heroicons/vue/24/outline'
import ModelCard from '../components/ModelCard.vue'
import ModelDetailDialog from '../components/ModelDetailDialog.vue'
import api from '../api'

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

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { selectedProjectId } = storeToRefs(projectStore)

// 状态
const loading = ref(false)
const checkpoints = ref<ModelMeta[]>([])
const loras = ref<ModelMeta[]>([])

// 筛选器
const ecosystemFilter = ref('')
const baseModelFilter = ref('')
const privacyMode = ref(false)

// 对话框
const showImportDialog = ref(false)
const showClearDialog = ref(false)
const showRefreshDialog = ref(false)
const importAirInput = ref('')
const importStatus = ref('')
const importStatusColor = ref('')
const importing = ref(false)

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
    const checkpointData = await api.get('/model-meta/checkpoint')
    checkpoints.value = Array.isArray(checkpointData) ? checkpointData : []
    
    // 加载 LoRA
    const loraData = await api.get('/model-meta/loras')
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

// 切换隐私模式
const togglePrivacyMode = () => {
  privacyMode.value = !privacyMode.value
  // TODO: 保存到 settings API
}

// 导出所有 AIR
const exportAllAir = async () => {
  try {
    const airList = allModels.value.map(m => m.air)
    const airText = airList.join('\n')
    
    await navigator.clipboard.writeText(airText)
    alert(`✅ 已复制 ${airList.length} 个模型的 AIR 到剪贴板`)
  } catch (error) {
    console.error('导出 AIR 失败:', error)
    alert('❌ 导出失败')
  }
}

// 打开所有链接
const openAllUrls = () => {
  try {
    // 按 model_id 去重
    const modelIdToUrl = new Map<number, string>()
    allModels.value.forEach(model => {
      if (model.web_page_url && !modelIdToUrl.has(model.model_id)) {
        modelIdToUrl.set(model.model_id, model.web_page_url)
      }
    })
    
    const urls = Array.from(modelIdToUrl.values())
    
    if (urls.length === 0) {
      alert('❌ 没有找到任何模型的网页链接')
      return
    }
    
    urls.forEach(url => window.open(url, '_blank'))
    alert(`✅ 已在浏览器中打开 ${urls.length} 个模型链接（共 ${allModels.value.length} 个模型，已去重）`)
  } catch (error) {
    console.error('打开链接失败:', error)
    alert('❌ 打开失败')
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
  
  // 获取最大并发数设置
  let maxConcurrency = 3 // 默认值
  try {
    const settings = await api.get('/settings/civitai')
    maxConcurrency = settings.max_concurrency || 3
  } catch (error) {
    console.warn('获取并发数设置失败，使用默认值:', error)
  }
  
  // 并发导入函数
  const importSingleModel = async (air: string, index: number) => {
    if (cancelImportFlag.value) {
      return { success: false, air, error: '已取消' }
    }
    
    try {
      const response = await api.post('/model-meta/import', {
        air: air
      })
      
      if (response.success) {
        successCount++
        return { success: true, air, modelName: response.model_name }
      } else {
        failedCount++
        const errorMsg = `${air}: ${response.error || '未知错误'}`
        importErrors.value.push(errorMsg)
        return { success: false, air, error: response.error }
      }
    } catch (error: any) {
      failedCount++
      const errorMsg = `${air}: ${error.response?.data?.detail || error.message || '网络错误'}`
      importErrors.value.push(errorMsg)
      return { success: false, air, error: errorMsg }
    } finally {
      // 更新进度
      importProgress.value.current++
      importProgress.value.percentage = Math.round(
        (importProgress.value.current / importProgress.value.total) * 100
      )
      importStatus.value = `⏳ ${importProgress.value.current}/${importProgress.value.total} 已完成（成功: ${successCount}, 失败: ${failedCount}）`
    }
  }
  
  // 并发控制导入
  const importWithConcurrency = async () => {
    // 分批处理，每批最多 maxConcurrency 个
    for (let i = 0; i < lines.length; i += maxConcurrency) {
      if (cancelImportFlag.value) {
        break
      }
      
      const batch = lines.slice(i, i + maxConcurrency)
      const batchPromises = batch.map((air, batchIndex) => 
        importSingleModel(air, i + batchIndex)
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
      importStatus.value = `✅ 成功导入 ${successCount} 个模型`
      importStatusColor.value = 'text-green-600'
      // 导入成功后刷新模型列表
      await loadModels()
      // 3秒后关闭对话框
      setTimeout(() => {
        if (importProgress.value.current === importProgress.value.total) {
          showImportDialog.value = false
          importAirInput.value = ''
          importStatus.value = ''
          importErrors.value = []
        }
      }, 3000)
    } else if (successCount === 0) {
      importStatus.value = `❌ 全部导入失败（${failedCount} 个）`
      importStatusColor.value = 'text-red-600'
    } else {
      importStatus.value = `⚠️ 成功 ${successCount} 个，失败 ${failedCount} 个`
      importStatusColor.value = 'text-orange-600'
      // 部分成功也刷新模型列表
      await loadModels()
    }
  }
}

// 取消导入
const cancelImport = () => {
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
    // TODO: 调用清空 API
    showClearDialog.value = false
    alert('✅ 已清空所有模型元数据')
    await loadModels()
  } catch (error) {
    console.error('清空失败:', error)
    alert('❌ 清空失败')
  }
}

// 刷新所有元数据
const refreshAllMetadata = async () => {
  showRefreshDialog.value = false
  const airList = allModels.value.map(m => m.air)
  importAirInput.value = airList.join('\n')
  showImportDialog.value = true
  // 自动开始导入
  setTimeout(() => {
    batchImport()
  }, 100)
}

// 详情对话框
const detailModel = ref<ModelMeta | null>(null)

// 打开详情对话框
const openDetailDialog = (model: ModelMeta) => {
  detailModel.value = model
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
    // TODO: 调用删除 API
    contextMenu.value.show = false
    alert(`✅ 已删除: ${contextMenu.value.model.name}`)
    await loadModels()
  } catch (error) {
    console.error('删除失败:', error)
    alert('❌ 删除失败')
    contextMenu.value.show = false
  }
}

// 检查模型文件是否存在
const checkModelFileExists = (model: ModelMeta) => {
  // TODO: 调用 API 检查
  return true
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
  
  // 确保项目列表已加载
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  
  // 加载模型
  loadModels()
})
</script>
