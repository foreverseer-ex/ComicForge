<template>
  <div class="space-y-6">
    <!-- 页面标题栏 -->
    <div 
      :class="[
        'flex items-center justify-between gap-4 pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <div class="flex items-center gap-4">
        <UserGroupIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          角色管理
        </h1>
      </div>
      
      <div v-if="selectedProjectId" class="flex items-center gap-2">
        <button
          v-if="actors.length > 0"
          @click="selectedActorIds.size > 0 ? handleDeleteSelected() : handleClearAll()"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'
          ]"
          :title="selectedActorIds.size > 0 ? `删除选中 (${selectedActorIds.size})` : '清空所有角色'"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
        <button
          @click="showCreateDialog = true"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          ]"
          title="新增角色"
        >
          <PlusIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div>
      <!-- 无项目状态 -->
      <div 
        v-if="!selectedProjectId"
        class="h-full flex items-center justify-center py-20"
      >
        <div 
          :class="[
            'text-center rounded-lg border p-8',
            isDark 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          ]"
        >
          <svg 
            class="w-16 h-16 mx-auto mb-4"
            :class="isDark ? 'text-gray-600' : 'text-gray-400'"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            请先创建一个项目
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            在主页创建项目后，才能管理角色
          </p>
        </div>
      </div>

      <!-- 加载状态 -->
      <div 
        v-else-if="loading"
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
        v-else-if="actors.length === 0"
        class="h-full flex items-center justify-center py-20"
      >
        <div 
          @click="showCreateDialog = true"
          :class="[
            'text-center rounded-lg border p-8 cursor-pointer transition-all',
            isDark 
              ? 'bg-gray-800 border-gray-700 hover:bg-gray-700 hover:border-gray-600' 
              : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
          ]"
        >
          <UserGroupIcon 
            class="w-16 h-16 mx-auto mb-4"
            :class="isDark ? 'text-gray-600' : 'text-gray-400'"
          />
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            暂无角色
          </h3>
          <p 
            :class="[
              'text-sm mb-4',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            点击此处或"新增角色"按钮开始添加角色
          </p>
        </div>
      </div>

      <!-- 角色列表 -->
      <div 
        v-else
        class="space-y-4"
      >
        <!-- 全选复选框（如果有角色） -->
        <div 
          v-if="actors.length > 0"
          :class="[
            'pb-2 mb-2 border-b',
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              :checked="isAllSelected"
              @change="toggleSelectAll"
              :class="[
                'w-4 h-4 rounded cursor-pointer',
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
              ]"
            />
            <span :class="['text-sm font-medium', isDark ? 'text-gray-300' : 'text-gray-700']">
              全选 (已选择 {{ selectedActorIds.size }} 项)
            </span>
          </label>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="actor in actors"
            :key="actor.actor_id"
            class="relative"
          >
            <!-- 复选框覆盖层 -->
            <div 
              class="absolute top-2 left-2 z-10"
              @click.stop
            >
              <input
                type="checkbox"
                :checked="selectedActorIds.has(actor.actor_id)"
                @change="toggleSelectActor(actor.actor_id)"
                :class="[
                  'w-5 h-5 rounded cursor-pointer shadow-lg',
                  isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
                ]"
              />
            </div>
            
            <!-- 选中高亮 -->
            <div
              v-if="selectedActorIds.has(actor.actor_id)"
              class="absolute inset-0 border-2 border-blue-500 rounded-lg pointer-events-none z-20"
              :class="isDark ? 'bg-blue-900/20' : 'bg-blue-100/30'"
            ></div>
            
            <ActorCard
              :actor="actor"
              @open-detail="openDetailDialog"
              @open-examples="openExamplesDialog"
              :on-delete="handleDelete"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑角色对话框 -->
    <Teleport to="body">
      <div
        v-if="showCreateDialog || editingActor"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="closeCreateDialog"
      >
        <div
          :class="[
            'w-full max-w-lg rounded-lg shadow-xl',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 
              :class="[
                'text-xl font-bold mb-4',
                isDark ? 'text-white' : 'text-gray-900'
              ]"
            >
              {{ editingActor ? '编辑角色' : '创建角色' }}
            </h2>

            <div class="space-y-4">
              <!-- 提示信息 -->
              <div 
                :class="[
                  'p-3 rounded-lg text-xs',
                  isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-50 text-gray-600'
                ]"
              >
                <p class="font-semibold mb-1">提示：</p>
                <p>• Actor 可以是角色、地点、组织等小说要素</p>
                <p>• 颜色建议：女性→粉色 #FF69B4，男性→蓝色 #4169E1，地点→绿色 #228B22</p>
              </div>

              <!-- 名称 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  名称 *
                </label>
                <input
                  v-model="actorForm.name"
                  type="text"
                  placeholder="如：主角、帝国、纽约"
                  :class="[
                    'w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
                    isDark
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  ]"
                />
              </div>

              <!-- 描述 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  描述
                </label>
                <textarea
                  v-model="actorForm.desc"
                  rows="3"
                  placeholder="简要描述"
                  :class="[
                    'w-full px-4 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
                    isDark
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  ]"
                ></textarea>
              </div>

              <!-- 颜色 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  颜色
                </label>
                <div class="flex items-center gap-2">
                  <input
                    v-model="actorForm.color"
                    type="color"
                    :class="[
                      'w-7 h-7 rounded-full border-2 cursor-pointer appearance-none',
                      isDark ? 'border-gray-600' : 'border-gray-300'
                    ]"
                    :style="{ backgroundColor: actorForm.color }"
                    title="点击选择颜色"
                  />
                  <input
                    v-model="actorForm.color"
                    type="text"
                    placeholder="#808080"
                    :class="[
                      'flex-1 px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    ]"
                  />
                </div>
              </div>
            </div>

            <!-- 对话框按钮 -->
            <div class="flex justify-end gap-3 mt-6">
              <button
                @click="closeCreateDialog"
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
                @click="saveActor"
                :disabled="!actorForm.name.trim() || saving"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  !actorForm.name.trim() || saving
                    ? isDark
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                ]"
              >
                {{ saving ? '保存中...' : (editingActor ? '保存' : '创建') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 统一确认对话框 -->
    <ConfirmDialog
      :show="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.show = false"
    />

    <!-- 角色详情对话框 -->
    <ActorDetailDialog
      :actor="detailActor"
      @close="detailActor = null"
      @edit="handleEdit"
      @generate="handleGenerate"
      @examples="openExamplesDialog"
      @refresh="handleRefresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import { UserGroupIcon, PlusIcon, TrashIcon } from '@heroicons/vue/24/outline'
import ActorCard from '../components/ActorCard.vue'
import ActorDetailDialog from '../components/ActorDetailDialog.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { showToast } from '../utils/toast'
import api from '../api'

interface Actor {
  actor_id: string
  project_id: string
  name: string
  desc: string
  color: string
  tags: Record<string, string>
  examples: any[]
}

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { selectedProjectId } = storeToRefs(projectStore)

const loading = ref(false)
const actors = ref<Actor[]>([])
const showCreateDialog = ref(false)
const editingActor = ref<Actor | null>(null)
const actorToDelete = ref<Actor | null>(null)
const detailActor = ref<Actor | null>(null)
const saving = ref(false)
const deleting = ref(false)

// 多选状态
const selectedActorIds = ref<Set<string>>(new Set())

// 统一确认对话框
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {}
})

