<template>
  <CreateDrawTaskDialog
    :show="show"
    :title="`为 ${actorName} 生成立绘`"
    :context-info="actorName"
    :initial-name="taskName"
    :initial-desc="taskDesc"
    submit-button-text="开始生成"
    submit-button-loading-text="生成中..."
    :show-cancel="false"
    @close="close"
    @submit="handleSubmit"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import api from '../api'
import { showToast } from '../utils/toast'
import CreateDrawTaskDialog from './CreateDrawTaskDialog.vue'

interface Props {
  show: boolean
  actorName: string
  actorId: string
  projectId: string
  actorDesc?: string // 角色描述
  actorTags?: Record<string, string> // 角色标签
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'generated'): void
}>()

// 计算任务名称和描述
const taskName = computed(() => {
  return `角色立绘-${props.actorName}`
})

const taskDesc = computed(() => {
  const parts: string[] = []
  if (props.actorDesc) {
    parts.push(props.actorDesc)
  }
  if (props.actorTags && Object.keys(props.actorTags).length > 0) {
    const tagStr = Object.entries(props.actorTags)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ')
    parts.push(tagStr)
  }
  return parts.join('\n')
})

// 提交表单
const handleSubmit = async (data: any) => {
  try {
    // 步骤1: 调用生成 API，获取 job_id
    showToast('正在创建绘图任务...', 'info')
    const lorasDict: Record<string, number> = data.loras || {}
    
    const result = await api.post('/draw', null, {
      params: {
        name: data.name || taskName.value,
        desc: data.desc || taskDesc.value || undefined,
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
        loras: Object.keys(lorasDict).length > 0 ? JSON.stringify(lorasDict) : undefined
      }
    })
    
    if (!result?.job_id) {
      throw new Error('创建绘图任务失败：未返回 job_id')
    }
    
    // 步骤2: 从 job_id 添加立绘到 actor（使用任务名称和任务描述）
    showToast('正在添加立绘任务...', 'info')
    await api.post(`/actor/${props.actorId}/add_portrait_from_job`, null, {
      params: {
        project_id: props.projectId,
        job_id: result.job_id,
        title: data.name || taskName.value,
        desc: data.desc || taskDesc.value || undefined
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

const close = () => {
  emit('close')
}
</script>
