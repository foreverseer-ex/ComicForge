<template>
  <div class="space-y-6">
    <!-- 页面标题和语言切换 -->
    <div 
      :class="[
        'flex items-center justify-between pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <h1 
        :class="[
          'text-3xl font-bold',
          isDark ? 'text-white' : 'text-gray-900'
        ]"
      >
        {{ titleText }}
      </h1>
      
      <!-- 语言切换按钮 -->
      <button
        @click="toggleLanguage"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
          isDark
            ? 'bg-gray-700 hover:bg-gray-600 text-white'
            : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
        ]"
        :title="currentLang === 'zh' ? 'Switch to English' : '切换到中文'"
      >
        <LanguageIcon class="w-5 h-5" />
        <span>{{ currentLang === 'zh' ? 'EN' : '中文' }}</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
           :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" 
         :class="[
           'p-4 rounded-lg border',
           isDark 
             ? 'bg-red-900/20 border-red-700 text-red-300' 
             : 'bg-red-50 border-red-200 text-red-700'
         ]"
    >
      <p class="font-medium">加载失败</p>
      <p class="text-sm mt-1">{{ error }}</p>
      <button
        @click="loadHelp"
        :class="[
          'mt-3 px-4 py-2 rounded-lg text-sm transition-colors',
          isDark
            ? 'bg-red-700 hover:bg-red-600 text-white'
            : 'bg-red-600 hover:bg-red-700 text-white'
        ]"
      >
        重试
      </button>
    </div>

    <!-- Markdown 内容容器 -->
    <div v-else
         :class="[
           'markdown-container rounded-lg border',
           isDark 
             ? 'bg-[#1e1e1e] border-gray-700 dark-theme'
             : 'bg-white border-gray-200 light-theme'
         ]"
    >
      <div 
        :class="[
          'prose prose-base max-w-none px-8 py-6',
          isDark ? 'prose-invert' : ''
        ]"
        v-html="renderedContent"
        @click="handleLinkClick"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import '../styles/highlight.css'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import axios from 'axios'
import { getApiBaseURL } from '../utils/apiConfig'
import { LanguageIcon } from '@heroicons/vue/24/outline'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

// 状态
const currentLang = ref<'zh' | 'en'>('zh')
const helpContent = ref<string>('')
const loading = ref<boolean>(false)
const error = ref<string | null>(null)

// 配置 marked 渲染器，集成 highlight.js
const renderer = new marked.Renderer()

// 辅助函数：确保返回值是字符串
const ensureString = (value: any, fallback: string = ''): string => {
  if (typeof value === 'string') {
    return value
  }
  if (value && typeof value === 'object') {
    // 如果是对象，尝试提取有用的信息
    if ('html' in value && typeof value.html === 'string') {
      return value.html
    }
    if ('value' in value && typeof value.value === 'string') {
      return value.value
    }
    if ('text' in value && typeof value.text === 'string') {
      return value.text
    }
    // 最后尝试 JSON.stringify
    try {
      return JSON.stringify(value)
    } catch {
      return String(value || fallback)
    }
  }
  return String(value || fallback)
}

