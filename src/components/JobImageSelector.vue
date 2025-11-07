<template>
  <div class="w-full h-full flex flex-col">
    <!-- 标题栏 -->
    <div 
      :class="[
        'flex items-center justify-between border-b',
        'p-3 md:p-4',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <h2 
        :class="[
          'text-lg md:text-xl font-bold',
          isDark ? 'text-white' : 'text-gray-900'
        ]"
      >
        {{ title }}
      </h2>
      <div class="flex items-center gap-2">
        <button
          v-if="showSwitchButton"
          @click="$emit('switch-to-create')"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          ]"
          title="切换到新建任务"
        >
          <PlusIcon class="w-5 h-5" />
        </button>
        <button
          @click="$emit('close')"
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
      <!-- 加载状态 -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
             :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
      </div>

      <!-- 任务图像网格 -->
      <div v-else-if="completedJobs.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div
          v-for="job in completedJobs"
          :key="job.job_id"
          :class="[
            'relative rounded-lg overflow-hidden border cursor-pointer transition-all hover:shadow-lg',
            isDark ? 'border-gray-600 hover:border-gray-500' : 'border-gray-200 hover:border-gray-300'
          ]"
          @click="handleSelectJob(job)"
        >
          <!-- 图像 -->
          <div 
            :class="[
              'w-full aspect-square bg-gray-100 flex items-center justify-center overflow-hidden',
              isDark ? 'bg-gray-800' : 'bg-gray-100'
            ]"
          >
            <img
              v-if="!privacyMode"
              :src="getJobImageUrl(job.job_id)"
              :alt="job.name || `任务 ${job.job_id.substring(0, 8)}`"
              class="w-full h-full object-cover"
              @error="handleImageError"
            />
            <div v-else class="flex flex-col items-center justify-center w-full h-full">
              <PhotoIcon class="w-12 h-12 mb-2" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
              <span :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-500']">隐私模式</span>
            </div>
          </div>
          
          <!-- 任务信息 -->
          <div class="p-2">
            <div 
              :class="[
                'text-sm font-semibold truncate mb-1',
                isDark ? 'text-white' : 'text-gray-900'
              ]"
              :title="job.name || '未命名任务'"
            >
              {{ job.name || '未命名任务' }}
            </div>
            <div 
              v-if="job.desc"
              :class="[
                'text-xs truncate',
                isDark ? 'text-gray-400' : 'text-gray-600'
              ]"
              :title="job.desc"
            >
              {{ job.desc }}
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="flex flex-col items-center justify-center h-full">
        <PhotoIcon class="w-16 h-16 mb-4" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
        <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
          暂无已完成的任务
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'
import { XMarkIcon, PlusIcon, PhotoIcon } from '@heroicons/vue/24/outline'
import api from '../api'
import { getApiBaseURL } from '../utils/apiConfig'

interface Job {
  job_id: string
  name?: string
  desc?: string
  created_at: string
  completed_at?: string
  draw_args?: any
}

interface Props {
  title?: string
  showSwitchButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '选择已有任务图像',
  showSwitchButton: true
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'switch-to-create'): void
  (e: 'select', job: Job): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

const loading = ref(false)
const jobs = ref<Job[]>([])

// 只显示已完成的任务
const completedJobs = computed(() => {
  return jobs.value.filter(job => job.completed_at !== null && job.completed_at !== undefined)
})

// 获取任务图像 URL
const getJobImageUrl = (jobId: string) => {
  const baseURL = getApiBaseURL()
  return `${baseURL}/draw/job/image?job_id=${encodeURIComponent(jobId)}`
}

// 加载任务列表
const loadJobs = async () => {
  loading.value = true
  try {
    const data = await api.get('/draw/all')
    jobs.value = Array.isArray(data) ? data : []
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
    jobs.value = []
  } finally {
    loading.value = false
  }
}

// 选择任务
const handleSelectJob = (job: Job) => {
  emit('select', job)
}

// 图片加载错误处理
const handleImageError = () => {
  // 图片加载失败时，不显示图片
}

onMounted(() => {
  loadJobs()
})
</script>

