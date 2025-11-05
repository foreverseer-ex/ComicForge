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
      
      <button
        v-if="selectedProjectId"
        @click="showCreateDialog = true"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
          isDark
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        ]"
      >
        <PlusIcon class="w-5 h-5" />
        新增角色
      </button>
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
          :class="[
            'text-center rounded-lg border p-8',
            isDark 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
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
            点击"新增角色"按钮开始添加角色
          </p>
        </div>
      </div>

      <!-- 角色列表 -->
      <div 
        v-else
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        <ActorCard
          v-for="actor in actors"
          :key="actor.actor_id"
          :actor="actor"
          @open-detail="openDetailDialog"
          @open-examples="openExamplesDialog"
          :on-delete="handleDelete"
        />
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
                      'h-10 w-20 rounded border cursor-pointer',
                      isDark ? 'border-gray-600' : 'border-gray-300'
                    ]"
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

    <!-- 删除确认对话框 -->
    <Teleport to="body">
      <div
        v-if="actorToDelete"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="actorToDelete = null"
      >
        <div
          :class="[
            'w-full max-w-md rounded-lg shadow-xl',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 
              :class="[
                'text-xl font-bold mb-4 text-red-600'
              ]"
            >
              确认删除
            </h2>
            <p 
              :class="[
                'mb-4',
                isDark ? 'text-gray-300' : 'text-gray-700'
              ]"
            >
              即将删除以下角色：
            </p>
            <div 
              :class="[
                'p-3 rounded-lg mb-4',
                isDark ? 'bg-gray-700' : 'bg-gray-50'
              ]"
            >
              <p :class="['font-semibold', isDark ? 'text-white' : 'text-gray-900']">
                名称：{{ actorToDelete?.name }}
              </p>
              <p :class="['text-sm mt-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                描述：{{ actorToDelete?.desc || '无' }}
              </p>
            </div>
            <p 
              :class="[
                'text-sm mb-4 text-red-600 font-semibold'
              ]"
            >
              ⚠️ 此操作将删除角色的所有示例图片和标签，且不可恢复！
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="actorToDelete = null"
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
                @click="confirmDelete"
                :disabled="deleting"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  deleting
                    ? 'bg-gray-400 cursor-not-allowed text-white'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                ]"
              >
                {{ deleting ? '删除中...' : '确认删除' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 角色详情对话框 -->
    <ActorDetailDialog
      :actor="detailActor"
      @close="detailActor = null"
      @edit="handleEdit"
      @generate="handleGenerate"
      @examples="openExamplesDialog"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import { UserGroupIcon, PlusIcon } from '@heroicons/vue/24/outline'
import ActorCard from '../components/ActorCard.vue'
import ActorDetailDialog from '../components/ActorDetailDialog.vue'
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
    const data = await api.get('/actor/', {
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
    if (editingActor.value) {
      // 更新角色
      await api.put(`/actor/${editingActor.value.actor_id}`, null, {
        params: {
          project_id: selectedProjectId.value,
          name: actorForm.value.name.trim(),
          desc: actorForm.value.desc.trim(),
          color: actorForm.value.color.trim()
        }
      })
    } else {
      // 创建角色
      await api.post('/actor/create', null, {
        params: {
          project_id: selectedProjectId.value,
          name: actorForm.value.name.trim(),
          desc: actorForm.value.desc.trim(),
          color: actorForm.value.color.trim()
        }
      })
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

// 删除角色
const handleDelete = (actor: Actor) => {
  actorToDelete.value = actor
}

// 确认删除
const confirmDelete = async () => {
  if (!selectedProjectId.value || !actorToDelete.value) {
    return
  }

  deleting.value = true
  try {
    await api.delete(`/actor/${actorToDelete.value.actor_id}`, {
      params: {
        project_id: selectedProjectId.value
      }
    })
    
    actorToDelete.value = null
    await loadActors()
  } catch (error: any) {
    console.error('删除角色失败:', error)
    alert('删除角色失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deleting.value = false
  }
}

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

onMounted(() => {
  loadActors()
})
</script>
