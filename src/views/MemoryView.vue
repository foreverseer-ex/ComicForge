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
        <svg class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          记忆管理
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="memories.length > 0"
          @click="selectedMemoryIds.size > 0 ? handleDeleteSelected() : handleClearAll()"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'
          ]"
          :title="selectedMemoryIds.size > 0 ? `删除选中 (${selectedMemoryIds.size})` : '清空所有记忆'"
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
          title="新增记忆"
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
        v-else-if="memories.length === 0"
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
          <svg 
            class="w-16 h-16 mx-auto mb-4"
            :class="isDark ? 'text-gray-600' : 'text-gray-400'"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            暂无记忆条目
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            点击此处开始添加记忆
          </p>
        </div>
      </div>

      <!-- 记忆列表 -->
      <div 
        v-else
        class="space-y-4"
      >
        <!-- 全选复选框（如果有记忆） -->
        <div 
          v-if="memories.length > 0"
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
              全选 (已选择 {{ selectedMemoryIds.size }} 项)
            </span>
          </label>
        </div>
        <div
          v-for="memory in memories"
          :key="memory.memory_id"
          :class="[
            'rounded-lg border p-6 transition-shadow hover:shadow-md',
            isDark 
              ? selectedMemoryIds.has(memory.memory_id)
                ? 'bg-gray-800 border-gray-600' 
                : 'bg-gray-800 border-gray-700'
              : selectedMemoryIds.has(memory.memory_id)
                ? 'bg-blue-50 border-blue-300'
                : 'bg-white border-gray-200'
          ]"
        >
          <!-- 记忆卡片头部 -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-start gap-3 flex-1">
              <!-- 复选框 -->
              <input
                type="checkbox"
                :checked="selectedMemoryIds.has(memory.memory_id)"
                @change="toggleSelectMemory(memory.memory_id)"
                :class="[
                  'w-4 h-4 rounded cursor-pointer mt-1',
                  isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
                ]"
                @click.stop
              />
              <div class="flex-1">
                <h3 
                  :class="[
                    'text-lg font-semibold mb-1',
                    isDark ? 'text-white' : 'text-gray-900'
                  ]"
                >
                  {{ memory.key }}
                </h3>
                <p 
                  v-if="memory.description"
                  :class="[
                    'text-sm italic',
                    isDark ? 'text-gray-400' : 'text-gray-500'
                  ]"
                >
                  {{ memory.description }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button
                @click.stop="editMemory(memory)"
                :class="[
                  'p-2 rounded-lg transition-colors',
                  isDark
                    ? 'hover:bg-gray-700 text-gray-300 hover:text-blue-400'
                    : 'hover:bg-gray-100 text-gray-600 hover:text-blue-600'
                ]"
                title="编辑"
              >
                <PencilIcon class="w-5 h-5" />
              </button>
              <button
                @click.stop="deleteMemory(memory)"
                :class="[
                  'p-2 rounded-lg transition-colors',
                  isDark
                    ? 'hover:bg-gray-700 text-gray-300 hover:text-red-400'
                    : 'hover:bg-gray-100 text-gray-600 hover:text-red-600'
                ]"
                title="删除"
              >
                <TrashIcon class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- 分隔线 -->
          <div 
            :class="[
              'border-t mb-3',
              isDark ? 'border-gray-700' : 'border-gray-200'
            ]"
          ></div>

          <!-- 记忆内容 -->
          <div 
            :class="[
              'text-sm mb-3 whitespace-pre-wrap break-words',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            {{ memory.value }}
          </div>

          <!-- 时间信息 -->
          <div 
            :class="[
              'text-xs',
              isDark ? 'text-gray-500' : 'text-gray-400'
            ]"
          >
            创建时间: {{ formatDateTime(memory.created_at) }}
            <span v-if="memory.updated_at !== memory.created_at" class="ml-4">
              更新时间: {{ formatDateTime(memory.updated_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑记忆对话框 -->
    <Teleport to="body">
      <div
        v-if="showCreateDialog || editingMemory"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="closeDialog"
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
              {{ editingMemory ? '编辑记忆' : '新增记忆' }}
            </h2>

            <div class="space-y-4">
              <!-- 键名输入 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  记忆键名
                </label>
                <div class="flex gap-2">
                  <input
                    v-model="memoryForm.key"
                    type="text"
                    placeholder="例如：作品类型、主题、背景设定等"
                    :class="[
                      'flex-1 px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    ]"
                  />
                  <button
                    @click="showKeySelector = !showKeySelector"
                    :class="[
                      'px-3 py-2 rounded-lg border transition-colors',
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    ]"
                    title="选择预定义键"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
                <!-- 预定义键选择器 -->
                <div 
                  v-if="showKeySelector"
                  :class="[
                    'mt-2 p-3 rounded-lg border max-h-48 overflow-y-auto',
                    isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                  ]"
                >
                  <div class="space-y-2">
                    <div>
                      <p :class="['text-xs font-semibold mb-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        小说相关记忆
                      </p>
                      <div class="space-y-1">
                        <button
                          v-for="(desc, key) in novelKeys"
                          :key="key"
                          @click="selectKey(key)"
                          :class="[
                            'w-full text-left px-2 py-1 rounded text-sm transition-colors',
                            isDark
                              ? 'hover:bg-gray-600 text-gray-300'
                              : 'hover:bg-gray-200 text-gray-700'
                          ]"
                        >
                          <span class="font-medium">{{ key }}</span>
                          <span :class="['text-xs ml-2', isDark ? 'text-gray-500' : 'text-gray-500']">
                            - {{ desc }}
                          </span>
                        </button>
                      </div>
                    </div>
                    <div 
                      :class="[
                        'border-t pt-2 mt-2',
                        isDark ? 'border-gray-600' : 'border-gray-200'
                      ]"
                    >
                      <p :class="['text-xs font-semibold mb-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        用户偏好相关记忆
                      </p>
                      <div class="space-y-1">
                        <button
                          v-for="(desc, key) in userKeys"
                          :key="key"
                          @click="selectKey(key)"
                          :class="[
                            'w-full text-left px-2 py-1 rounded text-sm transition-colors',
                            isDark
                              ? 'hover:bg-gray-600 text-gray-300'
                              : 'hover:bg-gray-200 text-gray-700'
                          ]"
                        >
                          <span class="font-medium">{{ key }}</span>
                          <span :class="['text-xs ml-2', isDark ? 'text-gray-500' : 'text-gray-500']">
                            - {{ desc }}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 键描述提示 -->
                <p 
                  v-if="memoryForm.key && predefinedKeys[memoryForm.key]"
                  :class="[
                    'mt-1 text-xs',
                    isDark ? 'text-gray-400' : 'text-gray-500'
                  ]"
                >
                  {{ predefinedKeys[memoryForm.key] }}
                </p>
              </div>

              <!-- 内容输入 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  记忆内容
                </label>
                <textarea
                  v-model="memoryForm.value"
                  rows="4"
                  placeholder="输入记忆的具体内容"
                  :class="[
                    'w-full px-4 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
                    isDark
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  ]"
                ></textarea>
              </div>

              <!-- 说明输入 -->
              <div>
                <label 
                  :class="[
                    'block text-sm font-medium mb-2',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  说明{{ isPredefinedKey ? '（自动填充）' : '（可选）' }}
                </label>
                <input
                  v-model="memoryForm.description"
                  type="text"
                  :placeholder="isPredefinedKey ? '预定义键的说明' : '对这条记忆的补充说明'"
                  :disabled="isPredefinedKey"
                  :class="[
                    'w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
                    isDark
                      ? isPredefinedKey
                        ? 'bg-gray-800 border-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                      : isPredefinedKey
                        ? 'bg-gray-100 border-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                  ]"
                />
              </div>
            </div>

            <!-- 对话框按钮 -->
            <div class="flex justify-end gap-3 mt-6">
              <button
                @click="closeDialog"
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
                @click="saveMemory"
                :disabled="!memoryForm.key.trim() || !memoryForm.value.trim() || saving"
                :class="[
                  'px-4 py-2 rounded-lg font-medium transition-colors',
                  !memoryForm.key.trim() || !memoryForm.value.trim() || saving
                    ? isDark
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                ]"
              >
                {{ saving ? '保存中...' : (editingMemory ? '保存' : '创建') }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import api from '../api'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline'
import { showToast } from '../utils/toast'
import ConfirmDialog from '../components/ConfirmDialog.vue'

interface MemoryEntry {
  memory_id: string
  project_id: string
  key: string
  value: string
  description?: string | null
  created_at: string
  updated_at: string
}

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { selectedProjectId } = storeToRefs(projectStore)

// 数据
const memories = ref<MemoryEntry[]>([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

// 对话框状态
const showCreateDialog = ref(false)
const editingMemory = ref<MemoryEntry | null>(null)
const showKeySelector = ref(false)
const clearing = ref(false)

// 多选状态
const selectedMemoryIds = ref<Set<string>>(new Set())

// 统一确认对话框
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {}
})

// 表单数据
const memoryForm = ref({
  key: '',
  value: '',
  description: ''
})

// 预定义键
const predefinedKeys = ref<Record<string, string>>({})
const novelKeys = ref<Record<string, string>>({})
const userKeys = ref<Record<string, string>>({})

// 加载预定义键
const loadPredefinedKeys = async () => {
  try {
    const keys = await api.get('/memory/key-descriptions')
    predefinedKeys.value = keys
    
    // 分离小说相关和用户偏好相关的键
    const novelKeysMap: Record<string, string> = {}
    const userKeysMap: Record<string, string> = {}
    
    // 小说相关的键（根据常量文件中的定义）
    const novelKeyNames = ['作品类型', '小说主题', '背景设定', '主要地点', '故事梗概']
    // 用户偏好相关的键（根据常量文件中的定义）
    const userKeyNames = [
      '小说主题偏好', '主角性格偏好', '情节元素偏好', '叙事风格偏好',
      '艺术风格偏好', '画面元素偏好', '避免的标签', '喜欢的标签',
      '角色外貌偏好', '角色服装偏好', '补充说明'
    ]
    
    for (const [key, desc] of Object.entries(keys)) {
      if (novelKeyNames.includes(key)) {
        novelKeysMap[key] = desc
      } else if (userKeyNames.includes(key)) {
        userKeysMap[key] = desc
      }
    }
    
    novelKeys.value = novelKeysMap
    userKeys.value = userKeysMap
  } catch (error) {
    console.error('加载预定义键失败:', error)
  }
}

// 加载记忆列表
const loadMemories = async () => {
  loading.value = true
  try {
    const data = await api.get('/memory/all', {
      params: {
        project_id: selectedProjectId.value || null,
        limit: 1000
      }
    })
    memories.value = data || []
  } catch (error: any) {
    console.error('加载记忆失败:', error)
    showToast('加载记忆失败: ' + (error.response?.data?.detail || error.message), 'error')
    memories.value = []
  } finally {
    loading.value = false
  }
}

// 判断是否是预定义键
const isPredefinedKey = computed(() => {
  return memoryForm.value.key && predefinedKeys.value[memoryForm.value.key]
})

// 选择预定义键
const selectKey = (key: string) => {
  memoryForm.value.key = key
  showKeySelector.value = false
  
  // 如果选择了预定义键，强制更新描述
  if (predefinedKeys.value[key]) {
    memoryForm.value.description = predefinedKeys.value[key]
  }
}

// 监听键名变化，如果选择的是预定义键，自动更新说明
watch(() => memoryForm.value.key, (newKey) => {
  if (newKey && predefinedKeys.value[newKey]) {
    memoryForm.value.description = predefinedKeys.value[newKey]
  }
})

// 关闭对话框
const closeDialog = () => {
  showCreateDialog.value = false
  editingMemory.value = null
  showKeySelector.value = false
  memoryForm.value = {
    key: '',
    value: '',
    description: ''
  }
}

// 编辑记忆
const editMemory = (memory: MemoryEntry) => {
  editingMemory.value = memory
  memoryForm.value = {
    key: memory.key,
    value: memory.value,
    description: memory.description || ''
  }
}

// 保存记忆
const saveMemory = async () => {
  if (!memoryForm.value.key.trim() || !memoryForm.value.value.trim()) {
    return
  }

  saving.value = true
  try {
    if (editingMemory.value) {
      // 更新记忆
      await api.put(`/memory/${editingMemory.value.memory_id}`, {
        key: memoryForm.value.key.trim(),
        value: memoryForm.value.value.trim(),
        description: memoryForm.value.description.trim() || null
      })
    } else {
      // 创建记忆（如果没有项目，使用 null 作为 project_id）
      await api.post('/memory/create', {
        project_id: selectedProjectId.value || null,
        key: memoryForm.value.key.trim(),
        value: memoryForm.value.value.trim(),
        description: memoryForm.value.description.trim() || null
      })
    }
    
    closeDialog()
    await loadMemories()
    showToast(editingMemory.value ? '记忆已更新' : '记忆已创建', 'success')
  } catch (error: any) {
    console.error('保存记忆失败:', error)
    showToast('保存记忆失败: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    saving.value = false
  }
}

// 删除记忆
const deleteMemory = (memory: MemoryEntry) => {
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除记忆 "${memory.key}" 吗？此操作不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      const memoryId = memory.memory_id
      deleting.value = true
      try {
        await api.delete(`/memory/${memoryId}`)
        
        // 清除已删除记忆的选中状态
        selectedMemoryIds.value.delete(memoryId)
        await loadMemories()
        showToast('记忆已删除', 'success')
      } catch (error: any) {
        console.error('删除记忆失败:', error)
        showToast('删除记忆失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        deleting.value = false
      }
    }
  }
}

// 全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedMemoryIds.value.clear()
  } else {
    memories.value.forEach(memory => {
      selectedMemoryIds.value.add(memory.memory_id)
    })
  }
}

