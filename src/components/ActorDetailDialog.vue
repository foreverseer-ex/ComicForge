<template>
  <Teleport to="body">
    <div
      v-if="actor"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="close"
    >
      <div
        :class="[
          'w-full max-w-4xl max-h-[90vh] rounded-lg shadow-xl flex flex-col',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 标题栏 -->
        <div 
          :class="[
            'flex items-center justify-between p-4 border-b',
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <h2 
            :class="[
              'text-xl font-bold',
              isDark ? 'text-white' : 'text-gray-900'
            ]"
          >
            角色详情
          </h2>
          <button
            @click="close"
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

        <!-- 内容区域 -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-6">
            <!-- 立绘展示区域 -->
            <div>
              <div 
                v-if="firstExample"
                :class="[
                  'w-full h-64 rounded-lg overflow-hidden border flex items-center justify-center',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
              >
                <img
                  :src="getExampleImageUrl(firstExample, 0)"
                  :alt="actor.name"
                  class="w-full h-full object-contain"
                  @error="handleImageError"
                />
              </div>
              <div 
                v-else
                @click="openGenerateDialog"
                :class="[
                  'w-full h-64 rounded-lg border flex flex-col items-center justify-center cursor-pointer transition-colors',
                  isDark ? 'border-gray-600 bg-gray-900 hover:bg-gray-800' : 'border-gray-200 bg-gray-50 hover:bg-gray-100'
                ]"
              >
                <PhotoIcon class="w-16 h-16 mb-2" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
                <span :class="['text-sm', isDark ? 'text-gray-500' : 'text-gray-500']">暂无立绘</span>
                <span :class="['text-xs mt-1', isDark ? 'text-gray-600' : 'text-gray-400']">点击生成</span>
              </div>
            </div>

            <!-- 基本信息 -->
            <div>
              <h3 
                :class="[
                  'text-lg font-semibold mb-3',
                  isDark ? 'text-white' : 'text-gray-900'
                ]"
              >
                基本信息
              </h3>
              <div class="space-y-3">
                <!-- 名称 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-16 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    名称:
                  </span>
                  <div class="flex-1 flex items-center gap-2">
                    <template v-if="editingField === 'name'">
                      <input
                        v-model="editingName"
                        type="text"
                        :class="[
                          'flex-1 px-2 py-1 rounded border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
                          isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
                        ]"
                        @keydown.enter="saveName"
                        @keydown.esc="cancelEdit"
                        ref="nameInputRef"
                      />
                      <button
                        @click="saveName"
                        :class="['text-green-500 hover:text-green-600']"
                        title="保存"
                      >
                        ✓
                      </button>
                      <button
                        @click="cancelEdit"
                        :class="['text-red-500 hover:text-red-600']"
                        title="取消"
                      >
                        ✗
                      </button>
                    </template>
                    <template v-else>
                      <span :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        {{ actor.name }}
                      </span>
                      <button
                        @click="startEditName"
                        :class="[
                          'p-1 rounded hover:bg-gray-700 transition-colors',
                          isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
                        ]"
                        title="编辑"
                      >
                        <PencilIcon class="w-4 h-4" />
                      </button>
                    </template>
                  </div>
                </div>

                <!-- 描述 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-16 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    描述:
                  </span>
                  <div class="flex-1 flex items-start gap-2">
                    <template v-if="editingField === 'desc'">
                      <textarea
                        v-model="editingDesc"
                        rows="3"
                        :class="[
                          'flex-1 px-2 py-1 rounded border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
                          isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
                        ]"
                        @keydown.ctrl.enter="saveDesc"
                        @keydown.meta.enter="saveDesc"
                        @keydown.esc="cancelEdit"
                        ref="descInputRef"
                      />
                      <div class="flex flex-col gap-1">
                        <button
                          @click="saveDesc"
                          :class="['text-green-500 hover:text-green-600']"
                          title="保存"
                        >
                          ✓
                        </button>
                        <button
                          @click="cancelEdit"
                          :class="['text-red-500 hover:text-red-600']"
                          title="取消"
                        >
                          ✗
                        </button>
                      </div>
                    </template>
                    <template v-else>
                      <span :class="['text-sm flex-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        {{ actor.desc || '无' }}
                      </span>
                      <button
                        @click="startEditDesc"
                        :class="[
                          'p-1 rounded hover:bg-gray-700 transition-colors',
                          isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'
                        ]"
                        title="编辑"
                      >
                        <PencilIcon class="w-4 h-4" />
                      </button>
                    </template>
                  </div>
                </div>

                <!-- 颜色 -->
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-16 flex-shrink-0 pt-1', isDark ? 'text-gray-300' : 'text-gray-700']">
                    颜色:
                  </span>
                  <div class="flex items-center gap-2">
                    <div class="relative group">
                      <input
                        v-model="localColor"
                        type="color"
                        :class="[
                          'w-7 h-7 rounded-full border-2 cursor-pointer appearance-none',
                          isDark ? 'border-gray-600' : 'border-gray-300'
                        ]"
                        :style="{ backgroundColor: localColor }"
                        @change="updateColor"
                        title="点击选择颜色"
                      />
                    </div>
                    <span :class="['text-sm font-mono', isDark ? 'text-gray-400' : 'text-gray-600']">
                      {{ localColor }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 立绘列表 -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h3 
                  :class="[
                    'text-lg font-semibold',
                    isDark ? 'text-white' : 'text-gray-900'
                  ]"
                >
                  立绘列表 ({{ exampleCount }})
                </h3>
                <button
                  v-if="exampleCount > 0"
                  @click="openGenerateDialog"
                  :class="[
                    'flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg transition-colors',
                    isDark
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-blue-500 hover:bg-blue-600 text-white'
                  ]"
                  title="生成新立绘"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  生成新立绘
                </button>
              </div>
              <div v-if="exampleCount > 0" class="overflow-x-auto">
                <div class="flex gap-4 pb-2">
                  <div
                    v-for="(example, index) in actor.examples"
                    :key="index"
                    :class="[
                      'relative rounded-lg overflow-hidden border cursor-pointer group flex-shrink-0',
                      isDark ? 'border-gray-600' : 'border-gray-200'
                    ]"
                    style="width: 120px; height: 120px;"
                    @click="viewExample(index)"
                    @contextmenu.prevent="showExampleContextMenu($event, example, index)"
                  >
                    <img
                      :src="getExampleImageUrl(example, index)"
                      :alt="example.title || `立绘 ${index + 1}`"
                      class="w-full h-full object-cover"
                      @error="handleImageError"
                    />
                    <div 
                      :class="[
                        'absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center',
                        isDark ? 'text-gray-300' : 'text-white'
                      ]"
                    >
                      <span class="text-xs opacity-0 group-hover:opacity-100 text-center px-1">
                        {{ example.title || `立绘 ${index + 1}` }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div 
                v-else
                @click="openGenerateDialog"
                :class="[
                  'p-8 rounded-lg border flex flex-col items-center justify-center cursor-pointer transition-colors',
                  isDark ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                ]"
              >
                <PhotoIcon class="w-12 h-12 mb-2" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
                <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-500']">
                  暂无立绘
                </p>
                <span :class="['text-xs mt-1', isDark ? 'text-gray-600' : 'text-gray-400']">点击添加</span>
              </div>
            </div>

            <!-- 标签 -->
            <div>
              <h3 
                :class="[
                  'text-lg font-semibold mb-3',
                  isDark ? 'text-white' : 'text-gray-900'
                ]"
              >
                标签
              </h3>
              <div class="flex flex-wrap gap-2">
                <!-- 现有标签 chips -->
                <div
                  v-for="(value, key) in actor.tags"
                  :key="key"
                  :class="[
                    'flex items-center gap-1 px-3 py-1.5 rounded-full text-sm transition-colors',
                    editingTagKey === key
                      ? isDark ? 'bg-blue-900/50 border-2 border-blue-500' : 'bg-blue-50 border-2 border-blue-400'
                      : isDark ? 'bg-gray-700 border border-gray-600 hover:bg-gray-600' : 'bg-gray-100 border border-gray-300 hover:bg-gray-200'
                  ]"
                  @click="startEditTag(key, value)"
                >
                  <template v-if="editingTagKey === key">
                    <input
                      v-model="editingTagValue"
                      type="text"
                      :class="[
                        'w-32 px-1 bg-transparent focus:outline-none',
                        isDark ? 'text-white' : 'text-gray-900'
                      ]"
                      @keydown.enter="saveTag"
                      @keydown.esc="cancelEditTag"
                      @click.stop
                      ref="tagInputRef"
                    />
                    <button
                      @click.stop="saveTag"
                      :class="['hover:text-green-500', isDark ? 'text-gray-300' : 'text-gray-600']"
                      title="保存"
                    >
                      ✓
                    </button>
                  </template>
                  <template v-else>
                    <span :class="[isDark ? 'text-gray-200' : 'text-gray-700']">
                      {{ key }}: {{ value }}
                    </span>
                    <button
                      @click.stop="deleteTag(key)"
                      :class="['hover:text-red-500', isDark ? 'text-gray-400' : 'text-gray-500']"
                      title="删除"
                    >
                      ×
                    </button>
                  </template>
                </div>

                <!-- 添加标签按钮 -->
                <button
                  v-if="!isAddingTag"
                  @click="startAddTag"
                  :class="[
                    'flex items-center gap-1 px-3 py-1.5 rounded-full text-sm border-2 border-dashed transition-colors',
                    isDark
                      ? 'border-gray-600 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                      : 'border-gray-300 text-gray-500 hover:border-gray-400 hover:text-gray-600'
                  ]"
                >
                  + 添加标签
                </button>

                <!-- 添加标签输入 -->
                <div
                  v-else
                  :class="[
                    'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border-2',
                    isDark ? 'bg-blue-900/50 border-blue-500' : 'bg-blue-50 border-blue-400'
                  ]"
                >
                  <input
                    v-model="newTagKey"
                    type="text"
                    placeholder="键"
                    :class="[
                      'w-20 px-1 bg-transparent focus:outline-none',
                      isDark ? 'text-white placeholder-gray-400' : 'text-gray-900 placeholder-gray-500'
                    ]"
                    @keydown.enter="saveNewTag"
                    @keydown.esc="cancelAddTag"
                    ref="newTagKeyInputRef"
                  />
                  <span :class="isDark ? 'text-gray-400' : 'text-gray-600'">:</span>
                  <input
                    v-model="newTagValue"
                    type="text"
                    placeholder="值"
                    :class="[
                      'w-20 px-1 bg-transparent focus:outline-none',
                      isDark ? 'text-white placeholder-gray-400' : 'text-gray-900 placeholder-gray-500'
                    ]"
                    @keydown.enter="saveNewTag"
                    @keydown.esc="cancelAddTag"
                  />
                  <button
                    @click="saveNewTag"
                    :class="['hover:text-green-500', isDark ? 'text-gray-300' : 'text-gray-600']"
                    title="保存"
                  >
                    ✓
                  </button>
                  <button
                    @click="cancelAddTag"
                    :class="['hover:text-red-500', isDark ? 'text-gray-400' : 'text-gray-500']"
                    title="取消"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

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
        @click="deleteExample"
        :class="[
          'w-full px-4 py-2 text-left text-sm hover:bg-red-500 hover:text-white transition-colors',
          isDark ? 'text-gray-300' : 'text-gray-700'
        ]"
      >
        删除立绘
      </button>
    </div>

    <!-- 生成立绘对话框 -->
    <GeneratePortraitDialog
      :show="showGenerateDialog"
      :actor-name="actor?.name || ''"
      :actor-id="actor?.actor_id || ''"
      :project-id="actor?.project_id || ''"
      @close="showGenerateDialog = false"
      @generated="handleGenerated"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { PhotoIcon, PencilIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import api from '../api'
import GeneratePortraitDialog from './GeneratePortraitDialog.vue'

interface Actor {
  actor_id: string
  project_id: string
  name: string
  desc: string
  color: string
  tags: Record<string, string>
  examples: any[]
}

interface Props {
  actor: Actor | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', actor: Actor): void
  (e: 'generate', actor: Actor): void
  (e: 'examples', actor: Actor): void
  (e: 'refresh'): void
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 颜色选择
const localColor = ref('#808080')
watch(() => props.actor?.color, (newColor) => {
  if (newColor) {
    localColor.value = newColor
  }
}, { immediate: true })

// 基本信息编辑状态
const editingField = ref<'name' | 'desc' | null>(null)
const editingName = ref('')
const editingDesc = ref('')
const nameInputRef = ref<HTMLInputElement | null>(null)
const descInputRef = ref<HTMLTextAreaElement | null>(null)

// 标签编辑状态
const editingTagKey = ref<string | null>(null)
const editingTagValue = ref('')
const isAddingTag = ref(false)
const newTagKey = ref('')
const newTagValue = ref('')
const tagInputRef = ref<HTMLInputElement | null>(null)
const newTagKeyInputRef = ref<HTMLInputElement | null>(null)

// 右键菜单状态
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  example: null as any,
  index: -1
})

