<template>
  <div class="space-y-6">
    <!-- 页面标题栏 -->
    <div 
      :class="[
        'flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <div class="flex items-center gap-4">
        <PaintBrushIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          任务管理
        </h1>
      </div>
      
      <div class="flex items-center gap-2 flex-wrap">
        <button
          @click="showCreateDialog = true"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          ]"
          title="新建任务"
        >
          <PlusIcon class="w-5 h-5" />
        </button>
        <button
          v-if="jobs.length > 0"
          @click="selectedJobIds.size > 0 ? handleDeleteSelected() : handleClearAll()"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'
          ]"
          :title="selectedJobIds.size > 0 ? `删除选中 (${selectedJobIds.size})` : '清空所有任务'"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div>
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

      <!-- 空状态 -->
      <div 
        v-else-if="jobs.length === 0"
        class="h-full flex items-center justify-center py-20"
      >
        <div 
          @click="showCreateDialog = true"
          :class="[
            'text-center rounded-lg border p-8 cursor-pointer transition-colors',
            isDark 
              ? 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600' 
              : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
          ]"
        >
          <PaintBrushIcon class="w-16 h-16 mx-auto mb-4" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            暂无任务
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            点击此处开始创建绘图任务
          </p>
        </div>
      </div>

      <!-- 任务列表 -->
      <div v-else>
        <!-- 表头 -->
        <div 
          :class="[
            'grid gap-4 p-3 border-b font-medium text-xs',
            'grid-cols-5 md:grid-cols-12',
            isDark ? 'border-gray-700 text-gray-300' : 'border-gray-200 text-gray-700'
          ]"
        >
          <div class="hidden md:flex md:col-span-1 items-center justify-center">
            <input
              type="checkbox"
              :checked="isAllSelected"
              @change="toggleSelectAll"
              :class="[
                'w-4 h-4 rounded cursor-pointer',
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
              ]"
              title="全选/取消全选"
            />
          </div>
          <div class="col-span-2 md:col-span-2">任务名称</div>
          <div class="hidden md:block md:col-span-5">任务描述</div>
          <div class="hidden md:block md:col-span-2">Job ID</div>
          <div class="col-span-2 md:col-span-1">状态</div>
          <div class="col-span-1 md:col-span-1 text-right">操作</div>
        </div>

        <!-- 任务行 -->
        <div
          v-for="job in jobs"
          :key="job.job_id"
          :class="[
            'grid gap-4 p-3 border-b transition-colors',
            'grid-cols-5 md:grid-cols-12',
            isDark 
              ? selectedJobIds.has(job.job_id)
                ? 'border-gray-700 bg-gray-800 hover:bg-gray-750'
                : 'border-gray-700 hover:bg-gray-800/50'
              : selectedJobIds.has(job.job_id)
                ? 'border-gray-200 bg-blue-50 hover:bg-blue-100'
                : 'border-gray-200 hover:bg-gray-50'
          ]"
        >
          <!-- 复选框（移动端隐藏） -->
          <div class="hidden md:flex md:col-span-1 items-center justify-center">
            <input
              type="checkbox"
              :checked="selectedJobIds.has(job.job_id)"
              @change="toggleSelectJob(job.job_id)"
              :class="[
                'w-4 h-4 rounded cursor-pointer',
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
              ]"
            />
          </div>
          <!-- 任务名称 -->
          <div class="col-span-2 md:col-span-2 flex items-center">
            <div class="flex-1 min-w-0">
              <div 
                v-if="job.name"
                @click="openParamsDialog(job)"
                :class="[
                  'text-xs truncate cursor-pointer hover:underline',
                  isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-900'
                ]"
                :title="job.name + ' (点击查看参数)'"
              >
                {{ job.name }}
              </div>
              <div 
                v-else
                :class="[
                  'text-xs truncate',
                  isDark ? 'text-gray-400' : 'text-gray-600'
                ]"
              >
                -
              </div>
            </div>
          </div>

          <!-- 任务描述（移动端隐藏） -->
          <div class="hidden md:flex md:col-span-5 items-center">
            <div 
              v-if="job.desc"
              @click="copyToClipboard(job.desc)"
              :class="[
                'text-xs truncate cursor-pointer hover:underline',
                isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-600 hover:text-gray-900'
              ]"
              :title="job.desc + ' (点击复制)'"
            >
              {{ job.desc }}
            </div>
            <div 
              v-else
              :class="[
                'text-xs truncate',
                isDark ? 'text-gray-400' : 'text-gray-600'
              ]"
            >
              -
            </div>
          </div>

          <!-- Job ID（移动端隐藏） -->
          <div class="hidden md:flex md:col-span-2 items-center">
            <div 
              @click="copyToClipboard(job.job_id)"
              :class="[
                'text-xs font-mono truncate cursor-pointer hover:underline',
                isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-900'
              ]"
              :title="job.job_id + ' (点击复制)'"
            >
              {{ job.job_id.substring(0, 20) }}...
            </div>
          </div>

          <!-- 状态标识 -->
          <div class="col-span-2 md:col-span-1 flex items-center">
            <span
              v-if="job.status === 'failed'"
              @click="showErrorDialog(job)"
              :class="[
                'px-2 py-1 text-xs rounded cursor-pointer transition-opacity hover:opacity-80 whitespace-nowrap',
                isDark ? 'bg-red-600 text-white' : 'bg-red-100 text-red-800'
              ]"
              title="任务失败，点击查看详情"
            >
              失败
            </span>
            <span
              v-else-if="job.status === 'completed' || jobStatuses[job.job_id] === true"
              @click="handlePreviewImage(job.job_id)"
              :class="[
                'px-2 py-1 text-xs rounded cursor-pointer transition-opacity hover:opacity-80 whitespace-nowrap',
                isDark ? 'bg-green-600 text-white' : 'bg-green-100 text-green-800'
              ]"
              title="点击预览"
            >
              已完成
            </span>
            <span
              v-else-if="jobStatuses[job.job_id] === false || !job.completed_at"
              :class="[
                'px-2 py-1 text-xs rounded whitespace-nowrap',
                isDark ? 'bg-yellow-600 text-white' : 'bg-yellow-100 text-yellow-800'
              ]"
            >
              生成中
            </span>
            <span
              v-else
              :class="[
                'px-2 py-1 text-xs rounded whitespace-nowrap',
                isDark ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-800'
              ]"
            >
              未知
            </span>
          </div>

          <!-- 操作按钮 -->
          <div class="col-span-1 md:col-span-1 flex items-center justify-end gap-2">

            <!-- 下载按钮（移动端隐藏） -->
            <button
              v-if="jobStatuses[job.job_id] === true"
              @click="handleDownload(job.job_id)"
              :class="[
                'p-2 rounded transition-colors hidden md:block',
                isDark
                  ? 'hover:bg-gray-700 text-blue-400'
                  : 'hover:bg-gray-100 text-blue-600'
              ]"
              title="下载图片"
            >
              <ArrowDownTrayIcon class="w-5 h-5" />
            </button>

            <!-- 删除按钮 -->
            <button
              @click="handleDelete(job.job_id)"
              :class="[
                'p-2 rounded transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-red-400'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-red-600'
              ]"
              title="删除任务"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建任务对话框 -->
    <CreateDrawTaskDialog
      :show="showCreateDialog"
      title="新建绘图任务"
      submit-button-text="创建任务"
      submit-button-loading-text="创建中..."
      :show-cancel="true"
      @close="showCreateDialog = false"
      @submit="handleTaskSubmit"
      @submitted="handleTaskCreated"
    />

    <!-- 生成参数对话框 -->
    <ModelParamsDialog
      v-if="selectedJobForParams"
      :params="selectedJobForParams.draw_args || null"
      :title="selectedJobForParams.name ? `生成参数 - ${selectedJobForParams.name}` : '生成参数'"
      :job-id="selectedJobForParams.job_id"
      @close="selectedJobForParams = null"
    />

    <!-- 图片预览对话框 -->
    <ImageGalleryDialog
      :visible="previewJobId !== null"
      :images="completedJobImageUrls"
      :initial-index="previewJobIndex"
      :job-ids="completedJobIds"
      @close="previewJobId = null"
      @show-params="handleShowParamsFromGallery"
    />

    <!-- 确认对话框 -->
    <ConfirmDialog
      :show="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.show = false"
    />

    <!-- 提示对话框 -->
    <AlertDialog
      :show="alertDialog.show"
      :title="alertDialog.title"
      :message="alertDialog.message"
      @close="alertDialog.show = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import api from '../api'
