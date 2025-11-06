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
        <DocumentTextIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h1 
          :class="[
            'text-3xl font-bold',
            isDark ? 'text-white' : 'text-gray-900'
          ]"
        >
          内容管理
        </h1>
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
            在主页创建项目后，才能管理内容
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

      <!-- 内容列表 -->
      <div 
        v-else-if="contents.length > 0 || insertingIndex !== null"
        class="space-y-4"
      >
        <!-- 第一个插入编辑框（在所有段落之前） -->
        <div
          v-if="insertingIndex === 0"
          class="mb-4"
        >
          <textarea
            :ref="(el) => { if (el) insertingTextareaRef = el as HTMLTextAreaElement }"
            v-model="insertText"
            @keydown="handleInsertKeydown"
            @keydown.esc.prevent="handleInsertCancel"
            @blur="handleInsertBlur"
            rows="4"
            placeholder="输入新段落内容..."
            :class="[
              'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            ]"
          ></textarea>
        </div>
        
        <div
          v-for="(content, index) in contents"
          :key="`${content.chapter}-${content.line}`"
          @contextmenu.prevent="showContextMenu($event, content, index)"
          data-content-item
        >
          <!-- 段落 -->
          <div class="flex items-start gap-4">
            <!-- 左侧：内容文本 -->
            <div class="flex-1 min-w-0">
              <!-- 编辑模式 -->
              <div v-if="editingId === `${content.chapter}-${content.line}`" class="space-y-2">
                <textarea
                  :ref="(el) => { if (el) editingTextareaRef = el as HTMLTextAreaElement }"
                  v-model="editingText"
                  @keydown="handleEditKeydown"
                  @keydown.esc.prevent="handleEditCancel"
                  @blur="handleTextareaBlur"
                  rows="4"
                  :class="[
                    'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
                    isDark
                      ? 'bg-gray-700 border-gray-600 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  ]"
                  placeholder="输入内容..."
                ></textarea>
              </div>
              
              <!-- 显示模式 -->
              <div 
                v-else
                @click.stop="startEdit(content)"
                :class="[
                  'cursor-pointer rounded hover:bg-opacity-50 transition-colors',
                  isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                ]"
              >
                <p class="whitespace-pre-wrap text-sm leading-relaxed" 
                   :class="isDark ? 'text-gray-200' : 'text-gray-900'">
                  {{ content.content }}
                </p>
              </div>
            </div>
            
            <!-- 右侧：功能区（只显示章节-段落标识） -->
            <div class="flex items-center flex-shrink-0">
              <div 
                :class="[
                  'text-xs font-medium px-2 py-1 rounded',
                  isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ content.chapter }}-{{ content.line }}
              </div>
            </div>
          </div>
          
          <!-- 插入编辑框（出现在段落下方） -->
          <div
            v-if="insertingIndex === index + 1"
            class="mt-4"
          >
            <textarea
              :ref="(el) => { if (el) insertingTextareaRef = el as HTMLTextAreaElement }"
              v-model="insertText"
              @keydown="handleInsertKeydown"
              @keydown.esc.prevent="handleInsertCancel"
              @blur="handleInsertBlur"
              rows="4"
              placeholder="输入新段落内容..."
              :class="[
                'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
                isDark
                  ? 'bg-gray-700 border-gray-600 text-white'
                  : 'bg-white border-gray-300 text-gray-900'
              ]"
            ></textarea>
          </div>
        </div>
        
        <!-- 最后一个插入编辑框（在列表末尾） -->
        <div
          v-if="insertingIndex === contents.length"
          class="mt-4"
        >
          <textarea
            :ref="(el) => { if (el) insertingTextareaRef = el as HTMLTextAreaElement }"
            v-model="insertText"
            @keydown="handleInsertKeydown"
            @keydown.esc.prevent="handleInsertCancel"
            @blur="handleInsertBlur"
            rows="4"
            placeholder="输入新段落内容..."
            :class="[
              'w-full px-3 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm',
              isDark
                ? 'bg-gray-700 border-gray-600 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            ]"
          ></textarea>
        </div>
      </div>

      <!-- 空状态 -->
      <div 
        v-else
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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 
            :class="[
              'text-lg font-semibold mb-2',
              isDark ? 'text-gray-300' : 'text-gray-700'
            ]"
          >
            暂无内容
          </h3>
          <p 
            :class="[
              'text-sm',
              isDark ? 'text-gray-500' : 'text-gray-500'
            ]"
          >
            右键段落卡片可添加新段落
          </p>
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
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
          'min-w-[160px] rounded-lg shadow-lg border overflow-hidden',
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        ]"
      >
        <button
          @click="handleInsertAbove"
          :class="[
            'w-full px-4 py-2 text-left text-sm transition-colors',
            isDark
              ? 'hover:bg-gray-700 text-gray-300'
              : 'hover:bg-gray-100 text-gray-700'
          ]"
        >
          在上方插入段落
        </button>
        <button
          @click="handleInsertBelow"
          :class="[
            'w-full px-4 py-2 text-left text-sm transition-colors',
            isDark
              ? 'hover:bg-gray-700 text-gray-300'
              : 'hover:bg-gray-100 text-gray-700'
          ]"
        >
          在下方插入段落
        </button>
        <div :class="['border-t', isDark ? 'border-gray-700' : 'border-gray-200']"></div>
        <button
          @click="handleDeleteFromMenu"
          :class="[
            'w-full px-4 py-2 text-left text-sm transition-colors',
            isDark
              ? 'hover:bg-red-900 text-red-400'
              : 'hover:bg-red-50 text-red-600'
          ]"
        >
          删除段落
        </button>
      </div>
    </Teleport>

    <!-- 删除确认对话框 -->
    <Teleport to="body">
      <div
        v-if="showDeleteDialog"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showDeleteDialog = false"
      >
        <div
          :class="[
            'w-full max-w-md rounded-lg shadow-xl',
            isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border-gray-200'
          ]"
          @click.stop
        >
          <div class="p-6">
            <h2 class="text-xl font-bold mb-4 text-red-600">确认删除</h2>
            <p :class="['mb-4', isDark ? 'text-gray-300' : 'text-gray-700']">
              确定要删除这条内容吗？此操作不可恢复。
            </p>
            <div 
              v-if="deletingContent"
              :class="[
                'p-3 rounded border mb-4 text-sm',
                isDark ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-700'
              ]"
            >
              {{ deletingContent.content }}
            </div>
            <div class="flex justify-end gap-3">
              <button
                @click="showDeleteDialog = false; deletingContent = null"
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
                @click="handleDelete"
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'
import api from '../api'