// 生成立绘对话框状态
const showGenerateDialog = ref(false)

const exampleCount = computed(() => props.actor?.examples?.length || 0)
const firstExample = computed(() => {
  if (!props.actor?.examples || props.actor.examples.length === 0) return null
  return props.actor.examples[0]
})

const getExampleImageUrl = (example: any, index: number) => {
  if (!example?.image_path || !props.actor) return ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:7864'
  // 通过 actor-example 端点获取图片
  return `${baseURL}/file/actor-example?actor_id=${props.actor.actor_id}&example_index=${index}`
}

const handleImageError = () => {
  // 图片加载失败处理
}

// 开始编辑名称
const startEditName = () => {
  if (!props.actor) return
  editingField.value = 'name'
  editingName.value = props.actor.name
  nextTick(() => {
    nameInputRef.value?.focus()
  })
}

// 保存名称
const saveName = async () => {
  if (!props.actor || !editingName.value.trim()) return
  
  try {
    await api.put(`/actor/${props.actor.actor_id}`, {
      name: editingName.value.trim()
    })
    editingField.value = null
    editingName.value = ''
    emit('refresh')
  } catch (error) {
    console.error('保存名称失败:', error)
  }
}

// 开始编辑描述
const startEditDesc = () => {
  if (!props.actor) return
  editingField.value = 'desc'
  editingDesc.value = props.actor.desc || ''
  nextTick(() => {
    descInputRef.value?.focus()
  })
}