import { showToast } from '../utils/toast'
import { getApiBaseURL } from '../utils/apiConfig'
import {
  PaintBrushIcon,
  PlusIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import CreateDrawTaskDialog from '../components/CreateDrawTaskDialog.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import AlertDialog from '../components/AlertDialog.vue'
import ImageGalleryDialog from '../components/ImageGalleryDialog.vue'
import ModelParamsDialog from '../components/ModelParamsDialog.vue'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

interface Job {
  job_id: string
  name?: string
  desc?: string
  created_at: string
  completed_at?: string
  status?: string  // 'completed' | 'failed' | 'pending'
  draw_args?: {
    model?: string
    prompt?: string
    negative_prompt?: string
    width?: number
    height?: number
    steps?: number
    cfg_scale?: number
    sampler?: string
    seed?: number
    [key: string]: any
  }
}

const jobs = ref<Job[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const previewJobId = ref<string | null>(null)
const jobStatuses = ref<Record<string, boolean | null>>({})  // true=完成, false=生成中, null=未知（兼容旧逻辑）
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null)
const selectedJobIds = ref<Set<string>>(new Set()) // 选中的任务ID集合
const selectedJobForParams = ref<Job | null>(null) // 选中的任务（用于显示参数）

// 对话框状态
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {}
})