interface NovelContent {
  id?: number
  project_id: string
  chapter: number
  line: number
  content: string
}

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { selectedProjectId } = storeToRefs(projectStore)

// 状态
const loading = ref(false)
const contents = ref<NovelContent[]>([])

// 编辑状态
const editingId = ref<string | null>(null)
const editingText = ref('')
const editingContent = ref<NovelContent | null>(null)
const editingTextareaRef = ref<HTMLTextAreaElement | null>(null)
const originalText = ref('') // 保存原始文本，用于判断是否有修改
const isBlurHandling = ref(false) // 防止重复处理 blur
const isSwitchingEdit = ref(false) // 正在切换编辑状态

// 插入状态
const insertingIndex = ref<number | null>(null)
const insertText = ref('')
const inserting = ref(false)
const insertingTextareaRef = ref<HTMLTextAreaElement | null>(null)
const originalInsertText = ref('') // 保存原始插入文本，用于判断是否有输入
const isInsertBlurHandling = ref(false) // 防止重复处理 blur

// 右键菜单状态
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  content: null as NovelContent | null,
  index: -1
})

// 删除状态
const showDeleteDialog = ref(false)
const deletingContent = ref<NovelContent | null>(null)
const deleting = ref(false)

// 加载内容列表
const loadContents = async () => {
  if (!selectedProjectId.value) return
  
  loading.value = true
  try {
    // 加载所有内容（不限制数量）
    const data = await api.get('/novel/content/project', {
      params: {
        project_id: selectedProjectId.value
      }
    })
    contents.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载内容失败:', error)
    contents.value = []
  } finally {
    loading.value = false
  }
}

