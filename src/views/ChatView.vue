<template>
  <div class="flex flex-col fixed inset-0 overflow-hidden" :style="{ top: '0', left: `${navigationWidth}px`, right: '0', bottom: '0' }">
    <!-- 顶部：项目标题和清空按钮 -->
    <div 
      :class="[
        'flex items-center justify-between gap-4 p-4 border-b flex-shrink-0',
        isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
      ]"
    >
      <!-- 左侧：项目标题 -->
      <div class="flex items-center gap-3 min-w-0">
        <h1 
          :class="[
            'text-lg font-semibold truncate',
            isDark ? 'text-gray-100' : 'text-gray-900'
          ]"
          :title="selectedProject?.title || '默认工作空间'"
        >
          {{ selectedProject?.title || '默认工作空间' }}
        </h1>
        <span 
          v-if="selectedProject"
          :class="[
            'text-xs px-2 py-1 rounded-full hidden md:inline-block',
            isDark ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-100 text-blue-700'
          ]"
        >
          {{ messages.length }} 条消息
        </span>
      </div>

      <!-- 右侧：清空按钮 -->
      <button
        @click="showClearHistoryDialog = true"
        :disabled="loadingHistory"
        :class="[
          'px-4 py-2 rounded-lg transition-colors text-sm flex-shrink-0',
          !loadingHistory
            ? isDark
              ? 'bg-gray-700 hover:bg-gray-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            : isDark
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        ]"
        title="清空历史"
      >
        清空历史
      </button>
    </div>

    <!-- 消息列表容器：可滚动区域 -->
    <div 
      ref="messagesContainerRef"
      class="flex-1 overflow-y-auto p-4 space-y-4"
      :class="isDark ? 'bg-gray-900' : 'bg-gray-50'"
    >
      <!-- 加载历史记录 -->
      <div v-if="loadingHistory" class="flex justify-center py-4">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2" 
             :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
      </div>

      <!-- 消息列表 -->
      <div 
        v-for="message in messages" 
        :key="message._internalKey || message.message_id" 
        class="message-item"
      >
        <!-- 用户消息 -->
        <div v-if="message.role === 'user'" 
             class="flex items-start gap-3 mb-4 justify-end">
          <!-- 消息内容 - 卡片样式或编辑模式 -->
          <div 
            v-if="editingMessageId !== message.message_id"
            @click.stop="startEditMessage(message.message_id, message.context)"
            :class="[
              'w-full max-w-[90%] rounded-lg px-4 py-3 shadow-sm cursor-pointer hover:opacity-90 transition-opacity',
              isDark ? 'bg-gray-800 border border-gray-700 text-gray-100' : 'bg-white border border-gray-200 text-gray-900 shadow'
            ]"
          >
            <p class="whitespace-pre-wrap text-sm leading-relaxed">{{ message.context }}</p>
          </div>
          
          <!-- 编辑模式 -->
          <div 
            v-else
            @click.stop
            class="editing-message-container"
            :class="[
              'w-full max-w-[90%] rounded-lg px-4 py-3 shadow-sm border-2',
              isDark ? 'bg-gray-800 border-blue-500 text-gray-100' : 'bg-white border-blue-500 text-gray-900 shadow'
            ]"
          >
            <div class="flex items-start gap-2">
              <textarea
                v-model="editingText"
                @keydown.esc="cancelEdit"
                @keydown.ctrl.enter="confirmRestart"
                @keydown.meta.enter="confirmRestart"
                :class="[
                  'flex-1 text-sm leading-relaxed resize-none focus:outline-none bg-transparent',
                  isDark ? 'text-gray-100' : 'text-gray-900'
                ]"
                rows="3"
                style="min-height: 60px;"
                :ref="setEditingTextareaRef"
              ></textarea>
              <button
                @click="confirmRestart"
                :class="[
                  'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors',
                  isDark 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-green-500 hover:bg-green-600 text-white'
                ]"
                title="从此处重新开始（Ctrl+Enter）"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </div>
          
          <!-- 头像 -->
          <div class="flex-shrink-0">
            <div 
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
                isDark ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
              ]"
            >
              用
            </div>
          </div>
        </div>

        <!-- 助手消息 -->
        <div v-else-if="message.role === 'assistant'"
             class="flex items-start gap-3 mb-4">
          <!-- 头像 -->
          <div class="flex-shrink-0">
            <div 
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
                isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-200 text-gray-700'
              ]"
            >
              AI
            </div>
          </div>
          
          <!-- 消息内容 - 无卡片样式 -->
          <div class="w-full max-w-[90%] flex-1">
            <!-- AI 思考中提示 -->
            <div 
              v-if="message.status === 'thinking' && !message.context && (!message.tools || message.tools.length === 0)"
              class="flex items-center gap-2 mb-2"
            >
              <div class="flex items-center gap-1.5">
                <div 
                  class="w-2 h-2 rounded-full animate-bounce"
                  :class="isDark ? 'bg-blue-400' : 'bg-blue-500'"
                  style="animation-delay: 0ms;"
                ></div>
                <div 
                  class="w-2 h-2 rounded-full animate-bounce"
                  :class="isDark ? 'bg-blue-400' : 'bg-blue-500'"
                  style="animation-delay: 150ms;"
                ></div>
                <div 
                  class="w-2 h-2 rounded-full animate-bounce"
                  :class="isDark ? 'bg-blue-400' : 'bg-blue-500'"
                  style="animation-delay: 300ms;"
                ></div>
              </div>
              <span 
                :class="[
                  'text-sm',
                  isDark ? 'text-gray-400' : 'text-gray-500'
                ]"
              >
                AI 思考中...
              </span>
            </div>

            <!-- 工具调用 -->
            <div v-if="message.tools && message.tools.length > 0" class="mb-4 space-y-1">
              <div 
                v-for="(tool, index) in message.tools" 
                :key="`${message.message_id}-tool-${index}`"
                class="transition-all"
              >
                <!-- 折叠状态：显示为 list_memories > 格式 -->
                <button
                  @click="toggleToolExpand(message.message_id, index)"
                  :class="[
                    'w-full text-left py-1.5 px-0 flex items-center gap-2 hover:opacity-80 transition-opacity group',
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  ]"
                >
                  <span :class="[
                    'font-mono text-sm',
                    getToolNameColorClasses(tool.name, isDark)
                  ]">
                    {{ tool.name }}
                  </span>
                  <span :class="[
                    'text-xs transition-transform',
                    isToolExpanded(message.message_id, index) ? 'rotate-90' : '',
                    isDark ? 'text-gray-500' : 'text-gray-400'
                  ]">
                    >
                  </span>
                </button>
                
                <!-- 展开状态：显示完整内容 -->
                <div 
                  v-if="isToolExpanded(message.message_id, index)"
                  class="ml-4 mt-2 mb-4 pb-2 border-l-2 pl-4"
                  :class="isDark ? 'border-gray-700' : 'border-gray-200'"
                >
                  <div class="mt-2 space-y-3">
                    <!-- 参数部分 -->
                    <div>
                      <div class="flex items-center justify-between mb-1">
                        <span :class="['text-xs font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">参数</span>
                        <div class="flex items-center gap-2">
                          <!-- Switch 开关：渲染/原始 -->
                          <button
                            @click.stop="toggleToolDisplayMode(message.message_id, index, 'args')"
                            :class="[
                              'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none',
                              getToolDisplayMode(message.message_id, index, 'args') === 'rendered'
                                ? isDark ? 'bg-blue-600' : 'bg-blue-500'
                                : isDark ? 'bg-gray-600' : 'bg-gray-300'
                            ]"
                            :title="getToolDisplayMode(message.message_id, index, 'args') === 'rendered' ? '渲染模式（点击切换到原始）' : '原始模式（点击切换到渲染）'"
                          >
                            <span
                              :class="[
                                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                                getToolDisplayMode(message.message_id, index, 'args') === 'rendered' ? 'translate-x-4' : 'translate-x-0.5'
                              ]"
                            />
                          </button>
                          <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-600']">
                            {{ getToolDisplayMode(message.message_id, index, 'args') === 'rendered' ? '渲染' : '原始' }}
                          </span>
                          <button
                            @click.stop="copyToClipboard(JSON.stringify(tool.args, null, 2), `tool-args-${message.message_id}-${index}`)"
                            :class="[
                              'text-xs px-2 py-0.5 rounded transition-colors flex items-center gap-1',
                              isDark 
                                ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                            ]"
                            title="复制参数"
                          >
                            <svg :id="`tool-args-icon-${message.message_id}-${index}`" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <span :id="`tool-args-copied-${message.message_id}-${index}`" class="hidden text-green-500">已复制</span>
                          </button>
                        </div>
                      </div>
                      <div 
                        class="rounded-md border overflow-hidden"
                        :class="isDark ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50 border-gray-200'"
                      >
                        <!-- 渲染视图 -->
                        <div v-if="getToolDisplayMode(message.message_id, index, 'args') === 'rendered'" class="divide-y" :class="isDark ? 'divide-gray-700' : 'divide-gray-200'">
                          <div 
                            v-for="(value, key) in tool.args" 
                            :key="key"
                            class="px-3 py-2 flex items-start gap-3"
                          >
                            <div 
                              class="font-semibold text-xs flex-shrink-0 pt-0.5"
                              :class="isDark ? 'text-cyan-400' : 'text-cyan-600'"
                              style="min-width: 100px;"
                            >
                              {{ key }}:
                            </div>
                            <div 
                              class="text-xs flex-1 break-words"
                              :class="isDark ? 'text-cyan-300' : 'text-cyan-700'"
                            >
                              <span v-if="typeof value === 'object' && value !== null" class="font-mono" :class="isDark ? 'text-purple-400' : 'text-purple-600'">
                                {{ JSON.stringify(value, null, 2) }}
                              </span>
                              <span v-else>
                                {{ value }}
                              </span>
                            </div>
                          </div>
                        </div>
                        <!-- 原始文本视图 -->
                        <div v-else class="px-3 py-2">
                          <pre 
                            class="text-xs font-mono whitespace-pre-wrap break-words overflow-x-auto"
                            :class="isDark ? 'text-gray-200' : 'text-gray-800'"
                          >{{ JSON.stringify(tool.args, null, 2) }}</pre>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 结果部分 -->
                    <div v-if="tool.result">
                      <div class="flex items-center justify-between mb-1">
                        <span :class="['text-xs font-semibold', isDark ? 'text-gray-300' : 'text-gray-700']">结果</span>
                        <div class="flex items-center gap-2">
                          <!-- Switch 开关：渲染/原始 -->
                          <button
                            @click.stop="toggleToolDisplayMode(message.message_id, index, 'result')"
                            :class="[
                              'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none',
                              getToolDisplayMode(message.message_id, index, 'result') === 'rendered'
                                ? isDark ? 'bg-blue-600' : 'bg-blue-500'
                                : isDark ? 'bg-gray-600' : 'bg-gray-300'
                            ]"
                            :title="getToolDisplayMode(message.message_id, index, 'result') === 'rendered' ? '渲染模式（点击切换到原始）' : '原始模式（点击切换到渲染）'"
                          >
                            <span
                              :class="[
                                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                                getToolDisplayMode(message.message_id, index, 'result') === 'rendered' ? 'translate-x-4' : 'translate-x-0.5'
                              ]"
                            />
                          </button>
                          <span :class="['text-xs', isDark ? 'text-gray-400' : 'text-gray-600']">
                            {{ getToolDisplayMode(message.message_id, index, 'result') === 'rendered' ? '渲染' : '原始' }}
                          </span>
                          <button
                            @click.stop="copyToClipboard(typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result, null, 2), `tool-result-${message.message_id}-${index}`)"
                            :class="[
                              'text-xs px-2 py-0.5 rounded transition-colors flex items-center gap-1',
                              isDark 
                                ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' 
                                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                            ]"
                            title="复制结果"
                          >
                            <svg :id="`tool-result-icon-${message.message_id}-${index}`" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <span :id="`tool-result-copied-${message.message_id}-${index}`" class="hidden text-green-500">已复制</span>
                          </button>
                        </div>
                      </div>
                      <div 
                        class="rounded-md border overflow-hidden"
                        :class="isDark ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50 border-gray-200'"
                      >
                        <!-- 渲染视图 -->
                        <div v-if="getToolDisplayMode(message.message_id, index, 'result') === 'rendered'">
                          <!-- 将结果统一转换为 list 格式进行渲染 -->
                          <template v-for="(item, _itemIndex) in normalizeResultToList(tool.result)" :key="_itemIndex">
                            <div 
                              class="border-t first:border-t-0 divide-y"
                              :class="isDark ? 'border-gray-700 divide-gray-700' : 'border-gray-200 divide-gray-200'"
                            >
                              <!-- 每个卡片 -->
                              <div v-if="isDict(item)" class="px-3 py-2">
                                <!-- 如果项是 dict，渲染为 key: value 格式 -->
                                <div 
                                  v-for="(value, key) in item" 
                                  :key="key"
                                  class="flex items-start gap-3 py-1 first:pt-0 last:pb-0"
                                >
                                  <div 
                                    class="font-semibold text-xs flex-shrink-0 pt-0.5"
                                    :class="isDark ? 'text-emerald-400' : 'text-emerald-600'"
                                    style="min-width: 100px;"
                                  >
                                    {{ key }}:
                                  </div>
                                  <div 
                                    class="text-xs flex-1 break-words"
                                    :class="isDark ? 'text-emerald-300' : 'text-emerald-700'"
                                  >
                                    {{ value }}
                                  </div>
                                </div>
                              </div>
                              <!-- 如果项是基本类型，直接显示值 -->
                              <div v-else class="px-3 py-2">
                                <div class="text-xs break-words" :class="isDark ? 'text-emerald-300' : 'text-emerald-700'">
                                  {{ item }}
                                </div>
                              </div>
                            </div>
                          </template>
                          <!-- 如果结果为空 -->
                          <div v-if="normalizeResultToList(tool.result).length === 0" class="px-3 py-2">
                            <div class="text-xs" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                              无结果
                            </div>
                          </div>
                        </div>
                        <!-- 原始文本视图 -->
                        <div v-else class="px-3 py-2">
                          <pre 
                            class="text-xs font-mono whitespace-pre-wrap break-words overflow-x-auto"
                            :class="isDark ? 'text-gray-200' : 'text-gray-800'"
                          >{{ typeof tool.result === 'string' ? formatToolResult(tool.result) : JSON.stringify(tool.result, null, 2) }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Markdown 内容 -->
            <div 
              v-if="message.context"
              class="prose prose-sm max-w-none markdown-content mt-2"
              :class="[
                isDark ? 'prose-invert prose-headings:text-gray-100 prose-p:text-gray-300 prose-strong:text-gray-100' : 'prose-headings:text-gray-900 prose-p:text-gray-700',
                message.tools && message.tools.length > 0 ? '' : ''
              ]"
              v-html="renderMarkdown(message.context)"
              ref="markdownContentRef"
            ></div>

            <!-- Suggest 建议 -->
            <div v-if="message.suggests && message.suggests.length > 0" class="mt-4">
              <div 
                :class="[
                  'text-xs font-semibold mb-2',
                  isDark ? 'text-gray-400' : 'text-gray-600'
                ]"
              >
                建议：
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="(suggest, index) in message.suggests"
                  :key="index"
                  @click="useSuggest(suggest)"
                  :class="[
                    'px-3 py-1 rounded text-sm transition-colors',
                    isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300'
                  ]"
                >
                  {{ formatSuggest(suggest) }}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>

    </div>


    <!-- 清空历史确认对话框（radix-vue/shadcn） -->
    <ConfirmDialog
      :show="showClearHistoryDialog"
      title="确认清空历史"
      :message="'确定要清空所有历史记录吗？\n\n此操作不可恢复，将删除该项目的所有聊天消息。'"
      type="danger"
      @confirm="confirmClearHistory"
      @cancel="() => { showClearHistoryDialog = false }"
    />

    <!-- 输入区域：固定在底部 -->
    <div 
      :class="[
        'p-4 border-t flex-shrink-0',
        isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
      ]"
    >
      <div class="flex items-end gap-2">
        <textarea
          ref="inputRef"
          v-model="inputText"
          @keydown="handleKeydown"
          :disabled="isStreaming"
          placeholder="输入消息...（按 Enter 发送，Shift+Enter 换行）"
          :class="[
            'flex-1 px-4 py-2 rounded-lg border resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
            isDark
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
            isStreaming ? 'opacity-50 cursor-not-allowed' : ''
          ]"
          rows="1"
          style="min-height: 40px; max-height: 200px;"
        ></textarea>
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || isStreaming"
          :class="[
            'px-6 py-2 rounded-lg font-medium transition-colors',
            inputText.trim() && !isStreaming
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : isDark
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          ]"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { useNavigationStore } from '../stores/navigation'
import { storeToRefs } from 'pinia'
import api from '../api'
import { getApiBaseURL } from '../utils/apiConfig'
import { marked } from 'marked'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import hljs from 'highlight.js'
// 动态导入 highlight.js 样式（根据主题）
import 'highlight.js/styles/github-dark.css'