// 自定义代码块渲染器，使用 highlight.js 进行语法高亮
// @ts-ignore - marked 的类型定义可能不完整
renderer.code = (code: string | any, language: string | undefined | null) => {
  // 确保 code 是字符串类型
  const codeStr = ensureString(code, '')
  let lang: string = ''
  let highlighted: string
  
  // 处理语言参数：去除空白、转小写
  const providedLang = (language && typeof language === 'string') 
    ? language.trim().toLowerCase() 
    : ''
  
  try {
    // 如果提供了语言且 highlight.js 支持，使用提供的语言
    if (providedLang && hljs.getLanguage(providedLang)) {
      const result = hljs.highlight(codeStr, { language: providedLang })
      highlighted = ensureString(result.value, codeStr)
      lang = providedLang
    } else {
      // 自动检测语言
      const result = hljs.highlightAuto(codeStr)
      highlighted = ensureString(result.value, codeStr)
      lang = result.language || 'plaintext'
    }
  } catch (err) {
    // 如果高亮失败，使用 HTML 转义
    console.warn('代码高亮失败:', err)
    highlighted = codeStr
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    lang = providedLang || 'plaintext'
  }
  
  // 生成唯一的 ID 用于复制功能
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

// 配置 marked 选项
marked.setOptions({
  breaks: true, // 支持 GitHub 风格的换行
  gfm: true, // 启用 GitHub 风格的 Markdown
  renderer: renderer,
})

// 计算属性
const titleText = computed(() => {
  return currentLang.value === 'zh' ? '帮助文档' : 'Help'
})

const renderedContent = computed(() => {
  if (!helpContent.value) {
    return ''
  }
  
  // 确保 helpContent.value 是字符串
  let content: string
  if (typeof helpContent.value === 'string') {
    content = helpContent.value
  } else if (helpContent.value && typeof helpContent.value === 'object') {
    // 如果是对象，尝试 JSON.stringify
    console.warn('helpContent.value 是对象:', helpContent.value)
    try {
      content = JSON.stringify(helpContent.value)
    } catch {
      content = String(helpContent.value)
    }
  } else {
    content = String(helpContent.value || '')
  }
  
  if (!content) {
    return ''
  }
  
  try {
    // 使用 marked 将 Markdown 转换为 HTML
    // 代码高亮已经在 renderer.code 中完成，不需要再次处理
    const result = marked.parse(content)
    
    // 确保返回的是字符串
    let html = ensureString(result, '')
    
    // 检查并清理 HTML 中的 [object Object]
    if (html.includes('[object Object]')) {
      console.warn('渲染的 HTML 中包含 [object Object]')
      console.warn('原始内容前500字符:', content.substring(0, 500))
      console.warn('渲染的 HTML 前1000字符:', html.substring(0, 1000))
      // 清理 HTML 中的 [object Object]
      html = html.replace(/\[object Object\]/g, '')
    }
    
    return html
  } catch (err) {
    console.error('Markdown 解析失败:', err)
    return '<p>解析 Markdown 内容时出错</p>'
  }
})

// 切换语言
const toggleLanguage = () => {
  currentLang.value = currentLang.value === 'zh' ? 'en' : 'zh'
  loadHelp()
}

// 加载帮助内容
const loadHelp = async () => {
  loading.value = true
  error.value = null
  
  try {
    // 直接使用 axios 而不是 api 实例，避免拦截器处理 text 响应
    const baseURL = getApiBaseURL()
    const response = await axios.get(`${baseURL}/help/`, {
      params: {
        lang: currentLang.value
      },
      responseType: 'text' // 后端返回的是纯文本 Markdown
    })
    
    // axios 直接返回响应对象，response.data 是字符串
    // 确保 response.data 是字符串类型
    let content = response.data
    if (typeof content !== 'string') {
      console.warn('响应数据类型不是字符串:', typeof content, content)
      // 尝试转换为字符串
      if (content && typeof content === 'object') {
        content = JSON.stringify(content)
      } else {
        content = String(content || '')
      }
    }
    helpContent.value = content
  } catch (err: any) {
    console.error('加载帮助内容失败:', err)
    error.value = err.response?.data?.detail || err.message || '无法加载帮助内容'
    helpContent.value = ''
  } finally {
    loading.value = false
  }
}

// 处理链接点击
const handleLinkClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  
  // 检查是否点击的是复制按钮
  const copyBtn = target.closest('.code-block-copy-btn') as HTMLElement | null
  if (copyBtn) {
    event.preventDefault()
    event.stopPropagation()
    const codeBlockId = copyBtn.getAttribute('data-copy-target')
    if (codeBlockId) {
      copyCodeBlock(codeBlockId, copyBtn)
    }
    return
  }
  
  // 检查是否点击的是链接
  const link = target.closest('a')
  if (!link) {
    return
  }
  
  event.preventDefault()
  
  const href = link.getAttribute('href')
  if (!href) {
    return
  }
  
  // 处理 README 链接（切换语言）
  if (href === 'README.en.md' || href === 'README.md') {
    if (href === 'README.en.md' && currentLang.value !== 'en') {
      toggleLanguage()
    } else if (href === 'README.md' && currentLang.value !== 'zh') {
      toggleLanguage()
    }
    return
  }
  
  // 处理外部链接（http/https）
  if (href.startsWith('http://') || href.startsWith('https://')) {
    window.open(href, '_blank', 'noopener,noreferrer')
    return
  }
  
  // 处理相对路径或文件路径
  // 对于前端，我们只能打开外部链接，本地文件路径无法直接打开
  // 可以尝试作为外部链接打开，或者显示提示
  console.warn('无法打开本地文件路径:', href)
  
  // 尝试作为外部链接打开（如果可能）
  try {
    // 如果是相对路径，尝试构建完整 URL
    if (href.startsWith('/')) {
      // 相对根路径，尝试在当前域名下打开
      window.open(href, '_blank', 'noopener,noreferrer')
    } else {
      // 其他相对路径，尝试在当前域名下打开
      window.open(href, '_blank', 'noopener,noreferrer')
    }
  } catch (err) {
    console.error('打开链接失败:', err)
  }
}