// 开始编辑
const startEdit = async (content: NovelContent) => {
  const newEditingId = `${content.chapter}-${content.line}`
  
  // 如果点击的是正在编辑的同一个段落，不处理
  if (editingId.value === newEditingId) {
    return
  }
  
  // 如果正在编辑其他内容，先退出编辑状态
  if (editingId.value && editingContent.value) {
    isSwitchingEdit.value = true
    const hasChanged = editingText.value.trim() !== originalText.value.trim()
    
    if (hasChanged) {
      // 有修改，先保存
      try {
        await api.put('/novel/content', {
          content: editingText.value.trim()
        }, {
          params: {
            project_id: editingContent.value.project_id,
            chapter: editingContent.value.chapter,
            line: editingContent.value.line
          }
        })
        await loadContents()
      } catch (error) {
        console.error('保存失败:', error)
        alert('保存失败，请重试')
      }
    }
    
    // 清除编辑状态，退出编辑
    cancelEdit()
    isSwitchingEdit.value = false
    return
  }
  
  // 开始新的编辑
  editingId.value = newEditingId
  editingText.value = content.content
  originalText.value = content.content
  editingContent.value = content
  isBlurHandling.value = false
  isSwitchingEdit.value = false
  // 取消插入状态和右键菜单
  cancelInsert()
  hideContextMenu()
  
  // 等待DOM更新后focus文本框
  await nextTick()
  if (editingTextareaRef.value) {
    editingTextareaRef.value.focus()
    // 将光标移动到第0个字符位置
    editingTextareaRef.value.setSelectionRange(0, 0)
  }
}

// 取消编辑
const cancelEdit = () => {
  editingId.value = null
  editingText.value = ''
  originalText.value = ''
  editingContent.value = null
}

// 保存编辑
const saveEdit = async () => {
  if (!editingContent.value || !selectedProjectId.value) return
  
  try {
    const text = editingText.value.trim()
    
    // 如果内容是多行，需要切分成多个段落
    const lines = text.split('\n').map(l => l.trim()).filter(l => l)
    
    if (lines.length === 0) {
      // 如果删除所有内容，删除这个段落
      await api.delete('/novel/content', {
        params: {
          project_id: editingContent.value.project_id,
          chapter: editingContent.value.chapter,
          line: editingContent.value.line
        }
      })
    } else if (lines.length === 1) {
      // 单行，直接更新
      await api.put('/novel/content', {
        content: lines[0]
      }, {
        params: {
          project_id: editingContent.value.project_id,
          chapter: editingContent.value.chapter,
          line: editingContent.value.line
        }
      })
    } else {
      // 多行，需要切分成多个段落
      // 先更新第一个段落
      await api.put('/novel/content', {
        content: lines[0]
      }, {
        params: {
          project_id: editingContent.value.project_id,
          chapter: editingContent.value.chapter,
          line: editingContent.value.line
        }
      })
      
      // 批量插入后续段落
      if (lines.length > 1) {
        await api.post('/novel/content/insert/batch', lines.slice(1), {
          params: {
            project_id: editingContent.value.project_id,
            chapter: editingContent.value.chapter,
            line: editingContent.value.line + 1
          }
        })
      }
    }
    
    // 重新加载内容
    await loadContents()
    cancelEdit()
  } catch (error) {
    console.error('保存失败:', error)
    alert('保存失败，请重试')
  }
}

// 处理编辑键盘事件（Enter提交，Shift+Enter换行）
const handleEditKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    // Enter（非Shift）：提交
    event.preventDefault()
    saveEdit()
  }
  // Shift+Enter：允许默认行为（换行）
}

// 处理编辑Enter键（Enter提交，Shift+Enter换行）
const handleEditEnter = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift+Enter：换行
    return
  } else {
    // Enter：提交
    event.preventDefault()
    saveEdit()
  }
}

// 处理编辑取消（ESC或点击外部）
const handleEditCancel = () => {
  if (!editingContent.value || isBlurHandling.value) return
  
  isBlurHandling.value = true
  
  // ESC和点击其他地方，直接取消，不做任何操作
  cancelEdit()
  isBlurHandling.value = false
}