const alertDialog = ref({
  show: false,
  title: '',
  message: ''
})

// 加载任务列表
const loadJobs = async () => {
  loading.value = true
  try {
    const data = await api.get('/draw/all')
    jobs.value = data
    // 清除已删除任务的选中状态
    const existingJobIds = new Set(jobs.value.map(job => job.job_id))
    selectedJobIds.value = new Set(
      Array.from(selectedJobIds.value).filter(id => existingJobIds.has(id))
    )
    // 直接从数据库字段判断状态（completed_at 存在 = 已完成）
    updateJobStatusesFromData()
    // 只检查那些可能还在生成中的任务（completed_at 为 null）
    await checkPendingJobStatuses()
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 从数据库数据更新任务状态（不需要API调用）
const updateJobStatusesFromData = () => {
  jobStatuses.value = {}
  for (const job of jobs.value) {
    // 根据 status 字段判断状态
    if (job.status === 'completed') {
      jobStatuses.value[job.job_id] = true
    } else if (job.status === 'failed') {
      jobStatuses.value[job.job_id] = false  // 失败的任务不算完成，但已完成（有 completed_at）
    } else if (job.completed_at) {
      // 兼容旧数据：如果有 completed_at 但没有 status，默认为完成
      jobStatuses.value[job.job_id] = true
    } else {
      // 否则是生成中
      jobStatuses.value[job.job_id] = false
    }
  }
}

// 只检查那些可能还在生成中的任务（completed_at 为 null）
const checkPendingJobStatuses = async () => {
  const pendingJobs = jobs.value.filter(job => !job.completed_at)
  
  // 并行检查所有待处理任务
  const promises = pendingJobs.map(async (job) => {
    try {
      const jobData = await api.get('/draw', { params: { job_id: job.job_id } })
      // 更新任务数据（可能包含 status 或 completed_at）
      const index = jobs.value.findIndex(j => j.job_id === job.job_id)
      if (index >= 0) {
        jobs.value[index] = jobData
      }
      // 更新状态
      if (jobData.status === 'completed') {
        jobStatuses.value[job.job_id] = true
      } else if (jobData.status === 'failed') {
        jobStatuses.value[job.job_id] = false
      } else if (jobData.completed_at) {
        // 兼容旧数据
        jobStatuses.value[job.job_id] = true
      }
    } catch (error) {
      console.debug(`检查任务状态失败: ${job.job_id}`, error)
    }
  })
  
  await Promise.all(promises)
}

// 检查单个任务状态（只在需要时调用）
const checkJobStatus = async (jobId: string): Promise<boolean> => {
  try {
    const response = await api.get('/draw/job/status', { params: { job_id: jobId } })
    return response.completed || false
  } catch (error) {
    console.debug(`检查任务状态失败: ${jobId}`, error)
    return false
  }
}

// 注意：移除了 loadJobImage 和 jobImageUrls
// 图片会在预览时由 ImageGalleryDialog 按需加载，不需要预加载

// 删除任务
const handleDelete = async (jobId: string) => {
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: '确定要删除这个任务吗？',
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        await api.delete('/draw', { params: { job_id: jobId } })
        selectedJobIds.value.delete(jobId) // 从选中状态中移除
        await loadJobs()
        showToast('删除成功', 'success')
      } catch (error: any) {
        console.error('删除任务失败:', error)
        alertDialog.value = {
          show: true,
          title: '删除失败',
          message: error.response?.data?.detail || error.message || '未知错误'
        }
      }
    }
  }
}

