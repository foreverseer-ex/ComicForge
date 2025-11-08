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
      
      <div class="flex items-center gap-2">
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
        <button
          v-if="actors.length > 0"
          @click="handleClearAll"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'
          ]"
          title="清空所有角色"
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
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="actor in actors"
            :key="actor.actor_id"
          >
            <ActorCard
              :actor="actor"
              :privacy-mode="privacyMode"
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
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'
import { UserGroupIcon, PlusIcon, TrashIcon, EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
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

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

// 切换隐私模式
const togglePrivacyMode = () => {
  privacyStore.togglePrivacyMode()
}

const loading = ref(false)
const actors = ref<Actor[]>([])
const showCreateDialog = ref(false)
const editingActor = ref<Actor | null>(null)
const detailActor = ref<Actor | null>(null)
const saving = ref(false)
const deleting = ref(false)

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
  loading.value = true
  try {
    const data = await api.get('/actor/all', {
      params: {
        project_id: selectedProjectId.value || null,
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
  if (!actorForm.value.name.trim()) {
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
      // 创建角色（如果没有项目，使用 null 作为 project_id）
      const result = await api.post('/actor/create', null, {
        params: {
          project_id: selectedProjectId.value || null,
          name: actorForm.value.name.trim(),
          desc: actorForm.value.desc.trim(),
          color: actorForm.value.color.trim()
        }
      })
      actorId = result.actor_id
      showToast('角色创建成功', 'success')
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
  // 先保存当前 detailActor 的 ID
  const currentActorId = detailActor.value?.actor_id
  
  // 重新加载所有角色
  await loadActors()
  
  // 如果详情对话框打开，更新其数据
  if (currentActorId && detailActor.value) {
    const updatedActor = actors.value.find(a => a.actor_id === currentActorId)
    if (updatedActor) {
      // 创建新对象，确保响应式系统检测到变化
      // 特别注意：需要深拷贝 examples 数组，确保顺序变化能被检测到
      detailActor.value = {
        ...updatedActor,
        examples: [...updatedActor.examples]
      }
    }
  }
}

// 检查是否有正在生成的立绘
const hasGeneratingPortrait = computed(() => {
  return actors.value.some(actor => 
    actor.examples && actor.examples.some((ex: any) => !ex.image_path)
  )
})

// 每5秒检查一次正在生成的立绘状态（如果有正在生成的立绘）
let refreshTimer: ReturnType<typeof setInterval> | null = null
// 保存上一次的 actors 状态快照，用于比较是否有变化
let lastActorsState = ref<string>('')

watch([hasGeneratingPortrait, selectedProjectId], ([hasGenerating, projectId]) => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  
  // 初始化状态快照
  if (actors.value.length > 0) {
    lastActorsState.value = JSON.stringify(actors.value.map(actor => ({
      actor_id: actor.actor_id,
      examples: actor.examples?.map((ex: any) => ({
        image_path: ex.image_path,
        title: ex.title
      })) || []
    })))
  }
  
  // 如果有正在生成的立绘，启动定时检查（只检查状态变化，不刷新整个页面）
  // 支持 project_id=None（默认工作空间）
  if (hasGenerating) {
    refreshTimer = setInterval(async () => {
      try {
        // 只获取有正在生成立绘的 actor 列表，检查是否有变化
        const response = await api.get(`/actor/all`, {
          params: {
            project_id: projectId || null,
            limit: 1000
          }
        })
        
        if (response && Array.isArray(response)) {
          // 比较当前状态和上次状态
          const currentState = JSON.stringify(response.map((actor: any) => ({
            actor_id: actor.actor_id,
            examples: actor.examples?.map((ex: any) => ({
              image_path: ex.image_path,
              title: ex.title
            })) || []
          })))
          
          // 如果有变化（比如 image_path 从 null 变成了有值），才更新
          if (currentState !== lastActorsState.value) {
            lastActorsState.value = currentState
            
            // 只更新 actors 列表，不触发整个页面刷新
            // 智能更新：只更新有变化的 actor
            response.forEach((updatedActor: any) => {
              const existingIndex = actors.value.findIndex(a => a.actor_id === updatedActor.actor_id)
              if (existingIndex >= 0) {
                // 检查这个 actor 的 examples 是否有变化
                const existingActor = actors.value[existingIndex]
                const existingExamplesState = JSON.stringify(existingActor.examples?.map((ex: any) => ({
                  image_path: ex.image_path,
                  title: ex.title
                })) || [])
                const updatedExamplesState = JSON.stringify(updatedActor.examples?.map((ex: any) => ({
                  image_path: ex.image_path,
                  title: ex.title
                })) || [])
                
                // 只有 examples 有变化时才更新
                if (existingExamplesState !== updatedExamplesState) {
                  actors.value[existingIndex] = { ...updatedActor, examples: [...updatedActor.examples] }
                  
                  // 如果详情对话框打开且是当前 actor，更新其数据
                  if (detailActor.value && detailActor.value.actor_id === updatedActor.actor_id) {
                    detailActor.value = { ...updatedActor, examples: [...updatedActor.examples] }
                  }
                }
              } else {
                // 新 actor，添加到列表
                actors.value.push(updatedActor)
              }
            })
          }
          // 如果没有变化，不进行任何操作，避免刷新页面
        }
      } catch (error) {
        console.error('检查立绘状态失败:', error)
      }
    }, 5000) // 每5秒检查一次
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