// 处理文本框失去焦点
const handleTextareaBlur = (event: FocusEvent) => {
  // 如果正在切换编辑，不处理 blur
  if (isSwitchingEdit.value) {
    return
  }
  
  // 延迟处理，避免点击其他元素时立即触发
  setTimeout(() => {
    // 如果已经在处理，直接返回
    if (isBlurHandling.value || isSwitchingEdit.value) return
    
    // 检查是否点击到了其他段落（开始编辑另一个）
    const target = event.relatedTarget as HTMLElement | null
    if (target) {
      const clickedContentItem = target.closest('[data-content-item]')
      if (clickedContentItem) {
        // 如果点击的是另一个段落，不处理 blur，让 startEdit 处理
        return
      }
    }
    
    // 检查是否点击了其他可交互元素（如按钮）
    if (target && (target.tagName === 'BUTTON' || target.closest('button'))) {
      return
    }
    
    if (editingId.value) {
      // 点击其他地方，直接取消，不做任何操作
      handleEditCancel()
    }
  }, 150)
}

// 显示右键菜单
const showContextMenu = async (event: MouseEvent, content: NovelContent, index: number) => {
  // 如果正在编辑，先退出编辑，但不显示右键菜单
  if (editingId.value && editingContent.value) {
    isSwitchingEdit.value = true
    const hasChanged = editingText.value.trim() !== originalText.value.trim()
    
    if (hasChanged) {
      // 有修改，先保存
      try {
        await api.put('/novel/content', {
          content: editingText.value.trim()
        }, {
          params: {
            project_id: editingContent.value.project_id,
            chapter: editingContent.value.chapter,
            line: editingContent.value.line
          }
        })
        await loadContents()
      } catch (error) {
        console.error('保存失败:', error)
        alert('保存失败，请重试')
      }
    }
    
    // 清除编辑状态，退出编辑，不显示右键菜单
    cancelEdit()
    isSwitchingEdit.value = false
    return
  }
  
  // 显示右键菜单
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    content: content,
    index: index
  }
}

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenu.value.show = false
}

// 在上方插入
const handleInsertAbove = async () => {
  if (!contextMenu.value.content) return
  
  // 插入到当前位置之前
  insertingIndex.value = contextMenu.value.index
  insertText.value = ''
  originalInsertText.value = ''
  isInsertBlurHandling.value = false
  hideContextMenu()
  
  // 等待DOM更新后focus文本框
  await nextTick()
  if (insertingTextareaRef.value) {
    insertingTextareaRef.value.focus()
    insertingTextareaRef.value.setSelectionRange(0, 0)
  }
}

// 在下方插入
const handleInsertBelow = async () => {
  if (!contextMenu.value.content) return
  
  // 插入到当前位置之后
  insertingIndex.value = contextMenu.value.index + 1
  insertText.value = ''
  originalInsertText.value = ''
  isInsertBlurHandling.value = false
  hideContextMenu()
  
  // 等待DOM更新后focus文本框
  await nextTick()
  if (insertingTextareaRef.value) {
    insertingTextareaRef.value.focus()
    insertingTextareaRef.value.setSelectionRange(0, 0)
  }
}

// 从菜单删除
const handleDeleteFromMenu = () => {
  if (!contextMenu.value.content) return
  
  deletingContent.value = contextMenu.value.content
  showDeleteDialog.value = true
  hideContextMenu()
}

// 取消插入
const cancelInsert = () => {
  insertingIndex.value = null
  insertText.value = ''
  originalInsertText.value = ''
  isInsertBlurHandling.value = false
}

// 处理插入键盘事件（Enter提交，Shift+Enter换行）
const handleInsertKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    // Enter（非Shift）：提交
    event.preventDefault()
    const hasContent = insertText.value.trim().length > 0
    if (hasContent) {
      saveInsert()
    } else {
      cancelInsert()
    }
  }
  // Shift+Enter：允许默认行为（换行）
}

// 处理插入Enter键（Enter提交，Shift+Enter换行）
const handleInsertEnter = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift+Enter：换行
    return
  } else {
    // Enter：提交
    event.preventDefault()
    const hasContent = insertText.value.trim().length > 0
    if (hasContent) {
      saveInsert()
    } else {
      cancelInsert()
    }
  }
}