// 全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedJobIds.value.clear()
  } else {
    selectedJobIds.value = new Set(jobs.value.map(job => job.job_id))
  }
}

// 切换单个任务选中状态
const toggleSelectJob = (jobId: string) => {
  if (selectedJobIds.value.has(jobId)) {
    selectedJobIds.value.delete(jobId)
  } else {
    selectedJobIds.value.add(jobId)
  }
}

// 是否全选
const isAllSelected = computed(() => {
  return jobs.value.length > 0 && selectedJobIds.value.size === jobs.value.length
})

// 删除选中任务
const handleDeleteSelected = async () => {
  const count = selectedJobIds.value.size
  if (count === 0) return
  
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除选中的 ${count} 个任务吗？此操作不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        const jobIdsArray = Array.from(selectedJobIds.value)
        await api.post('/draw/batch/delete', jobIdsArray)
        selectedJobIds.value.clear() // 清除选中状态
        await loadJobs()
        showToast(`成功删除 ${count} 个任务`, 'success')
      } catch (error: any) {
        console.error('批量删除任务失败:', error)
        alertDialog.value = {
          show: true,
          title: '删除失败',
          message: error.response?.data?.detail || error.message || '未知错误'
        }
      }
    }
  }
}

// 清空所有任务
const handleClearAll = async () => {
  confirmDialog.value = {
    show: true,
    title: '确认清空',
    message: '确定要清空所有任务吗？此操作不可恢复！',
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        await api.delete('/draw/clear')
        selectedJobIds.value.clear() // 清除选中状态
        await loadJobs()
        showToast('清空成功', 'success')
      } catch (error: any) {
        console.error('清空任务失败:', error)
        alertDialog.value = {
          show: true,
          title: '清空失败',
          message: error.response?.data?.detail || error.message || '未知错误'
        }
      }
    }
  }
}

