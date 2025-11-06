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
          'mx-4 md:mx-0', // 移动端添加左右边距
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @click.stop
      >
        <!-- 标题栏 -->
        <div 
          :class="[
            'flex items-center justify-between border-b',
            'p-3 md:p-4', // 移动端使用更小的内边距
            isDark ? 'border-gray-700' : 'border-gray-200'
          ]"
        >
          <h2 
            :class="[
              'text-lg md:text-xl font-bold', // 移动端使用更小的字体
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
        <div class="flex-1 overflow-y-auto p-4 md:p-6">
          <div class="space-y-6">
            <!-- 立绘展示区域 -->
            <div class="relative">
              <!-- 左右切换按钮 -->
              <div 
                v-if="exampleCount > 1"
                class="absolute inset-0 flex items-center justify-between pointer-events-none z-10"
              >
                <button
                  @click="prevExample"
                  :disabled="currentExampleIndex === 0"
                  :class="[
                    'pointer-events-auto p-2 rounded-full transition-colors ml-2',
                    currentExampleIndex === 0
                      ? 'bg-gray-900 bg-opacity-30 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                        : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="上一张"
                >
                  <ChevronLeftIcon class="w-6 h-6" />
                </button>
                <button
                  @click="nextExample"
                  :disabled="currentExampleIndex === exampleCount - 1"
                  :class="[
                    'pointer-events-auto p-2 rounded-full transition-colors mr-2',
                    currentExampleIndex === exampleCount - 1
                      ? 'bg-gray-900 bg-opacity-30 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                        : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="下一张"
                >
                  <ChevronRightIcon class="w-6 h-6" />
                </button>
              </div>
              
              <!-- 生成参数按钮组 -->
              <div 
                v-if="currentExample && currentExample.draw_args"
                class="absolute top-2 right-2 z-10 flex gap-2"
              >
                <!-- 复制生成参数按钮 -->
                <button
                  @click.stop="copyParams"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    isDark
                      ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                      : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="复制生成参数"
                >
                  <ClipboardIcon class="w-5 h-5" />
                </button>
                <!-- 查看生成参数按钮 -->
                <button
                  @click.stop="showParamsDialog = true"
                  :class="[
                    'p-2 rounded-lg transition-colors',
                    isDark
                      ? 'bg-gray-800 bg-opacity-80 text-white hover:bg-opacity-100'
                      : 'bg-white bg-opacity-80 text-gray-900 hover:bg-opacity-100'
                  ]"
                  title="查看生成参数"
                >
                  <InformationCircleIcon class="w-5 h-5" />
                </button>
              </div>
              
              <div 
                v-if="currentExample && currentExample.image_path"
                :class="[
                  'w-full h-96 rounded-lg overflow-hidden border flex items-center justify-center cursor-pointer',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
                @click="openImageGallery"
              >
                <img
                  :src="getExampleImageUrl(currentExample, currentExampleIndex)"
                  :alt="currentExample.title || actor.name"
                  class="w-full h-full object-contain"
                  @error="handleImageError"
                />
              </div>
              <div 
                v-else-if="currentExample && !currentExample.image_path"
                :class="[
                  'w-full h-96 rounded-lg border flex flex-col items-center justify-center',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
              >
                <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
                     :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
                <span :class="['text-sm mt-4', isDark ? 'text-gray-500' : 'text-gray-500']">生成中...</span>
              </div>
              <div 
                v-else
                @click="openGenerateDialog"
                :class="[
                  'w-full h-96 rounded-lg border flex flex-col items-center justify-center cursor-pointer transition-colors',
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
                    <!-- 有图片路径时显示图片 -->
                    <template v-if="example.image_path">
                      <img
                        :src="getExampleImageUrl(example, index)"
                        :alt="example.title || `立绘 ${index + 1}`"
                        class="w-full h-full object-cover"
                        @error="handleImageError"
                      />
                    </template>
                    <!-- 没有图片路径时显示生成中 -->
                    <template v-else>
                      <div 
                        :class="[
                          'w-full h-full flex flex-col items-center justify-center',
                          isDark ? 'bg-gray-800' : 'bg-gray-100'
                        ]"
                      >
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2" 
                             :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
                        <span :class="['text-xs mt-2', isDark ? 'text-gray-400' : 'text-gray-500']">生成中...</span>
                      </div>
                    </template>
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
      data-context-menu
      @click.stop
      @contextmenu.stop.prevent
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
        v-if="contextMenu.index !== 0"
        @click="setAsDefaultExample"
        :class="[
          'w-full px-4 py-2 text-left text-sm transition-colors',
          isDark 
            ? 'text-gray-300 hover:bg-blue-600 hover:text-white' 
            : 'text-gray-700 hover:bg-blue-500 hover:text-white'
        ]"
      >
        设置为默认图像
      </button>
      <button
        @click="deleteExample"
        :class="[
          'w-full px-4 py-2 text-left text-sm transition-colors',
          isDark ? 'text-gray-300 hover:bg-red-500 hover:text-white' : 'text-gray-700 hover:bg-red-500 hover:text-white'
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
      :actor-desc="actor?.desc"
      :actor-tags="actor?.tags"
      @close="showGenerateDialog = false"
      @generated="handleGenerated"
    />
    
    <!-- 生成参数对话框 -->
    <ModelParamsDialog
      v-if="showParamsDialog"
      :params="currentExample?.draw_args || null"
      @close="showParamsDialog = false"
    />
    
    <!-- 大图显示对话框 -->
    <ImageGalleryDialog
      :images="allExampleUrls"
      :initial-index="currentExampleIndex"
      :visible="showImageGallery"
      @close="showImageGallery = false"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch, onUnmounted, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { 
  PhotoIcon, 
  PencilIcon, 
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  ClipboardIcon
} from '@heroicons/vue/24/outline'
import api from '../api'
import { getApiBaseURL } from '../utils/apiConfig'
import GeneratePortraitDialog from './GeneratePortraitDialog.vue'
import ModelParamsDialog from './ModelParamsDialog.vue'
import ImageGalleryDialog from './ImageGalleryDialog.vue'
import { showToast } from '../utils/toast'

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