// 类型定义
interface ChatMessage {
  message_id: string
  project_id: string | null
  role: 'user' | 'assistant' | 'system'
  context: string
  status: string
  message_type: string
  tools: ToolCall[]
  suggests: string[]
  created_at: string
  _internalKey?: string  // 内部稳定 key，用于 Vue 的 :key 绑定
}

interface ToolCall {
  name: string
  args: Record<string, any>
  result: string | null
}

// 主题
const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 导航栏相关（用于响应式布局）
const navigationStore = useNavigationStore()
const { width: navigationWidth } = storeToRefs(navigationStore)

// 项目相关（使用全局 store）
const projectStore = useProjectStore()
const { 
  selectedProjectId, 
  selectedProject
} = storeToRefs(projectStore)

// 消息相关
const messages = ref<ChatMessage[]>([])
const loadingHistory = ref(false)

// 输入相关
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const messagesContainerRef = ref<HTMLDivElement | null>(null)

// 流式传输相关
const isStreaming = ref(false)
let currentEventSource: EventSource | null = null
let currentAssistantMessage: Partial<ChatMessage> | null = null

// 清空历史确认对话框
const showClearHistoryDialog = ref(false)

// 编辑消息相关
const editingMessageId = ref<string | null>(null)
const editingText = ref('')
const editingTextareaRef = ref<HTMLTextAreaElement | null>(null)