// 下载图片
const handleDownload = async (jobId: string) => {
  try {
    const baseURL = getApiBaseURL()
    const url = `${baseURL}/draw/job/image?job_id=${encodeURIComponent(jobId)}`
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `job_${jobId}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
    showToast('下载成功', 'success')
  } catch (error: any) {
    console.error('下载图片失败:', error)
    alertDialog.value = {
      show: true,
      title: '下载失败',
      message: error.message || '未知错误'
    }
  }
}

// 已完成任务的 job_id 列表（用于图片画廊）
const completedJobIds = computed(() => {
  return jobs.value
    .filter(job => jobStatuses.value[job.job_id] === true)
    .map(job => job.job_id)
})

// 已完成任务的图片 URL 列表（用于图片画廊）
const completedJobImageUrls = computed(() => {
  const baseURL = getApiBaseURL()
  return jobs.value
    .filter(job => jobStatuses.value[job.job_id] === true)
    .map(job => {
      // 使用 API URL 而不是 blob URL，因为 ImageGalleryDialog 可能需要重新加载
      return `${baseURL}/draw/job/image?job_id=${encodeURIComponent(job.job_id)}`
    })
})

// 当前预览任务在已完成任务列表中的索引
const previewJobIndex = computed(() => {
  if (!previewJobId.value) return 0
  
  const index = completedJobIds.value.indexOf(previewJobId.value)
  return index >= 0 ? index : 0
})

// 预览图片
const handlePreviewImage = (jobId: string) => {
  previewJobId.value = jobId
  // 不需要预加载图片，ImageGalleryDialog 会按需加载
}

// 复制到剪贴板
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    showToast('已复制到剪贴板', 'success')
  } catch (error: any) {
    console.error('复制失败:', error)
    showToast('复制失败', 'error')
  }
}

// 打开参数对话框
const openParamsDialog = (job: Job) => {
  selectedJobForParams.value = job
}

// 从图片画廊打开参数对话框
const handleShowParamsFromGallery = (jobId: string) => {
  const job = jobs.value.find(j => j.job_id === jobId)
  if (job) {
    selectedJobForParams.value = job
  }
}

// 显示错误对话框
const showErrorDialog = (job: Job) => {
  alertDialog.value = {
    show: true,
    title: '任务失败',
    message: `任务执行失败（${job.job_id.substring(0, 8)}...），请检查参数或重试`
  }
}

// 提交任务
const handleTaskSubmit = async (data: any) => {
  try {
    // 构建 LoRA 字典
    const lorasDict: Record<string, number> = data.loras || {}
    
    // 调用创建任务 API
    const result = await api.post('/draw', null, {
      params: {
        name: data.name || undefined,
        desc: data.desc || undefined,
        model: data.model,
        prompt: data.prompt,
        negative_prompt: data.negative_prompt,
        sampler_name: data.sampler_name,
        steps: data.steps,
        cfg_scale: data.cfg_scale,
        width: data.width,
        height: data.height,
        seed: data.seed,
        clip_skip: data.clip_skip || undefined,
        vae: data.vae || undefined,
        loras: Object.keys(lorasDict).length > 0 ? JSON.stringify(lorasDict) : undefined,
        batch_size: data.batch_size || 1
      }
    })
    
    if (!result?.batch_id) {
      throw new Error('创建绘图任务失败：未返回 batch_id')
    }
    
    // 检查是否有部分失败
    if (result.partial_success) {
      showToast(
        `批量任务部分成功：成功创建 ${result.success_count}/${result.total_requested} 个任务，${result.failed_count} 个任务创建失败`,
        'warning'
      )
    } else {
      showToast(`已创建批量任务（batch_id: ${result.batch_id.substring(0, 8)}...，包含 ${result.job_ids?.length || 1} 个任务）`, 'success')
    }
  } catch (error: any) {
    console.error('创建任务失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    showToast('创建任务失败: ' + errorMessage, 'error')
    throw error // 重新抛出错误，让对话框保持打开状态
  }
}

// 任务创建成功
const handleTaskCreated = () => {
  showCreateDialog.value = false
  loadJobs()
}

// 检查是否有正在生成的任务
const hasGeneratingJobs = computed(() => {
  return Object.values(jobStatuses.value).some(status => status === false)
})

// 定时刷新（只检查待处理的任务）
watch(hasGeneratingJobs, (hasGenerating) => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
  
  if (hasGenerating) {
    refreshTimer.value = setInterval(async () => {
      await checkPendingJobStatuses()
    }, 3000) // 每3秒刷新一次
  }
}, { immediate: true })

onMounted(() => {
  loadJobs()
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
})
</script>