// 复制代码块内容
const copyCodeBlock = async (codeBlockId: string, button: HTMLElement) => {
  const codeElement = document.getElementById(codeBlockId)
  if (!codeElement) {
    return
  }
  
  // 获取代码文本（移除高亮标记）
  const codeText = codeElement.textContent || ''
  
  try {
    await navigator.clipboard.writeText(codeText)
    
    // 显示成功反馈
    const copyIcon = button.querySelector('.copy-icon') as HTMLElement
    const checkIcon = button.querySelector('.check-icon') as HTMLElement
    
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
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement('textarea')
    textArea.value = codeText
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      // 显示成功反馈
      const copyIcon = button.querySelector('.copy-icon') as HTMLElement
      const checkIcon = button.querySelector('.check-icon') as HTMLElement
      if (copyIcon && checkIcon) {
        copyIcon.style.display = 'none'
        checkIcon.style.display = 'block'
        setTimeout(() => {
          copyIcon.style.display = 'block'
          checkIcon.style.display = 'none'
        }, 2000)
      }
    } catch (fallbackErr) {
      console.error('降级复制也失败:', fallbackErr)
    } finally {
      document.body.removeChild(textArea)
    }
  }
}

// 组件挂载时加载帮助内容
onMounted(() => {
  loadHelp()
})

// 监听内容更新，重新绑定复制按钮事件
const setupCopyButtons = () => {
  nextTick(() => {
    const copyButtons = document.querySelectorAll('.code-block-copy-btn')
    copyButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault()
        e.stopPropagation()
        const codeBlockId = btn.getAttribute('data-copy-target')
        if (codeBlockId) {
          copyCodeBlock(codeBlockId, btn as HTMLElement)
        }
      })
    })
  })
}

// 监听 renderedContent 变化，设置复制按钮
watch(renderedContent, () => {
  setupCopyButtons()
}, { immediate: true })
</script>

<style scoped>
/* 确保 Markdown 内容可选中 */
.markdown-container {
  user-select: text;
}

/* VSCode 风格的 Markdown 样式 */

/* 段落 */
.markdown-container :deep(.prose p) {
  margin: 1em 0;
  line-height: 1.6;
}

/* 标题 */
.markdown-container :deep(.prose h1) {
  font-size: 2em;
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid;
}

.markdown-container :deep(.prose h2) {
  font-size: 1.5em;
  font-weight: 600;
  margin-top: 1.3em;
  margin-bottom: 0.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid;
}

.markdown-container :deep(.prose h3) {
  font-size: 1.25em;
  font-weight: 600;
  margin-top: 1.2em;
  margin-bottom: 0.5em;
}