// 工具调用展开状态：messageId -> toolIndex -> expanded
const toolExpandState = ref<Record<string, Record<number, boolean>>>({})

// 工具调用显示模式：messageId -> toolIndex -> { args: 'rendered'|'raw', result: 'rendered'|'raw' }
const toolDisplayMode = ref<Record<string, Record<number, { args: 'rendered' | 'raw', result: 'rendered' | 'raw' }>>>({})

// 比较两条消息是否相同（用于差异刷新）
const areMessagesEqual = (msg1: ChatMessage, msg2: ChatMessage): boolean => {
  return (
    msg1.message_id === msg2.message_id &&
    msg1.context === msg2.context &&
    msg1.status === msg2.status &&
    JSON.stringify(msg1.tools) === JSON.stringify(msg2.tools) &&
    JSON.stringify(msg1.suggests) === JSON.stringify(msg2.suggests) &&
    msg1.role === msg2.role &&
    msg1.message_type === msg2.message_type
  )
}

// 智能合并消息列表：只更新有变化的项，保持未变化项的引用不变
const mergeMessages = (oldMessages: ChatMessage[], newMessages: ChatMessage[]): ChatMessage[] => {
  // 如果长度不同，直接返回新列表
  if (oldMessages.length !== newMessages.length) {
    return newMessages
  }
  
  // 检查是否有临时消息需要替换
  const hasTempMessages = oldMessages.some(msg => 
    msg.message_id.startsWith('temp-') || msg.message_id.startsWith('streaming-')
  )
  
  if (hasTempMessages) {
    // 有临时消息，需要替换整个列表
    return newMessages
  }
  
  // 逐个比较并合并
  let hasChanges = false
  const mergedMessages: ChatMessage[] = []
  
  for (let i = 0; i < oldMessages.length; i++) {
    const oldMsg = oldMessages[i]
    const newMsg = newMessages[i]
    
    if (oldMsg && newMsg && areMessagesEqual(oldMsg, newMsg)) {
      // 内容相同，保持原对象引用（避免Vue重新渲染）
      mergedMessages.push(oldMsg)
    } else if (newMsg) {
      // 内容不同，使用新对象
      mergedMessages.push(newMsg)
      hasChanges = true
    } else if (oldMsg) {
      // 新消息不存在，保留旧消息
      mergedMessages.push(oldMsg)
    }
  }
  
  // 如果没有任何变化，返回原数组（保持引用不变）
  if (!hasChanges) {
    return oldMessages
  }
  
  return mergedMessages
}