// 当前example索引
const currentExampleIndex = ref(0)
const showParamsDialog = ref(false)
const showImageGallery = ref(false)

// 当前example
const currentExample = computed(() => {
  if (!props.actor?.examples || currentExampleIndex.value >= props.actor.examples.length) {
    return null
  }
  return props.actor.examples[currentExampleIndex.value]
})

// 所有example的URL数组（用于大图显示）
const allExampleUrls = computed(() => {
  if (!props.actor?.examples) return []
  return props.actor.examples
    .map((ex: any, index: number) => {
      if (!ex?.image_path) return null
      return getExampleImageUrl(ex, index)
    })
    .filter((url): url is string => url !== null && url !== '')
})

const firstExample = computed(() => {
  if (!props.actor?.examples || props.actor.examples.length === 0) return null
  return props.actor.examples[0]
})

const getExampleImageUrl = (example: any, index: number) => {
  if (!example?.image_path || !props.actor) return ''
  const baseURL = getApiBaseURL()
  // 通过 actor-example 端点获取图片
  return `${baseURL}/file/actor-example?actor_id=${props.actor.actor_id}&example_index=${index}`
}

// 检查是否有正在生成的立绘（image_path 为 None）
const hasGeneratingPortrait = computed(() => {
  if (!props.actor?.examples) return false
  return props.actor.examples.some((ex: any) => !ex.image_path)
})

// 每5秒刷新一次（如果有正在生成的立绘）
let refreshTimer: ReturnType<typeof setInterval> | null = null

watch(() => props.actor, (newActor) => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  
  // 如果有正在生成的立绘，启动定时刷新
  if (newActor && hasGeneratingPortrait.value) {
    refreshTimer = setInterval(async () => {
      try {
        // 重新加载 actor 数据
        const response = await api.get(`/actor/${newActor.actor_id}`)
        if (response) {
          emit('refresh')
        }
      } catch (error) {
        console.error('刷新立绘状态失败:', error)
      }
    }, 5000) // 每5秒刷新一次
  }
}, { immediate: true })


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

// 切换到上一张example
const prevExample = () => {
  if (currentExampleIndex.value > 0) {
    currentExampleIndex.value--
  }
}

// 切换到下一张example
const nextExample = () => {
  if (currentExampleIndex.value < exampleCount.value - 1) {
    currentExampleIndex.value++
  }
}

// 监听角色变化，重置索引
watch(() => props.actor, () => {
  if (props.actor) {
    currentExampleIndex.value = 0
    showParamsDialog.value = false
    showImageGallery.value = false
  }
}, { immediate: true })

// 查看立绘（点击时）
const viewExample = (index: number) => {
  // 设置当前索引并打开大图
  currentExampleIndex.value = index
  if (props.actor?.examples[index]?.image_path) {
    openImageGallery()
  }
}

// 打开大图显示
const openImageGallery = () => {
  if (allExampleUrls.value.length > 0) {
    showImageGallery.value = true
  }
}