// 表单数据
const actorForm = ref({
  name: '',
  desc: '',
  color: '#808080'
})

// 加载角色列表
const loadActors = async () => {
  if (!selectedProjectId.value) {
    actors.value = []
    return
  }

  loading.value = true
  try {
    const data = await api.get('/actor/all', {
      params: {
        project_id: selectedProjectId.value,
        limit: 1000
      }
    })
    actors.value = Array.isArray(data) ? data : []
  } catch (error: any) {
    console.error('加载角色列表失败:', error)
    actors.value = []
  } finally {
    loading.value = false
  }
}

// 关闭创建对话框
const closeCreateDialog = () => {
  showCreateDialog.value = false
  editingActor.value = null
  actorForm.value = {
    name: '',
    desc: '',
    color: '#808080'
  }
}

// 保存角色（创建或更新）
const saveActor = async () => {
  if (!selectedProjectId.value || !actorForm.value.name.trim()) {
    return
  }

  saving.value = true
  try {
    let actorId: string | null = null
    if (editingActor.value) {
      // 更新角色
      await api.put(`/actor/${editingActor.value.actor_id}`, {
        name: actorForm.value.name.trim(),
        desc: actorForm.value.desc.trim(),
        color: actorForm.value.color.trim()
      })
      actorId = editingActor.value.actor_id
    } else {
      // 创建角色
      const result = await api.post('/actor/create', null, {
        params: {
          project_id: selectedProjectId.value,
          name: actorForm.value.name.trim(),
          desc: actorForm.value.desc.trim(),
          color: actorForm.value.color.trim()
        }
      })
      actorId = result.actor_id
      
      // 创建角色后，自动创建一个生成角色立绘的任务
      try {
        const taskName = `角色立绘 - ${actorForm.value.name.trim()}`
        const taskDescParts: string[] = []
        if (actorForm.value.desc.trim()) {
          taskDescParts.push(actorForm.value.desc.trim())
        }
        const taskDesc = taskDescParts.join('\n')
        
        // 调用 AI 生成参数 API
        const paramsResponse = await api.post('/llm/generate-draw-params', {
          name: taskName,
          desc: taskDesc || undefined
        })
        
        if (paramsResponse.success && paramsResponse.params) {
          const params = paramsResponse.params
          const lorasDict: Record<string, number> = params.loras || {}
          
          // 创建绘图任务
          await api.post('/draw', null, {
            params: {
              name: taskName,
              desc: taskDesc || undefined,
              model: params.model,
              prompt: params.prompt,
              negative_prompt: params.negative_prompt,
              sampler_name: params.sampler_name || params.sampler,
              steps: params.steps,
              cfg_scale: params.cfg_scale,
              width: params.width,
              height: params.height,
              seed: params.seed,
              clip_skip: params.clip_skip || undefined,
              vae: params.vae || undefined,
              loras: Object.keys(lorasDict).length > 0 ? JSON.stringify(lorasDict) : undefined
            }
          })
          
          showToast('角色创建成功，已自动提交立绘生成任务', 'success')
        }
      } catch (error: any) {
        // 如果自动创建任务失败，不影响角色创建，只记录错误
        console.error('自动创建立绘任务失败:', error)
        showToast('角色创建成功，但自动创建立绘任务失败', 'warning')
      }
    }
    
    closeCreateDialog()
    await loadActors()
  } catch (error: any) {
    console.error('保存角色失败:', error)
    alert('保存角色失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

// 打开详情对话框
const openDetailDialog = (actor: Actor) => {
  detailActor.value = actor
}

// 编辑角色
const handleEdit = (actor: Actor) => {
  editingActor.value = actor
  actorForm.value = {
    name: actor.name,
    desc: actor.desc,
    color: actor.color || '#808080'
  }
  detailActor.value = null
  showCreateDialog.value = true
}

// 生成立绘
const handleGenerate = (actor: Actor) => {
  // 生成立绘对话框待实现
  console.log('生成立绘:', actor)
}

// 打开示例图对话框
const openExamplesDialog = (actor: Actor) => {
  // 示例图对话框待实现
  console.log('打开示例图:', actor)
}

// 全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedActorIds.value.clear()
  } else {
    actors.value.forEach(actor => {
      selectedActorIds.value.add(actor.actor_id)
    })
  }
}

// 是否全选
const isAllSelected = computed(() => {
  return actors.value.length > 0 && selectedActorIds.value.size === actors.value.length
})

// 切换单个角色的选择状态
const toggleSelectActor = (actorId: string) => {
  if (selectedActorIds.value.has(actorId)) {
    selectedActorIds.value.delete(actorId)
  } else {
    selectedActorIds.value.add(actorId)
  }
}

// 删除选中的角色
const handleDeleteSelected = () => {
  const count = selectedActorIds.value.size
  if (count === 0) return

  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除选中的 ${count} 个角色吗？此操作不可恢复！\n\n⚠️ 此操作将删除角色的所有示例图片和标签，且不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      deleting.value = true
      try {
        const actorIds = Array.from(selectedActorIds.value)
        for (const actorId of actorIds) {
          await api.delete(`/actor/${actorId}`)
        }
        
        selectedActorIds.value.clear()
        await loadActors()
        showToast(`成功删除 ${count} 个角色`, 'success')
      } catch (error: any) {
        console.error('批量删除角色失败:', error)
        showToast('删除失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        deleting.value = false
      }
    }
  }
}

