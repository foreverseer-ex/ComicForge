<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="close"
    >
      <div
        :class="[
          'w-full max-w-6xl max-h-[90vh] rounded-lg shadow-xl flex flex-col',
          'mx-4 md:mx-0',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 新建任务模式 -->
        <CreateDrawTaskDialog
          v-if="mode === 'create'"
          :show="true"
          :title="`为 ${actorName} 生成立绘`"
          :context-info="actorName"
          :initial-name="taskName"
          :additional-info="additionalInfo"
          :project-id="projectId ?? undefined"
          submit-button-text="开始生成"
          submit-button-loading-text="生成中..."
          :show-cancel="false"
          :show-switch-to-jobs="true"
          @close="close"
          @submit="handleSubmit"
          @switch-to-jobs="mode = 'select'"
        />
        
        <!-- 选择已有任务模式 -->
        <JobImageSelector
          v-else
          :title="`为 ${actorName} 选择立绘`"
          :show-switch-button="true"
          @close="close"
          @switch-to-create="mode = 'create'"
          @select="handleSelectJob"
        />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import api from '../api'
import { showToast } from '../utils/toast'
import CreateDrawTaskDialog from './CreateDrawTaskDialog.vue'
import JobImageSelector from './JobImageSelector.vue'

interface Props {
  show: boolean
  actorName: string
  actorId: string
  projectId: string | null | undefined
  actorDesc?: string // 角色描述
  actorTags?: Record<string, string> // 角色标签
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'generated'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 模式：'create' 创建新任务，'select' 选择已有任务
const mode = ref<'create' | 'select'>('create')

// 计算任务名称和描述
const taskName = computed(() => {
  return `角色立绘-${props.actorName}`
})

// 计算附加信息（角色描述和标签）
const additionalInfo = computed(() => {
  const parts: string[] = []
  if (props.actorDesc) {
    parts.push(`角色描述：${props.actorDesc}`)
  }
  if (props.actorTags && Object.keys(props.actorTags).length > 0) {
    const tagStr = Object.entries(props.actorTags)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ')
    parts.push(`标签：${tagStr}`)
  }
  return parts.length > 0 ? parts.join('\n') : undefined
})

// 提交表单（创建新任务）
const handleSubmit = async (data: any) => {
  try {
    // 步骤1: 调用生成 API，获取 batch_id
    showToast('正在创建绘图任务...', 'info')
    const lorasDict: Record<string, number> = data.loras || {}
    
    // 合并附加信息到任务描述
    // 注意：DrawTaskForm 应该已经合并了，但为了确保，我们在这里再次检查
    let finalDesc = data.desc || ''
    if (additionalInfo.value) {
      if (finalDesc) {
        finalDesc = `${finalDesc}\n\n${additionalInfo.value}`
      } else {
        finalDesc = additionalInfo.value
      }
    }
    
    const response = await api.post('/draw', null, {
      params: {
        name: data.name || taskName.value,
        desc: finalDesc || undefined,
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
    
    // 后端直接返回 batch_id 字符串
    const batch_id = response.data || response
    
    if (!batch_id || typeof batch_id !== 'string') {
      throw new Error('创建绘图任务失败：未返回 batch_id')
    }
    
    // 步骤2: 从 batch_id 添加立绘到 actor（使用任务名称和任务描述）
    showToast('正在添加立绘任务...', 'info')
    await api.post(`/actor/${props.actorId}/add_portrait_from_batch`, null, {
      params: {
        batch_id: batch_id,
        title: data.name || taskName.value,
        desc: finalDesc || undefined,
        project_id: props.projectId || null
      }
    })
    
    showToast('立绘生成任务已提交，完成后将自动添加到角色', 'success')
    
    emit('generated')
    close()
  } catch (error: any) {
    console.error('生成立绘失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    showToast('生成立绘失败: ' + errorMessage, 'error')
    throw error // 重新抛出错误，让对话框保持打开状态
  }
}

// 选择已有任务
const handleSelectJob = async (job: any) => {
  try {
    showToast('正在添加立绘...', 'info')
    
    // 调用从 job 添加立绘的 API
    const result = await api.post(`/actor/${props.actorId}/add_portrait_from_job`, null, {
      params: {
        job_id: job.job_id,
        title: taskName.value,
        desc: additionalInfo.value || undefined,
        project_id: props.projectId || null
      }
    })
    const resultData = (result as any)?.data || result
    
    if (resultData?.completed) {
      showToast('立绘已成功添加到角色', 'success')
    } else {
      showToast('立绘生成任务已提交，完成后将自动添加到角色', 'success')
    }
    
    emit('generated')
    close()
  } catch (error: any) {
    console.error('添加立绘失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    showToast('添加立绘失败: ' + errorMessage, 'error')
  }
}

const close = () => {
  mode.value = 'create' // 重置模式
  emit('close')
}
</script>