// 复制生成参数到剪贴板
const copyParams = async () => {
  if (!currentExample.value?.draw_args) return
  
  try {
    const params = currentExample.value.draw_args
    
    // 构建符合 API 端点格式的参数对象
    const apiParams: Record<string, any> = {}
    
    // 必填字段
    if (params.model) apiParams.model = params.model
    if (params.prompt) apiParams.prompt = params.prompt
    
    // 可选字段（只包含有值的）
    if (params.negative_prompt) apiParams.negative_prompt = params.negative_prompt
    else apiParams.negative_prompt = ""
    
    // 统一采样器字段名（API 使用 sampler_name）
    if (params.sampler) apiParams.sampler_name = params.sampler
    else if (params.sampler_name) apiParams.sampler_name = params.sampler_name
    else apiParams.sampler_name = "DPM++ 2M Karras"
    
    if (params.steps !== undefined) apiParams.steps = params.steps
    else apiParams.steps = 30
    
    if (params.cfg_scale !== undefined) apiParams.cfg_scale = params.cfg_scale
    else apiParams.cfg_scale = 7.0
    
    if (params.seed !== undefined) apiParams.seed = params.seed
    else apiParams.seed = -1
    
    if (params.width !== undefined) apiParams.width = params.width
    else apiParams.width = 1024
    
    if (params.height !== undefined) apiParams.height = params.height
    else apiParams.height = 1024
    
    if (params.clip_skip !== undefined) apiParams.clip_skip = params.clip_skip
    if (params.vae) apiParams.vae = params.vae
    if (params.loras && Object.keys(params.loras).length > 0) {
      apiParams.loras = params.loras
    }
    
    const jsonString = JSON.stringify(apiParams, null, 2)
    await navigator.clipboard.writeText(jsonString)
    
    showToast('参数已复制到剪贴板', 'success')
  } catch (error) {
    console.error('复制失败:', error)
    showToast('复制失败，请重试', 'error')
  }
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

// 设置为默认图像（交换到首位）
const setAsDefaultExample = async () => {
  if (!props.actor || contextMenu.value.index === -1) return
  
  // 如果已经是首位，不需要操作
  if (contextMenu.value.index === 0) {
    contextMenu.value.show = false
    return
  }
  
  try {
    // 调用交换API，将选中的立绘与index=0的立绘交换
    await api.post(`/actor/${props.actor.actor_id}/example/swap`, null, {
      params: {
        index1: contextMenu.value.index,
        index2: 0
      }
    })
    
    contextMenu.value.show = false
    // 如果当前查看的是被交换的立绘，更新索引
    if (currentExampleIndex.value === contextMenu.value.index) {
      currentExampleIndex.value = 0
    } else if (currentExampleIndex.value === 0) {
      currentExampleIndex.value = contextMenu.value.index
    }
    emit('refresh')
    showToast('已设置为默认图像', 'success')
  } catch (error: any) {
    console.error('设置为默认图像失败:', error)
    showToast('设置为默认图像失败: ' + (error.response?.data?.detail || error.message), 'error')
    contextMenu.value.show = false
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
const handleClickOutside = (event: MouseEvent) => {
  if (!contextMenu.value.show) return
  
  // 检查点击目标是否在右键菜单内
  const target = event.target as HTMLElement
  const menuElement = document.querySelector('[data-context-menu]') as HTMLElement
  
  if (menuElement && !menuElement.contains(target)) {
    contextMenu.value.show = false
  }
}

// 右键点击外部关闭右键菜单
const handleContextMenuOutside = (event: MouseEvent) => {
  if (!contextMenu.value.show) return
  
  // 检查右键目标是否在右键菜单内
  const target = event.target as HTMLElement
  const menuElement = document.querySelector('[data-context-menu]') as HTMLElement
  
  if (menuElement && !menuElement.contains(target)) {
    contextMenu.value.show = false
  }
}

// 监听点击事件以关闭右键菜单
watch(() => contextMenu.value.show, (show) => {
  if (show) {
    // 使用 setTimeout 确保事件监听器在下一个事件循环中添加
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside, true)
      document.addEventListener('contextmenu', handleContextMenuOutside, true)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside, true)
    document.removeEventListener('contextmenu', handleContextMenuOutside, true)
  }
})

// ESC 键关闭对话框
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    // 如果生成立绘对话框打开，先关闭它（由子组件处理）
    if (showGenerateDialog.value) {
      return // ESC 会由子组件处理
    }
    
    // 如果右键菜单打开，关闭它
    if (contextMenu.value.show) {
      contextMenu.value.show = false
      return
    }
    
    // 如果正在添加标签，取消添加
    if (isAddingTag.value) {
      cancelAddTag()
      return
    }
    
    // 如果正在编辑标签，取消编辑
    if (editingTagKey.value !== null) {
      cancelEditTag()
      return
    }
    
    // 如果正在编辑基本信息，取消编辑
    if (editingField.value !== null) {
      cancelEdit()
      return
    }
    
    // 否则关闭对话框
    close()
  }
}

// 组件挂载时添加键盘事件监听
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

// 组件卸载时移除键盘事件监听
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  // 确保清理右键菜单的事件监听器
  document.removeEventListener('click', handleClickOutside, true)
  document.removeEventListener('contextmenu', handleContextMenuOutside, true)
  // 确保清理定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
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