// 是否全选
const isAllSelected = computed(() => {
  return memories.value.length > 0 && selectedMemoryIds.value.size === memories.value.length
})

// 切换单个记忆的选择状态
const toggleSelectMemory = (memoryId: string) => {
  if (selectedMemoryIds.value.has(memoryId)) {
    selectedMemoryIds.value.delete(memoryId)
  } else {
    selectedMemoryIds.value.add(memoryId)
  }
}

// 删除选中的记忆
const handleDeleteSelected = async () => {
  const count = selectedMemoryIds.value.size
  if (count === 0) return

  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: `确定要删除选中的 ${count} 条记忆吗？此操作不可恢复！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        // 批量删除
        const memoryIds = Array.from(selectedMemoryIds.value)
        for (const memoryId of memoryIds) {
          await api.delete(`/memory/${memoryId}`)
        }
        
        selectedMemoryIds.value.clear()
        await loadMemories()
        showToast(`成功删除 ${count} 条记忆`, 'success')
      } catch (error: any) {
        console.error('批量删除记忆失败:', error)
        showToast('删除失败: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  }
}

// 清空所有记忆
const handleClearAll = () => {
  confirmDialog.value = {
    show: true,
    title: '确认清空所有记忆',
    message: `即将清空当前项目的所有记忆条目（共 ${memories.value.length} 条）\n\n⚠️ 此操作不可恢复，所有记忆将被永久删除！`,
    onConfirm: async () => {
      confirmDialog.value.show = false
      clearing.value = true
      try {
        const result = await api.delete('/memory/clear', {
          params: {
            project_id: selectedProjectId.value || null
          }
        })
        
        selectedMemoryIds.value.clear()
        await loadMemories()
        showToast(`已清空 ${result.deleted_count || 0} 条记忆`, 'success')
      } catch (error: any) {
        console.error('清空记忆失败:', error)
        showToast('清空记忆失败: ' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        clearing.value = false
      }
    }
  }
}

// 截断值显示
const truncateValue = (value: string, maxLength: number = 100): string => {
  if (value.length <= maxLength) {
    return value
  }
  return value.substring(0, maxLength) + '...'
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 监听项目变化
watch(() => selectedProjectId.value, () => {
  loadMemories()
})

// 初始化
onMounted(() => {
  loadPredefinedKeys()
  loadMemories()
})
</script>