.markdown-container :deep(.prose h4) {
  font-size: 1.1em;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

/* 列表样式 - VSCode 风格 */
.markdown-container :deep(.prose ul),
.markdown-container :deep(.prose ol) {
  margin: 1em 0;
  padding-left: 2em;
}

.markdown-container :deep(.prose li) {
  margin: 0.5em 0;
  line-height: 1.6;
}

.markdown-container :deep(.prose ul li) {
  list-style-type: disc;
}

.markdown-container :deep(.prose ol li) {
  list-style-type: decimal;
}

/* 嵌套列表 */
.markdown-container :deep(.prose ul ul),
.markdown-container :deep(.prose ol ol),
.markdown-container :deep(.prose ul ol),
.markdown-container :deep(.prose ol ul) {
  margin: 0.5em 0;
  padding-left: 2em;
}

.markdown-container :deep(.prose ul ul li) {
  list-style-type: circle;
}

.markdown-container :deep(.prose ul ul ul li) {
  list-style-type: square;
}

/* 代码块包装器样式 */
.markdown-container :deep(.code-block-wrapper) {
  margin: 1.5em 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid;
  border-color: var(--code-border-color, rgba(110, 118, 129, 0.3));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.dark-theme .markdown-container :deep(.code-block-wrapper) {
  border-color: rgba(110, 118, 129, 0.3);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.light-theme .markdown-container :deep(.code-block-wrapper) {
  border-color: rgba(208, 215, 222, 0.8);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 代码块头部 */
.markdown-container :deep(.code-block-header) {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--code-header-bg, rgba(110, 118, 129, 0.1));
  border-bottom: 1px solid;
  border-bottom-color: var(--code-border-color, rgba(110, 118, 129, 0.2));
}

.dark-theme .markdown-container :deep(.code-block-header) {
  background-color: rgba(110, 118, 129, 0.15);
  border-bottom-color: rgba(110, 118, 129, 0.3);
}

.light-theme .markdown-container :deep(.code-block-header) {
  background-color: rgba(208, 215, 222, 0.3);
  border-bottom-color: rgba(208, 215, 222, 0.5);
}

/* 语言标签 */
.markdown-container :deep(.code-block-language) {
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--code-lang-color, rgba(110, 118, 129, 0.8));
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.dark-theme .markdown-container :deep(.code-block-language) {
  color: rgba(139, 148, 158, 0.9);
}

.light-theme .markdown-container :deep(.code-block-language) {
  color: rgba(101, 109, 118, 0.9);
}

/* 复制按钮 */
.markdown-container :deep(.code-block-copy-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  background: transparent;
  border: 1px solid;
  border-color: var(--code-border-color, rgba(110, 118, 129, 0.3));
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--code-lang-color, rgba(110, 118, 129, 0.8));
}

.markdown-container :deep(.code-block-copy-btn:hover) {
  background-color: var(--code-btn-hover-bg, rgba(110, 118, 129, 0.1));
  border-color: var(--code-border-color, rgba(110, 118, 129, 0.5));
}

.dark-theme .markdown-container :deep(.code-block-copy-btn:hover) {
  background-color: rgba(110, 118, 129, 0.2);
  border-color: rgba(110, 118, 129, 0.5);
}

.light-theme .markdown-container :deep(.code-block-copy-btn:hover) {
  background-color: rgba(208, 215, 222, 0.4);
  border-color: rgba(208, 215, 222, 0.8);
}

.markdown-container :deep(.code-block-copy-btn:active) {
  transform: scale(0.95);
}

.markdown-container :deep(.code-block-copy-btn svg) {
  width: 16px;
  height: 16px;
}

.markdown-container :deep(.code-block-copy-btn .check-icon) {
  color: #58a6ff;
}

.light-theme .markdown-container :deep(.code-block-copy-btn .check-icon) {
  color: #0969da;
}

/* 代码块样式 - VSCode 风格 */
.markdown-container :deep(.code-block-wrapper pre.hljs) {
  background-color: var(--code-bg-color);
  border-radius: 0;
  padding: 16px;
  overflow-x: auto;
  margin: 0;
  line-height: 1.45;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  border: none;
}

.markdown-container :deep(.code-block-wrapper pre.hljs code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
  color: inherit;
  display: block;
  overflow-x: auto;
}

/* pre 标签样式（没有包装器的代码块） */
.markdown-container :deep(.prose pre:not(.hljs)) {
  background-color: var(--code-bg-color);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 1em 0;
  line-height: 1.45;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  border: 1px solid;
  border-color: var(--code-border-color, rgba(110, 118, 129, 0.3));
}

.markdown-container :deep(.prose pre:not(.hljs) code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
  color: inherit;
  display: block;
  overflow-x: auto;
}

/* 行内代码 */
.markdown-container :deep(.prose code:not(pre code)) {
  background-color: var(--inline-code-bg);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: var(--inline-code-color);
}

/* 链接样式 */
.markdown-container :deep(.prose a) {
  color: var(--link-color);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-container :deep(.prose a:hover) {
  opacity: 0.8;
}

/* 表格样式 */
.markdown-container :deep(.prose table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  display: block;
  overflow-x: auto;
}

.markdown-container :deep(.prose thead) {
  background-color: var(--table-header-bg);
}

.markdown-container :deep(.prose table th),
.markdown-container :deep(.prose table td) {
  padding: 0.6em 1em;
  border: 1px solid var(--table-border-color);
  text-align: left;
}

.markdown-container :deep(.prose table th) {
  font-weight: 600;
}

/* 引用块样式 */
.markdown-container :deep(.prose blockquote) {
  border-left: 4px solid var(--blockquote-border);
  padding-left: 1em;
  margin: 1em 0;
  padding-right: 1em;
  color: var(--blockquote-color);
  background-color: var(--blockquote-bg);
}

/* 水平分割线 */
.markdown-container :deep(.prose hr) {
  border: none;
  border-top: 1px solid var(--hr-color);
  margin: 2em 0;
}

/* 图片样式 */
.markdown-container :deep(.prose img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 1em 0;
}

/* 强调 */
.markdown-container :deep(.prose strong) {
  font-weight: 600;
}

.markdown-container :deep(.prose em) {
  font-style: italic;
}

/* 深色主题变量 */
.markdown-container.dark-theme {
  --code-bg-color: #1e1e1e;
  --inline-code-bg: rgba(110, 118, 129, 0.4);
  --inline-code-color: #c9d1d9;
  --link-color: #58a6ff;
  --table-header-bg: rgba(110, 118, 129, 0.1);
  --table-border-color: rgba(110, 118, 129, 0.2);
  --blockquote-border: #58a6ff;
  --blockquote-color: #c9d1d9;
  --blockquote-bg: rgba(88, 166, 255, 0.1);
  --hr-color: rgba(110, 118, 129, 0.2);
  --code-border-color: rgba(110, 118, 129, 0.3);
  --code-header-bg: rgba(110, 118, 129, 0.15);
  --code-lang-color: rgba(139, 148, 158, 0.9);
  --code-btn-hover-bg: rgba(110, 118, 129, 0.2);
}

/* 浅色主题变量 */
.markdown-container.light-theme {
  --code-bg-color: #f6f8fa;
  --inline-code-bg: rgba(175, 184, 193, 0.2);
  --inline-code-color: #24292f;
  --link-color: #0969da;
  --table-header-bg: rgba(208, 215, 222, 0.5);
  --table-border-color: #d0d7de;
  --blockquote-border: #0969da;
  --blockquote-color: #57606a;
  --blockquote-bg: rgba(9, 105, 218, 0.1);
  --hr-color: #d0d7de;
  --code-border-color: rgba(208, 215, 222, 0.8);
  --code-header-bg: rgba(208, 215, 222, 0.3);
  --code-lang-color: rgba(101, 109, 118, 0.9);
  --code-btn-hover-bg: rgba(208, 215, 222, 0.4);
}

</style>