// 清空所有角色
const handleClearAll = () => {
  if (actors.value.length === 0) return

  confirmDialog.value = {
    show: true,
    title: '确认清空所有角色',
    message: `即将删除当前项目的所有角色（共 ${actors.value.length} 个）\n\n⚠️ 此操作将删除角色的所有示例图片和标签，且不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      deleting.value = true
      try {
        // 逐个删除所有角色
        for (const actor of actors.value) {
          await api.delete(`/actor/${actor.actor_id}`)
        }
        
        selectedActorIds.value.clear()
        await loadActors()
        showToast(`成功删除所有角色`, 'success')
      } catch (error: any) {
        console.error('清空角色失败:', error)
        showToast('清空失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        deleting.value = false
      }
    }
  }
}

// 删除角色
const handleDelete = (actor: Actor) => {
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除角色 "${actor.name}" 吗？\n\n⚠️ 此操作将删除角色的所有示例图片和标签，且不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      deleting.value = true
      try {
        await api.delete(`/actor/${actor.actor_id}`)
        
        // 清除已删除角色的选中状态
        selectedActorIds.value.delete(actor.actor_id)
        await loadActors()
        showToast('角色已删除', 'success')
      } catch (error: any) {
        console.error('删除角色失败:', error)
        showToast('删除角色失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        deleting.value = false
      }
    }
  }
}

// 刷新角色列表（用于详情对话框更新后刷新）
const handleRefresh = async () => {
  await loadActors()
  // 如果详情对话框打开，更新其数据
  if (detailActor.value) {
    const updatedActor = actors.value.find(a => a.actor_id === detailActor.value?.actor_id)
    if (updatedActor) {
      detailActor.value = updatedActor
    }
  }
}

// 检查是否有正在生成的立绘
const hasGeneratingPortrait = computed(() => {
  return actors.value.some(actor => 
    actor.examples && actor.examples.some((ex: any) => !ex.image_path)
  )
})

// 每5秒刷新一次（如果有正在生成的立绘）
let refreshTimer: ReturnType<typeof setInterval> | null = null

watch([hasGeneratingPortrait, selectedProjectId], ([hasGenerating, projectId]) => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  
  // 如果有正在生成的立绘且项目有效，启动定时刷新
  if (hasGenerating && projectId) {
    refreshTimer = setInterval(async () => {
      await loadActors()
      // 如果详情对话框打开，更新其数据
      if (detailActor.value) {
        const updatedActor = actors.value.find(a => a.actor_id === detailActor.value?.actor_id)
        if (updatedActor) {
          detailActor.value = updatedActor
        }
      }
    }, 5000) // 每5秒刷新一次
  }
}, { immediate: true })

// 监听项目变化
watch(() => selectedProjectId.value, () => {
  loadActors()
})

// 监听创建对话框打开，初始化表单
watch(showCreateDialog, (newVal) => {
  if (newVal && editingActor.value) {
    actorForm.value = {
      name: editingActor.value.name,
      desc: editingActor.value.desc,
      color: editingActor.value.color || '#808080'
    }
  }
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

onMounted(async () => {
  // 初始化 store（从 localStorage 恢复项目ID）
  projectStore.init()
  
  // 确保项目列表已加载
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  
  // 加载角色列表
  loadActors()
})
</script>