// 保存描述
const saveDesc = async () => {
  if (!props.actor) return
  
  try {
    await api.put(`/actor/${props.actor.actor_id}`, {
      desc: editingDesc.value.trim()
    })
    editingField.value = null
    editingDesc.value = ''
    emit('refresh')
  } catch (error) {
    console.error('保存描述失败:', error)
  }
}

// 取消编辑基本信息
const cancelEdit = () => {
  editingField.value = null
  editingName.value = ''
  editingDesc.value = ''
}

// 更新颜色
const updateColor = async () => {
  if (!props.actor) return
  
  try {
    await api.put(`/actor/${props.actor.actor_id}`, {
      color: localColor.value
    })
    emit('refresh')
  } catch (error) {
    console.error('更新颜色失败:', error)
  }
}

// 开始编辑标签
const startEditTag = (key: string, value: string) => {
  editingTagKey.value = key
  editingTagValue.value = value
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

// 保存标签
const saveTag = async () => {
  if (!props.actor || !editingTagKey.value) return
  
  try {
    const newTags = { ...props.actor.tags }
    newTags[editingTagKey.value] = editingTagValue.value
    
    await api.put(`/actor/${props.actor.actor_id}`, {
      tags: newTags
    })
    
    editingTagKey.value = null
    editingTagValue.value = ''
    emit('refresh')
  } catch (error) {
    console.error('保存标签失败:', error)
  }
}

// 取消编辑标签
const cancelEditTag = () => {
  editingTagKey.value = null
  editingTagValue.value = ''
}

// 删除标签
const deleteTag = async (key: string) => {
  if (!props.actor) return
  
  try {
    const newTags = { ...props.actor.tags }
    delete newTags[key]
    
    await api.put(`/actor/${props.actor.actor_id}`, {
      tags: newTags
    })
    
    emit('refresh')
  } catch (error) {
    console.error('删除标签失败:', error)
  }
}

// 开始添加标签
const startAddTag = () => {
  isAddingTag.value = true
  nextTick(() => {
    newTagKeyInputRef.value?.focus()
  })
}

// 保存新标签
const saveNewTag = async () => {
  if (!props.actor || !newTagKey.value.trim() || !newTagValue.value.trim()) return
  
  try {
    const newTags = { ...props.actor.tags }
    newTags[newTagKey.value.trim()] = newTagValue.value.trim()
    
    await api.put(`/actor/${props.actor.actor_id}`, {
      tags: newTags
    })
    
    isAddingTag.value = false
    newTagKey.value = ''
    newTagValue.value = ''
    emit('refresh')
  } catch (error) {
    console.error('添加标签失败:', error)
  }
}

// 取消添加标签
const cancelAddTag = () => {
  isAddingTag.value = false
  newTagKey.value = ''
  newTagValue.value = ''
}

const close = () => {
  emit('close')
}

const openEditDialog = () => {
  if (props.actor) {
    emit('edit', props.actor)
  }
}

const openGenerateDialog = () => {
  showGenerateDialog.value = true
}

const handleGenerated = () => {
  // 生成完成后刷新角色信息
  emit('refresh')
}

const openExamplesDialog = () => {
  if (props.actor) {
    emit('examples', props.actor)
  }
}

// 查看立绘（点击时）
const viewExample = (index: number) => {
  // 可以打开立绘详情或放大查看
  openExamplesDialog()
}

// 显示立绘右键菜单
const showExampleContextMenu = (event: MouseEvent, example: any, index: number) => {
  event.preventDefault()
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    example: example,
    index: index
  }
}

// 删除立绘
const deleteExample = async () => {
  if (!props.actor || contextMenu.value.index === -1) return
  
  try {
    // 调用删除示例图 API（使用索引）
    await api.delete(`/actor/${props.actor.actor_id}/example`, {
      params: {
        example_index: contextMenu.value.index
      }
    })
    
    contextMenu.value.show = false
    emit('refresh')
  } catch (error) {
    console.error('删除立绘失败:', error)
    contextMenu.value.show = false
  }
}

// 点击外部关闭右键菜单
const handleClickOutside = () => {
  if (contextMenu.value.show) {
    contextMenu.value.show = false
  }
}

// 监听点击事件以关闭右键菜单
watch(() => contextMenu.value.show, (show) => {
  if (show) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})
</script>

<style scoped>
/* 自定义圆形颜色选择器样式 */
input[type="color"] {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  border: none;
  cursor: pointer;
}

input[type="color"]::-webkit-color-swatch-wrapper {
  padding: 0;
  border-radius: 50%;
}

input[type="color"]::-webkit-color-swatch {
  border: none;
  border-radius: 50%;
}

input[type="color"]::-moz-color-swatch {
  border: none;
  border-radius: 50%;
}
</style>