// 加载历史记录（支持差异刷新）
const loadHistory = async (forceReload: boolean = false) => {
  if (selectedProjectId.value === undefined) {
    return
  }
  
  // 如果强制重新加载，显示 loading
  if (forceReload) {
    loadingHistory.value = true
  }
  
  try {
    const response = await api.get('/history/all', {
      params: { project_id: selectedProjectId.value || null }
    })
    const loadedMessages = (response as any).data || response
    
    // 为每条历史消息添加稳定的 _internalKey
    const newMessages = (Array.isArray(loadedMessages) ? loadedMessages : []).map((msg: ChatMessage) => ({
      ...msg,
      _internalKey: msg._internalKey || `loaded-${msg.message_id}`
    }))
    
    // 差异刷新：智能合并消息列表
    if (!forceReload && messages.value.length > 0) {
      const mergedMessages = mergeMessages(messages.value, newMessages)
      
      // 如果合并后的数组引用与原数组相同，说明没有任何变化，不更新UI
      if (mergedMessages === messages.value) {
        if (loadingHistory.value) {
          loadingHistory.value = false
        }
        return
      }
      
      // 有变化，更新消息列表
      messages.value = mergedMessages
    } else {
      // 强制重新加载或首次加载，直接替换
      messages.value = newMessages
    }
    
    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isStreaming.value) {
    return
  }

  const message = inputText.value.trim()
  inputText.value = ''

  // 关闭之前的连接
  if (currentEventSource) {
    currentEventSource.close()
    currentEventSource = null
  }

  // 创建用户消息（临时显示，稍后会被数据库中的消息替换）
  const userInternalKey = `user-${Date.now()}-${Math.random()}`
  const userMessage: ChatMessage = {
    message_id: `temp-${Date.now()}`,
    project_id: selectedProjectId.value || null,
    role: 'user',
    context: message,
    status: 'ready',
    message_type: 'normal',
    tools: [],
    suggests: [],
    created_at: new Date().toISOString(),
    _internalKey: userInternalKey
  }
  messages.value.push(userMessage)
  scrollToBottom()

  // 开始流式传输
  isStreaming.value = true
  const assistantInternalKey = `assistant-${Date.now()}-${Math.random()}`
  currentAssistantMessage = {
    message_id: `streaming-${Date.now()}`,
    project_id: selectedProjectId.value || null,
    role: 'assistant',
    context: '',
    status: 'thinking',
    message_type: 'normal',
    tools: [],
    suggests: [],
    _internalKey: assistantInternalKey
  }
  messages.value.push(currentAssistantMessage as ChatMessage)
  scrollToBottom()

  try {
    // 使用 fetch 发送 POST 请求并读取流式响应
    const baseURL = getApiBaseURL()
    
    const response = await fetch(`${baseURL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        project_id: selectedProjectId.value || null
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('响应体为空')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      
      // 处理完整的 SSE 消息（以 \n\n 分隔）
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const lines = part.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim()
              if (jsonStr) {
                const data = JSON.parse(jsonStr)
                handleStreamEvent(data)
              }
            } catch (e) {
              console.error('解析 SSE 数据失败:', e, line)
            }
          }
        }
      }
    }

    // 处理剩余的 buffer
    if (buffer.trim()) {
      const lines = buffer.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6).trim()
            if (jsonStr) {
              const data = JSON.parse(jsonStr)
              handleStreamEvent(data)
            }
          } catch (e) {
            console.error('解析 SSE 数据失败:', e)
          }
        }
      }
    }

  } catch (error: any) {
    console.error('发送消息失败:', error)
    if (currentAssistantMessage) {
      currentAssistantMessage.status = 'error'
      currentAssistantMessage.context = `错误: ${error.message || '发送失败'}`
    }
    // 发生错误时，强制重新加载以确保数据同步
    await loadHistory(true)
  } finally {
    isStreaming.value = false
    currentEventSource = null
    // 流式传输成功完成后，使用差异刷新（不显示 loading）
    // 只在数据有变化时才更新 UI，避免屏闪
    await loadHistory(false)
  }
}

// 处理流式事件
const handleStreamEvent = (data: any) => {
  if (!currentAssistantMessage) return

  const eventType = data.type

  if (eventType === 'message_id') {
    // 更新消息ID（将临时ID替换为真实ID）
    const oldId = currentAssistantMessage?.message_id
    if (currentAssistantMessage && oldId) {
      currentAssistantMessage.message_id = data.message_id
      // 找到临时消息并更新ID（保持 _internalKey 不变以避免重新渲染）
      const index = messages.value.findIndex(m => m.message_id === oldId)
      if (index !== -1 && messages.value[index]) {
        messages.value[index].message_id = data.message_id
        // 保留 _internalKey，避免因 key 变化导致组件重新挂载
      }
    }
  } else if (eventType === 'content') {
    // 流式更新内容
    if (currentAssistantMessage) {
      currentAssistantMessage.context = (currentAssistantMessage.context || '') + (data.content || '')
      // 找到对应的消息并实时更新
      const index = messages.value.findIndex(m => 
        m.message_id === currentAssistantMessage?.message_id
      )
      if (index !== -1 && messages.value[index]) {
        // 直接更新内容，触发响应式更新
        messages.value[index].context = currentAssistantMessage.context || ''
        // 确保工具调用和建议也更新
        if (currentAssistantMessage.tools) {
          messages.value[index].tools = [...currentAssistantMessage.tools]
        }
        if (currentAssistantMessage.suggests) {
          messages.value[index].suggests = [...(currentAssistantMessage.suggests || [])]
        }
      }
      scrollToBottom()
      // 更新代码块复制功能
      setupCodeBlockCopy()
    }
  } else if (eventType === 'tool_start') {
    if (!currentAssistantMessage.tools) {
      currentAssistantMessage.tools = []
    }
    currentAssistantMessage.tools.push({
      name: data.name || '',
      args: data.args || {},
      result: null
    })
    // 实时更新消息中的工具调用
    const index = messages.value.findIndex(m => m.message_id === currentAssistantMessage?.message_id)
    if (index !== -1 && messages.value[index] && currentAssistantMessage.tools) {
      messages.value[index].tools = [...currentAssistantMessage.tools]
    }
  } else if (eventType === 'tool_end') {
    if (currentAssistantMessage.tools && currentAssistantMessage.tools.length > 0) {
      const lastTool = currentAssistantMessage.tools[currentAssistantMessage.tools.length - 1]
      if (lastTool && lastTool.name === data.name) {
        lastTool.result = data.result
      }
    }
    // 实时更新消息中的工具调用
    const index = messages.value.findIndex(m => m.message_id === currentAssistantMessage?.message_id)
    if (index !== -1 && messages.value[index] && currentAssistantMessage.tools) {
      messages.value[index].tools = [...currentAssistantMessage.tools]
    }
  } else if (eventType === 'tools') {
    currentAssistantMessage.tools = data.tools || []
    // 更新消息
    const index = messages.value.findIndex(m => m.message_id === currentAssistantMessage?.message_id)
    if (index !== -1 && messages.value[index]) {
      messages.value[index] = { ...currentAssistantMessage } as ChatMessage
    }
  } else if (eventType === 'suggests') {
    currentAssistantMessage.suggests = data.suggests || []
    // 更新消息
    const index = messages.value.findIndex(m => m.message_id === currentAssistantMessage?.message_id)
    if (index !== -1) {
      messages.value[index] = { ...currentAssistantMessage } as ChatMessage
    }
  } else if (eventType === 'status') {
    currentAssistantMessage.status = data.status || 'ready'
    // 更新消息
    const index = messages.value.findIndex(m => m.message_id === currentAssistantMessage?.message_id)
    if (index !== -1) {
      messages.value[index] = { ...currentAssistantMessage } as ChatMessage
    }
  } else if (eventType === 'error') {
    currentAssistantMessage.status = 'error'
    currentAssistantMessage.context = (currentAssistantMessage.context || '') + `\n\n错误: ${data.error || '未知错误'}`
  } else if (eventType === 'done') {
    // 流式传输完成
  }
}

// 键盘处理
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 使用建议
const useSuggest = (suggest: string) => {
  // 如果是图片建议，可能需要特殊处理
  if (suggest.startsWith('image:')) {
    // 处理图片建议
    alert('图片建议功能待实现')
    return
  }
  // 文字建议直接填入输入框
  inputText.value = suggest
  inputRef.value?.focus()
}

// 格式化建议
const formatSuggest = (suggest: string): string => {
  if (suggest.startsWith('image:')) {
    return '图片'
  }
  return suggest
}

// 工具调用展开/折叠
const toggleToolExpand = (messageId: string, toolIndex: number) => {
  if (!toolExpandState.value[messageId]) {
    toolExpandState.value[messageId] = {}
  }
  toolExpandState.value[messageId][toolIndex] = !toolExpandState.value[messageId][toolIndex]
}

const isToolExpanded = (messageId: string, toolIndex: number): boolean => {
  return toolExpandState.value[messageId]?.[toolIndex] ?? false
}

// 切换工具显示模式
const toggleToolDisplayMode = (messageId: string, toolIndex: number, type: 'args' | 'result') => {
  if (!toolDisplayMode.value[messageId]) {
    toolDisplayMode.value[messageId] = {}
  }
  if (!toolDisplayMode.value[messageId][toolIndex]) {
    toolDisplayMode.value[messageId][toolIndex] = { args: 'rendered', result: 'rendered' }
  }
  
  const currentMode = toolDisplayMode.value[messageId][toolIndex][type]
  toolDisplayMode.value[messageId][toolIndex][type] = currentMode === 'rendered' ? 'raw' : 'rendered'
}

// 获取工具显示模式
const getToolDisplayMode = (messageId: string, toolIndex: number, type: 'args' | 'result'): 'rendered' | 'raw' => {
  return toolDisplayMode.value[messageId]?.[toolIndex]?.[type] ?? 'rendered'
}

// 根据工具名称获取颜色类别
const getToolColorCategory = (toolName: string): string => {
  // Session/Project 管理工具
  if (['create_session', 'get_session', 'list_sessions', 'update_session', 'delete_session', 'update_progress', 'get_project', 'update_project'].some(prefix => toolName.startsWith(prefix))) {
    return 'session'
  }
  // Memory 管理工具
  if (['create_memory', 'get_memory', 'list_memories', 'update_memory', 'delete_memory', 'delete_all_memories', 'get_key_description', 'get_all_key_descriptions'].some(prefix => toolName.startsWith(prefix))) {
    return 'memory'
  }
  // Actor 管理工具
  if (['create_actor', 'get_actor', 'list_actors', 'update_actor', 'remove_actor', 'add_example', 'remove_example', 'generate_portrait', 'add_actor_portrait', 'get_tag_description', 'get_all_tag_descriptions'].some(prefix => toolName.startsWith(prefix))) {
    return 'actor'
  }
  // Reader 工具
  if (['get_line', 'get_chapter_lines', 'get_lines_range', 'get_chapters', 'get_chapter', 'put_chapter', 'get_stats', 'start_iteration'].some(prefix => toolName.startsWith(prefix))) {
    return 'reader'
  }
  // Novel 内容管理工具
  if (['get_project_content', 'get_chapter_content', 'get_line_content'].some(prefix => toolName.startsWith(prefix))) {
    return 'novel'
  }
  // Draw 工具
  if (['get_loras', 'get_sd_models', 'generate', 'get_image'].some(prefix => toolName.startsWith(prefix))) {
    return 'draw'
  }
  // LLM 辅助工具
  if (['add_choices', 'get_choices', 'clear_choices'].some(prefix => toolName.startsWith(prefix))) {
    return 'llm'
  }
  // Illustration 工具
  if (['create_illustration', 'list_illustrations', 'get_illustration', 'update_illustration', 'delete_illustration'].some(prefix => toolName.startsWith(prefix))) {
    return 'illustration'
  }
  // File 工具
  if (['get_project_novel', 'get_illustration_image'].some(prefix => toolName.startsWith(prefix))) {
    return 'file'
  }
  return 'default'
}

// 获取工具背景颜色类（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _getToolColorClasses = (_toolName: string, _dark: boolean): string => {
  const category = getToolColorCategory(_toolName)
  const colorMap: Record<string, { bg: string, border: string, text: string }> = {
    session: {
      bg: _dark ? 'bg-blue-900/30' : 'bg-blue-50',
      border: _dark ? 'border-blue-700' : 'border-blue-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    memory: {
      bg: _dark ? 'bg-purple-900/30' : 'bg-purple-50',
      border: _dark ? 'border-purple-700' : 'border-purple-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    actor: {
      bg: _dark ? 'bg-pink-900/30' : 'bg-pink-50',
      border: _dark ? 'border-pink-700' : 'border-pink-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    reader: {
      bg: _dark ? 'bg-teal-900/30' : 'bg-teal-50',
      border: _dark ? 'border-teal-700' : 'border-teal-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    novel: {
      bg: _dark ? 'bg-cyan-900/30' : 'bg-cyan-50',
      border: _dark ? 'border-cyan-700' : 'border-cyan-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    draw: {
      bg: _dark ? 'bg-orange-900/30' : 'bg-orange-50',
      border: _dark ? 'border-orange-700' : 'border-orange-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    llm: {
      bg: _dark ? 'bg-green-900/30' : 'bg-green-50',
      border: _dark ? 'border-green-700' : 'border-green-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    illustration: {
      bg: _dark ? 'bg-purple-900/30' : 'bg-purple-50',
      border: _dark ? 'border-purple-700' : 'border-purple-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    file: {
      bg: _dark ? 'bg-amber-900/30' : 'bg-amber-50',
      border: _dark ? 'border-amber-700' : 'border-amber-200',
      text: _dark ? 'text-gray-200' : 'text-gray-800'
    },
    default: {
      bg: _dark ? 'bg-gray-700' : 'bg-gray-50',
      border: _dark ? 'border-gray-600' : 'border-gray-200',
      text: _dark ? 'text-gray-300' : 'text-gray-700'
    }
  }
  const colors = colorMap[category] || colorMap.default
  return `${colors?.bg || ''} ${colors?.border || ''} border ${colors?.text || ''}`
}

// 获取工具名称颜色类（Cursor 风格：更柔和的颜色）
const getToolNameColorClasses = (toolName: string, dark: boolean): string => {
  const category = getToolColorCategory(toolName)
  const colorMap: Record<string, string> = {
    session: dark ? 'text-blue-400' : 'text-blue-500',
    memory: dark ? 'text-purple-400' : 'text-purple-500',
    actor: dark ? 'text-pink-400' : 'text-pink-500',
    reader: dark ? 'text-teal-400' : 'text-teal-500',
    novel: dark ? 'text-cyan-400' : 'text-cyan-500',
    draw: dark ? 'text-orange-400' : 'text-orange-500',
    llm: dark ? 'text-green-400' : 'text-green-500',
    illustration: dark ? 'text-purple-400' : 'text-purple-500',
    file: dark ? 'text-amber-400' : 'text-amber-500',
    default: dark ? 'text-gray-300' : 'text-gray-600'
  }
  return colorMap[category] || colorMap.default || ''
}

// 格式化工具参数（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _formatToolArgs = (_args: Record<string, any>): string => {
  const parts: string[] = []
  for (const [key, value] of Object.entries(_args)) {
    const valStr = typeof value === 'string' ? `"${value}"` : String(value)
    parts.push(`${key}=${valStr}`)
  }
  return parts.join(', ')
}

// 判断结果是否是 JSON 格式（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _isJSONResult = (_result: string | null): boolean => {
  if (!_result || typeof _result !== 'string') return false
  try {
    JSON.parse(_result)
    return true
  } catch {
    return false
  }
}

// 解析 JSON 结果
const parseJSONResult = (result: string | null): any => {
  if (!result || typeof result !== 'string') return null
  try {
    return JSON.parse(result)
  } catch {
    return null
  }
}

// 将结果标准化为 list 格式（dict 转换为只有一个 dict 项的 list）
const normalizeResultToList = (result: any): any[] => {
  // 如果结果已经是对象或数组，直接处理
  if (typeof result === 'object' && result !== null) {
    // 如果是数组，直接返回
    if (Array.isArray(result)) {
      return result
    }
    // 如果是对象（dict），转换为只有一个对象的数组
    return [result]
  }
  
  // 如果是字符串，尝试解析为 JSON
  if (typeof result === 'string') {
    const parsed = parseJSONResult(result)
    if (parsed === null) {
      // 如果解析失败，作为基本类型处理
      return [result]
    }
    
    // 解析成功，递归处理
    return normalizeResultToList(parsed)
  }
  
  // 如果是基本类型，转换为数组
  if (result === null || result === undefined) {
    return []
  }
  
  return [result]
}

// 判断是否是字典类型
const isDict = (value: any): boolean => {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

// 格式化工具结果（完整内容）
const formatToolResult = (result: string | null): string => {
  if (!result || typeof result !== 'string') return ''
  
  // 尝试解析为 JSON 并格式化
  try {
    const parsed = JSON.parse(result)
    return JSON.stringify(parsed, null, 2)
  } catch {
    // 如果不是 JSON，直接返回原内容
    return result
  }
}

// 复制到剪贴板
const copyToClipboard = async (text: string, elementId: string) => {
  try {
    await navigator.clipboard.writeText(text)
    
    // 显示"已复制"提示
    const copiedId = elementId.replace('tool-args-', 'tool-args-copied-').replace('tool-result-', 'tool-result-copied-')
    const iconId = elementId.replace('tool-args-', 'tool-args-icon-').replace('tool-result-', 'tool-result-icon-')
    
    const copiedElement = document.getElementById(copiedId)
    const iconElement = document.getElementById(iconId)
    
    if (copiedElement && iconElement) {
      iconElement.classList.add('hidden')
      copiedElement.classList.remove('hidden')
      setTimeout(() => {
        copiedElement.classList.add('hidden')
        iconElement.classList.remove('hidden')
      }, 2000)
    }
  } catch (err) {
    console.error('复制失败:', err)
  }
}

// 截断结果（用于折叠状态）（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _truncateResult = (_result: string): string => {
  if (_result.length > 100) {
    return _result.substring(0, 100) + '...'
  }
  return _result
}

// 设置编辑文本框 ref
const setEditingTextareaRef = (el: any) => {
  editingTextareaRef.value = el ? (el as HTMLTextAreaElement) : null
}

// 开始编辑消息
const startEditMessage = (messageId: string, content: string) => {
  editingMessageId.value = messageId
  editingText.value = content
  nextTick(() => {
    editingTextareaRef.value?.focus()
  })
}

// 取消编辑
const cancelEdit = () => {
  editingMessageId.value = null
  editingText.value = ''
  editingTextareaRef.value = null
}

// 确认重新开始（使用编辑后的内容）
const confirmRestart = async () => {
  if (!editingMessageId.value) return
  
  const editedText = editingText.value.trim()
  if (!editedText) {
    alert('消息内容不能为空')
    return
  }

  const messageIdToRestart = editingMessageId.value
  
  try {
    // 找到这条消息的索引
    const messageIndex = messages.value.findIndex(m => m.message_id === messageIdToRestart)
    if (messageIndex === -1) {
      cancelEdit()
      return
    }

    // 先取消编辑状态
    cancelEdit()

    // 删除从这条消息开始的所有消息（包括这条消息本身）
    const messagesToDelete = messages.value.slice(messageIndex)
    for (const msg of messagesToDelete) {
      try {
        await api.delete(`/history/${msg.message_id}`)
      } catch (e) {
        console.error(`删除消息 ${msg.message_id} 失败:`, e)
      }
    }

    // 重新加载历史记录（删除消息后需要强制重新加载）
    await loadHistory(true)

    // 等待一下确保历史记录已更新
    await nextTick()
    
    // 使用编辑后的内容发送新消息（这会创建新的用户消息和AI回复）
    inputText.value = editedText
    await nextTick()
    await sendMessage()
  } catch (error) {
    console.error('重新开始失败:', error)
    alert('重新开始失败')
    cancelEdit()
  }
}

// 确认清空历史
const confirmClearHistory = async () => {
  showClearHistoryDialog.value = false

  try {
    await api.delete('/history/clear', {
      params: { project_id: selectedProjectId.value || null }
    })
    messages.value = []
  } catch (error) {
    console.error('清空历史失败:', error)
    alert('清空历史失败')
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
    // 更新代码块复制功能
    setupCodeBlockCopy()
  })
}

// Markdown 渲染配置（参考 HelpView）
const renderer = new marked.Renderer()

// 自定义代码块渲染器，使用 highlight.js 进行语法高亮
// @ts-ignore - marked 的类型定义可能不完整
renderer.code = (code: string | any, language: string | undefined | null) => {
  const codeStr = String(code || '')
  let lang: string = ''
  let highlighted: string
  
  const providedLang = (language && typeof language === 'string') 
    ? language.trim().toLowerCase() 
    : ''
  
  try {
    if (providedLang && hljs.getLanguage(providedLang)) {
      const result = hljs.highlight(codeStr, { language: providedLang })
      highlighted = String(result.value || codeStr)
      lang = providedLang
    } else {
      const result = hljs.highlightAuto(codeStr)
      highlighted = String(result.value || codeStr)
      lang = result.language || 'plaintext'
    }
  } catch (err) {
    console.warn('代码高亮失败:', err)
    highlighted = codeStr
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    lang = providedLang || 'plaintext'
  }
  
  const codeBlockId = `code-block-${Math.random().toString(36).substr(2, 9)}`
  
  return `
    <div class="code-block-wrapper" data-code-id="${codeBlockId}">
      <div class="code-block-header">
        <button class="code-block-copy-btn" data-copy-target="${codeBlockId}" title="复制代码">
          <svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
          </svg>
          <svg class="check-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="display: none;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </button>
      </div>
      <pre class="hljs" id="${codeBlockId}"><code class="language-${lang}">${highlighted}</code></pre>
    </div>
  `
}

marked.setOptions({
  renderer: renderer,
  breaks: true,
  gfm: true
})

// Markdown 渲染
const renderMarkdown = (content: string): string => {
  try {
    return marked.parse(content) as string
  } catch (e) {
    console.error('Markdown 渲染失败:', e)
    return content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

// 存储已添加的事件监听器，避免重复添加
const codeBlockCopyHandlers = new Map<Element, () => void>()

// 处理代码块复制功能
const setupCodeBlockCopy = () => {
  nextTick(() => {
    document.querySelectorAll('.code-block-copy-btn').forEach(btn => {
      // 如果已经添加过监听器，跳过
      if (codeBlockCopyHandlers.has(btn)) return
      
      const targetId = btn.getAttribute('data-copy-target')
      if (!targetId) return
      
      const handler = async () => {
        const codeElement = document.getElementById(targetId)
        if (!codeElement) return
        
        const code = codeElement.textContent || ''
        try {
          await navigator.clipboard.writeText(code)
          
          // 显示成功图标
          const copyIcon = btn.querySelector('.copy-icon') as HTMLElement
          const checkIcon = btn.querySelector('.check-icon') as HTMLElement
          if (copyIcon && checkIcon) {
            copyIcon.style.display = 'none'
            checkIcon.style.display = 'block'
            setTimeout(() => {
              copyIcon.style.display = 'block'
              checkIcon.style.display = 'none'
            }, 2000)
          }
        } catch (err) {
          console.error('复制失败:', err)
        }
      }
      
      btn.addEventListener('click', handler)
      codeBlockCopyHandlers.set(btn, handler)
    })
  })
}


// 监听项目变化（使用 store）
watch(() => selectedProjectId.value, () => {
  loadHistory()
})

// 点击外部关闭编辑模式的处理器
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (editingMessageId.value && !target.closest('.editing-message-container')) {
    cancelEdit()
  }
}

onMounted(async () => {
  // 初始化 store（从 localStorage 恢复项目ID）
  projectStore.init()
  
  // 确保项目列表已加载
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  } else {
    // 如果项目列表已存在但 currentProject 为空，重新加载当前项目
    if (projectStore.selectedProjectId && !projectStore.currentProject) {
      await projectStore.loadCurrentProject()
    }
  }
  
  // 加载历史记录
  loadHistory()
  
  // 点击外部关闭编辑模式
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  // 清理事件监听器
  document.removeEventListener('click', handleClickOutside)
  
  // 清理代码块复制按钮的事件监听器
  codeBlockCopyHandlers.forEach((handler, btn) => {
    btn.removeEventListener('click', handler)
  })
  codeBlockCopyHandlers.clear()
})
</script>

<style scoped>
.message-item {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 优化思考中的弹跳动画 */
@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-8px);
  }
}

.animate-bounce {
  animation: bounce 1.4s infinite ease-in-out;
}

.markdown-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
}

.markdown-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.9em;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-content :deep(.code-block-wrapper) {
  margin: 1rem 0;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid;
  border-color: var(--code-border-color, rgba(110, 118, 129, 0.2));
}

.markdown-content :deep(.code-block-header) {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--code-header-bg, rgba(110, 118, 129, 0.1));
  border-bottom: 1px solid;
  border-bottom-color: var(--code-border-color, rgba(110, 118, 129, 0.2));
}

.markdown-content :deep(.code-block-copy-btn) {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--code-btn-color, rgba(110, 118, 129, 0.8));
  transition: color 0.2s;
}

.markdown-content :deep(.code-block-copy-btn:hover) {
  color: var(--code-btn-hover-color, rgba(110, 118, 129, 1));
}

.markdown-content :deep(.code-block-copy-btn svg) {
  width: 16px;
  height: 16px;
}

.markdown-content :deep(.code-block-wrapper pre) {
  margin: 0;
  padding: 1rem;
  overflow-x: auto;
  background-color: var(--code-bg, rgba(0, 0, 0, 0.05));
}

.markdown-content :deep(.code-block-wrapper code) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* 工具调用代码块样式 */
.tool-call-code-block pre {
  margin: 0;
  padding: 0;
  background: transparent !important;
}

.tool-call-code-block pre code {
  background: transparent !important;
  padding: 0;
  font-size: 0.75rem;
  line-height: 1.6;
}

/* highlight.js 样式适配 */
.tool-call-code-block :deep(.hljs) {
  background: transparent !important;
  padding: 0;
  display: block;
}

.tool-call-code-block :deep(.hljs-keyword) {
  color: #c792ea;
}

.tool-call-code-block :deep(.hljs-string) {
  color: #c3e88d;
}

.tool-call-code-block :deep(.hljs-number) {
  color: #f78c6c;
}

.tool-call-code-block :deep(.hljs-literal) {
  color: #ff5370;
}

.tool-call-code-block :deep(.hljs-punctuation) {
  color: #89ddff;
}

.tool-call-code-block :deep(.hljs-property) {
  color: #82aaff;
}

.tool-call-code-block :deep(.hljs-attr) {
  color: #ffcb6b;
}
</style>