// 处理插入取消（ESC或点击外部）
const handleInsertCancel = () => {
  if (isInsertBlurHandling.value) return
  
  // ESC和点击其他地方，直接取消，不做任何操作
  cancelInsert()
}

// 处理插入文本框失去焦点
const handleInsertBlur = (event: FocusEvent) => {
  // 延迟处理，避免点击其他元素时立即触发
  setTimeout(() => {
    if (isInsertBlurHandling.value) return
    
    // 检查是否点击了其他可交互元素（如按钮）
    const target = event.relatedTarget as HTMLElement | null
    if (target && (target.tagName === 'BUTTON' || target.closest('button'))) {
      return
    }
    
    if (insertingIndex.value !== null) {
      // 点击其他地方，直接取消，不做任何操作
      handleInsertCancel()
    }
  }, 150)
}

// 保存插入
const saveInsert = async () => {
  if (!selectedProjectId.value || !insertText.value.trim() || inserting.value || isInsertBlurHandling.value) return
  
  isInsertBlurHandling.value = true
  inserting.value = true
  
  try {
    // 确定插入位置
    const insertPos = insertingIndex.value ?? 0
    
    // 确定章节和行号
    let chapter = 0
    let line = 0
    
    if (contents.value.length === 0) {
      // 空列表，从第0章第0行开始
      chapter = 0
      line = 0
    } else if (insertPos === 0) {
      // 插入到最前面：使用第一个内容的章节，行号为第一个内容的行号（插入到第一个内容之前）
      const firstContent = contents.value[0]
      if (firstContent) {
        chapter = firstContent.chapter
        line = firstContent.line  // 插入到这个位置，后端会将>=line的所有行+1
      }
    } else if (insertPos >= contents.value.length) {
      // 插入到最后
      const lastContent = contents.value[contents.value.length - 1]
      if (lastContent) {
        chapter = lastContent.chapter
        line = lastContent.line + 1
      }
    } else {
      // 插入到中间：插入到insertPos位置之前
      // 也就是说，新内容会插入到contents[insertPos-1]之后
      const prevContent = contents.value[insertPos - 1]
      if (prevContent) {
        chapter = prevContent.chapter
        line = prevContent.line + 1
      }
    }
    
    // 如果是多行内容，需要切分成多个段落
    const lines = insertText.value.split('\n').map(l => l.trim()).filter(l => l)
    
    if (lines.length === 0) {
      // 不应该到这里，因为前面已经检查了trim()
      return
    } else if (lines.length === 1) {
      // 单行，使用单条插入API
      await api.post('/novel/content/insert', null, {
        params: {
          project_id: selectedProjectId.value,
          chapter: chapter,
          line: line,
          content: lines[0]
        }
      })
    } else {
      // 多行，使用批量插入API
      await api.post('/novel/content/insert/batch', lines, {
        params: {
          project_id: selectedProjectId.value,
          chapter: chapter,
          line: line
        }
      })
    }
    
    // 重新加载内容
    await loadContents()
    cancelInsert()
  } catch (error) {
    console.error('插入失败:', error)
    alert('插入失败，请重试')
  } finally {
    inserting.value = false
    isInsertBlurHandling.value = false
  }
}

// 处理删除
const handleDelete = async () => {
  if (!deletingContent.value) return
  
  deleting.value = true
  try {
    await api.delete('/novel/content', {
      params: {
        project_id: deletingContent.value.project_id,
        chapter: deletingContent.value.chapter,
        line: deletingContent.value.line
      }
    })
    
    // 重新加载内容
    await loadContents()
    showDeleteDialog.value = false
    deletingContent.value = null
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  } finally {
    deleting.value = false
  }
}

// 点击外部关闭右键菜单
const handleClickOutside = () => {
  if (contextMenu.value.show) {
    hideContextMenu()
  }
}

// 监听右键菜单显示状态
watch(() => contextMenu.value.show, (show) => {
  if (show) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

// 监听项目变化
watch(selectedProjectId, async (newProjectId) => {
  if (newProjectId) {
    await loadContents()
  } else {
    contents.value = []
    cancelEdit()
    cancelInsert()
    hideContextMenu()
  }
})

onMounted(async () => {
  projectStore.init()
  
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
  
  if (selectedProjectId.value) {
    await loadContents()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
