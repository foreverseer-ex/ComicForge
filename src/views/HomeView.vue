<template>
  <div class="space-y-6">
    <!-- 顶部：项目选择器和操作按钮 -->
    <div 
      :class="[
        'flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b',
        isDark ? 'border-gray-700' : 'border-gray-200'
      ]"
    >
      <!-- 第一行：标题 -->
      <div class="flex items-center gap-4">
        <HomeIcon class="w-6 h-6" :class="isDark ? 'text-gray-400' : 'text-gray-600'" />
        <h2 :class="['text-xl font-bold', isDark ? 'text-white' : 'text-gray-900']">
          项目管理
        </h2>
      </div>

      <!-- 第二行：项目选择下拉框 -->
      <select
        :value="selectedProjectId"
        @change="(e) => { projectStore.setSelectedProjectId((e.target as HTMLSelectElement).value); onProjectChange() }"
        :class="[
          'px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
          'w-full md:flex-1 md:max-w-md',
          isDark
            ? 'bg-gray-800 border-gray-700 text-white'
            : 'bg-white border-gray-300 text-gray-900'
        ]"
      >
        <option value="" disabled>请选择一个项目</option>
        <option 
          v-for="project in projects" 
          :key="project.project_id" 
          :value="project.project_id"
        >
          {{ project.title }}
        </option>
      </select>

      <!-- 第三行：操作按钮 -->
      <div class="flex items-center gap-2">
        <button
          @click="showProjectDialog = true; editingProject = null"
          :class="[
            'p-2 rounded-lg transition-colors',
            isDark
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          ]"
          title="创建项目"
        >
          <PlusIcon class="w-5 h-5" />
        </button>
        <button
          @click="confirmDelete"
          :disabled="!selectedProjectId"
          :class="[
            'p-2 rounded-lg transition-colors',
            selectedProjectId
              ? isDark
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
              : isDark
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          ]"
          title="删除项目"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && projects.length === 0" 
         @click="showProjectDialog = true; editingProject = null"
         :class="[
           'flex flex-col items-center justify-center py-20 rounded-lg cursor-pointer transition-all',
           isDark 
             ? 'bg-gray-800 border border-gray-700 hover:bg-gray-700 hover:border-gray-600' 
             : 'bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
         ]">
      <FolderOpenIcon class="w-24 h-24 mb-4 transition-transform hover:scale-110" 
                      :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
      <h3 :class="['text-xl font-semibold mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
        你还没有创建项目
      </h3>
      <p :class="['text-sm mb-2', isDark ? 'text-gray-400' : 'text-gray-500']">
        点击此处创建你的第一个项目
      </p>
      <p :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
        或点击上方的「+」按钮
      </p>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2" 
           :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
    </div>

    <!-- 主内容区域：卡片布局 -->
    <div v-else-if="selectedProject && currentProject" class="space-y-6">
      <!-- 响应式布局：正常情况下两列，空间不够时一列 -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- 左侧：项目信息卡片 -->
        <div 
          :class="[
            'rounded-lg border p-6',
            isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          ]"
        >
          <div class="flex items-center justify-between mb-4">
            <h3 :class="['text-lg font-semibold', isDark ? 'text-white' : 'text-gray-900']">
              项目信息
            </h3>
            <button
              @click="editProject"
              :class="[
                'p-1 rounded transition-colors',
                isDark 
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
              ]"
              title="编辑项目"
            >
              <PencilIcon class="w-5 h-5" />
            </button>
          </div>

          <div class="space-y-3">
            <div>
              <label :class="['text-sm font-medium', isDark ? 'text-gray-400' : 'text-gray-500']">
                项目标题
              </label>
              <p :class="['mt-1', isDark ? 'text-white' : 'text-gray-900']">
                {{ currentProject.title }}
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="['text-sm font-medium', isDark ? 'text-gray-400' : 'text-gray-500']">
                  总章节
                </label>
                <p :class="['mt-1', isDark ? 'text-white' : 'text-gray-900']">
                  {{ currentProject.total_chapters || 0 }}
                </p>
              </div>
              <div>
                <label :class="['text-sm font-medium', isDark ? 'text-gray-400' : 'text-gray-500']">
                  总行数
                </label>
                <p :class="['mt-1', isDark ? 'text-white' : 'text-gray-900']">
                  {{ currentProject.total_lines || 0 }}
                </p>
              </div>
            </div>

            <!-- 进度信息 -->
            <div v-if="currentProject.total_lines > 0">
              <div class="flex justify-between text-sm mb-2" :class="isDark ? 'text-gray-400' : 'text-gray-600'">
                <span>处理进度</span>
                <span>{{ Math.round((currentProject.current_line / currentProject.total_lines) * 100) }}%</span>
              </div>
              <div 
                :class="[
                  'h-2 rounded-full overflow-hidden',
                  isDark ? 'bg-gray-700' : 'bg-gray-200'
                ]"
              >
                <div 
                  class="h-full bg-blue-600 transition-all duration-300"
                  :style="{ width: `${(currentProject.current_line / currentProject.total_lines) * 100}%` }"
                ></div>
              </div>
              <div class="text-xs mt-1" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                当前：第 {{ currentProject.current_chapter + 1 }} 章，第 {{ currentProject.current_line + 1 }} 行
              </div>
            </div>

            <div class="text-xs pt-3 border-t" :class="isDark ? 'border-gray-700 text-gray-500' : 'border-gray-200 text-gray-400'">
              创建于 {{ formatDate(currentProject.created_at) }}
            </div>
          </div>
        </div>

        <!-- 右侧：上下两个卡片 -->
        <div class="xl:col-span-2 space-y-6">
          <!-- 上方：当前段落卡片 -->
          <div 
            :class="[
              'rounded-lg border p-6',
              isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            ]"
          >
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
              <h3 :class="['text-lg font-semibold', isDark ? 'text-white' : 'text-gray-900']">
                当前段落
              </h3>
              <div class="flex items-center gap-2">
                <button
                  @click="prevParagraph"
                  :disabled="!canGoPrev || loadingParagraph"
                  :class="[
                    'p-2 rounded transition-colors',
                    canGoPrev && !loadingParagraph
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  ]"
                  title="上一段"
                >
                  <ChevronLeftIcon class="w-5 h-5" />
                </button>
                
                <!-- 当前段落位置显示 -->
                <div class="flex items-center gap-2">
                  <span 
                    v-if="currentParagraph"
                    @click="showJumpDialog = true"
                    class="text-sm px-3 py-1 rounded cursor-pointer transition-colors"
                    :class="isDark 
                      ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-700' 
                      : 'text-gray-600 hover:text-gray-700 hover:bg-gray-100'"
                    title="点击跳转"
                  >
                    第 {{ currentParagraph.chapter + 1 }} 章，第 {{ currentParagraph.line + 1 }} 行
                  </span>
                  <span 
                    v-else
                    class="text-sm px-3 text-gray-500"
                  >
                    无段落
                  </span>
                </div>
                
                <button
                  @click="nextParagraph"
                  :disabled="!canGoNext || loadingParagraph"
                  :class="[
                    'p-2 rounded transition-colors',
                    canGoNext && !loadingParagraph
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  ]"
                  title="下一段"
                >
                  <ChevronRightIcon class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- 加载状态：不隐藏现有内容，只在顶部显示加载指示器 -->
            <div v-if="loadingParagraph" class="flex justify-center py-2 mb-2">
              <div class="animate-spin rounded-full h-5 w-5 border-b-2" 
                   :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
            </div>
            <div v-if="currentParagraph" 
                 :class="[
                   'prose max-w-none',
                   isDark ? 'text-gray-300' : 'text-gray-700',
                   loadingParagraph ? 'opacity-50' : ''
                 ]"
            >
              <p class="whitespace-pre-wrap">{{ currentParagraph.content }}</p>
            </div>
            <div v-else-if="!loadingParagraph" 
                 :class="[
                   'text-center py-8 text-sm',
                   isDark ? 'text-gray-500' : 'text-gray-400'
                 ]"
            >
              暂无段落内容
            </div>
          </div>

          <!-- 下方：当前图片卡片 -->
          <div 
            :class="[
              'rounded-lg border p-6',
              isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            ]"
          >
            <h3 :class="['text-lg font-semibold mb-4', isDark ? 'text-white' : 'text-gray-900']">
              当前图片
            </h3>

            <div 
              :class="[
                'flex flex-col items-center justify-center py-12 text-center',
                isDark ? 'text-gray-500' : 'text-gray-400'
              ]"
            >
              <PhotoIcon class="w-16 h-16 mb-2 opacity-50" />
              <p class="text-sm">功能尚未实现</p>
              <p class="text-xs mt-1 opacity-75">当前图片功能开发中...</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 项目对话框（创建/编辑） -->
    <div
      v-if="showProjectDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showProjectDialog = false"
    >
      <div
        @click.stop
        :class="[
          'w-full max-w-md rounded-lg shadow-xl',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <div class="p-6">
          <h2 :class="['text-xl font-bold mb-4', isDark ? 'text-white' : 'text-gray-900']">
            {{ editingProject ? '编辑项目' : '创建新项目' }}
          </h2>
          <div class="space-y-4">
            <div>
              <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                项目标题 *
              </label>
              <input
                v-model="projectForm.title"
                type="text"
                placeholder="请输入项目标题"
                :class="[
                  'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2',
                  isDark
                    ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
                ]"
                @keyup.enter="saveProject"
              />
            </div>
            <div>
              <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                小说文件（可选）
              </label>
              <!-- 文件选择器 -->
              <div
                :class="[
                  'border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer',
                  isDragging
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : isDark
                      ? 'border-gray-600 hover:border-gray-500 bg-gray-700/50'
                      : 'border-gray-300 hover:border-gray-400 bg-gray-50'
                ]"
                @drop.prevent="handleDrop"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInputRef"
                  type="file"
                  accept=".txt,.pdf,.doc,.docx,.md"
                  class="hidden"
                  @change="handleFileSelect"
                />
                <div class="text-center">
                  <svg
                    class="mx-auto h-12 w-12 mb-3"
                    :class="isDark ? 'text-gray-500' : 'text-gray-400'"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                    aria-hidden="true"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <p :class="['text-sm mb-1', isDark ? 'text-gray-300' : 'text-gray-600']">
                    <span class="font-semibold">点击选择文件</span>
                    或拖拽文件到此处
                  </p>
                  <p :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-500']">
                    支持格式: TXT, PDF, DOC, DOCX, MD
                  </p>
                  <div
                    v-if="selectedFileName"
                    class="flex items-center justify-center gap-2 mt-2"
                  >
                    <p :class="['text-sm font-medium', isDark ? 'text-blue-400' : 'text-blue-600']">
                      已选择: {{ selectedFileName }}
                    </p>
                    <button
                      v-if="!editingProject"
                      @click.stop="clearFile"
                      :class="[
                        'p-1 rounded hover:bg-opacity-20',
                        isDark ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-600' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200'
                      ]"
                      title="清除文件"
                    >
                      <XMarkIcon class="w-4 h-4" />
                    </button>
                  </div>
                  <div
                    v-if="isUploading"
                    class="mt-2"
                  >
                    <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                      正在上传...
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button
              @click="showProjectDialog = false"
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
              @click="saveProject"
              :disabled="!projectForm.title.trim()"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                projectForm.title.trim()
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : isDark
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              ]"
            >
              {{ editingProject ? '保存' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 跳转对话框 -->
    <div
      v-if="showJumpDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showJumpDialog = false"
    >
      <div
        @click.stop
        :class="[
          'w-full max-w-md rounded-lg shadow-xl',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
        @keydown="handleJumpDialogKeydown"
        tabindex="0"
      >
        <div class="p-6">
          <h2 :class="['text-xl font-bold mb-4', isDark ? 'text-white' : 'text-gray-900']">
            跳转到指定位置
          </h2>
          <div class="space-y-4">
            <!-- 当前位置 -->
            <div v-if="currentParagraph">
              <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                当前位置
              </label>
              <p :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                第 {{ currentParagraph.chapter + 1 }} 章，第 {{ currentParagraph.line + 1 }} 行
              </p>
            </div>
            
            <!-- 跳转输入 -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                  章节号 *
                </label>
                <div class="flex items-center gap-2">
                  <button
                    @click="adjustChapter(-1)"
                    :disabled="!jumpChapter || jumpChapter <= 1"
                    :class="[
                      'p-1 rounded transition-colors',
                      jumpChapter && jumpChapter > 1
                        ? isDark
                          ? 'bg-gray-700 hover:bg-gray-600 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                        : isDark
                          ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    ]"
                    title="减少章节（左箭头键）"
                  >
                    <ChevronLeftIcon class="w-4 h-4" />
                  </button>
                  <input
                    ref="jumpChapterInputRef"
                    v-model.number="jumpChapter"
                    type="number"
                    min="1"
                    :max="currentProject ? currentProject.total_chapters : 1"
                    placeholder="章"
                    :class="[
                      'flex-1 px-3 py-2 text-center rounded border focus:outline-none focus:ring-2',
                      isDark
                        ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                        : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
                    ]"
                    @keyup.enter="jumpToPosition"
                  />
                  <button
                    @click="adjustChapter(1)"
                    :disabled="!jumpChapter || !currentProject || jumpChapter >= currentProject.total_chapters"
                    :class="[
                      'p-1 rounded transition-colors',
                      jumpChapter && currentProject && jumpChapter < currentProject.total_chapters
                        ? isDark
                          ? 'bg-gray-700 hover:bg-gray-600 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                        : isDark
                          ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    ]"
                    title="增加章节（右箭头键）"
                  >
                    <ChevronRightIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <div>
                <label :class="['block text-sm font-medium mb-2', isDark ? 'text-gray-300' : 'text-gray-700']">
                  行号 *
                </label>
                <input
                  ref="jumpLineInputRef"
                  v-model.number="jumpLine"
                  type="number"
                  min="1"
                  :max="currentProject ? currentProject.total_lines : 1"
                  placeholder="行"
                  :class="[
                    'w-full px-3 py-2 text-center rounded border focus:outline-none focus:ring-2',
                    isDark
                      ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                      : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
                  ]"
                  @keyup.enter="jumpToPosition"
                />
              </div>
            </div>
            
            <!-- 最大范围提示 -->
            <div v-if="currentProject">
              <p :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
                最大范围: {{ currentProject.total_chapters }} 章 / {{ currentProject.total_lines }} 行
              </p>
            </div>
            
            <!-- 快捷键提示 -->
            <div>
              <p :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-400']">
                快捷键: ← 减少章节 | → 增加章节 | Enter 跳转 | Esc 取消
              </p>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button
              @click="showJumpDialog = false"
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
              @click="jumpToPosition"
              :disabled="!jumpChapter || !jumpLine || loadingParagraph"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                jumpChapter && jumpLine && !loadingParagraph
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : isDark
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              ]"
            >
              {{ loadingParagraph ? '跳转中...' : '跳转' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div
      v-if="projectToDelete"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="projectToDelete = null"
    >
      <div
        @click.stop
        :class="[
          'w-full max-w-md rounded-lg shadow-xl',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <div class="p-6">
          <h2 :class="['text-xl font-bold mb-4 text-red-600']">
            确认删除项目
          </h2>
          <p :class="['mb-6', isDark ? 'text-gray-300' : 'text-gray-700']">
            确定要删除项目 <strong>{{ projectToDelete.title }}</strong> 吗？
            <br />
            <span class="text-sm text-red-600">此操作不可恢复，将删除项目的所有相关数据。</span>
          </p>
          <div class="flex justify-end gap-3">
            <button
              @click="projectToDelete = null"
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
              @click="deleteProject"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white'
              ]"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useProjectStore } from '../stores/project'
import { storeToRefs } from 'pinia'
import api from '../api'
import {
  HomeIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PhotoIcon,
  FolderOpenIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

interface Project {
  project_id: string
  title: string
  total_lines: number
  total_chapters: number
  current_line: number
  current_chapter: number
  novel_path?: string
  project_path: string
  created_at: string
  updated_at: string
}

interface NovelContent {
  project_id: string
  chapter: number
  line: number
  content: string
}

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()
const { 
  selectedProjectId, 
  projects, 
  currentProject
} = storeToRefs(projectStore)

const loading = ref(false)
const loadingParagraph = ref(false)
const currentParagraph = ref<NovelContent | null>(null)
const currentImageUrl = ref<string | null>(null)

const showProjectDialog = ref(false)
const editingProject = ref<Project | null>(null)
const projectToDelete = ref<Project | null>(null)

const projectForm = ref({
  title: '',
  novel_path: ''
})

const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFileName = ref<string>('')
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)

const jumpChapter = ref<number | null>(null)
const jumpLine = ref<number | null>(null)
const showJumpDialog = ref(false)
const jumpChapterInputRef = ref<HTMLInputElement | null>(null)
const jumpLineInputRef = ref<HTMLInputElement | null>(null)

// 计算属性（使用 store 中的 selectedProject）
const selectedProject = computed(() => {
  return projectStore.selectedProject
})

const canGoPrev = computed(() => {
  if (!currentProject.value || !currentParagraph.value) return false
  return currentProject.value.current_line > 0 || currentProject.value.current_chapter > 0
})

const canGoNext = computed(() => {
  if (!currentProject.value || !currentParagraph.value) return false
  return currentProject.value.current_line < currentProject.value.total_lines - 1 ||
         currentProject.value.current_chapter < currentProject.value.total_chapters - 1
})

// 加载项目列表（使用 store）
const loadProjects = async () => {
  loading.value = true
  try {
    await projectStore.loadProjects()
  } catch (error) {
    console.error('加载项目列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载当前项目详情（使用 store）
const loadCurrentProject = async () => {
  if (!selectedProjectId.value) {
    return
  }

  try {
    await projectStore.loadCurrentProject()
    
    // 加载当前段落和图片
    await loadCurrentParagraph()
  } catch (error) {
    console.error('加载项目详情失败:', error)
  }
}

// 加载当前段落
const loadCurrentParagraph = async () => {
  if (!currentProject.value) {
    currentParagraph.value = null
    currentImageUrl.value = null
    return
  }

  // 不立即设置 loading，避免频闪
  // 延迟一小段时间再显示加载状态（如果加载很快就不会显示）
  const loadingTimeout = setTimeout(() => {
    loadingParagraph.value = true
  }, 100) // 100ms 后才显示加载状态

  try {
    const chapter = currentProject.value.current_chapter
    const line = currentProject.value.current_line
    
    // 获取当前段落内容
    try {
      const content = await api.get('/context/line', {
        params: {
          project_id: currentProject.value.project_id,
          chapter,
          line
        }
      })
      const contentData = (content as any)?.data || content
      // 立即更新内容，不等待图片加载
      currentParagraph.value = contentData
      
      // 暂时禁用图片加载功能（功能尚未实现）
      // TODO: 实现当前图片功能
      currentImageUrl.value = null
    } catch (error: any) {
      // 如果段落不存在，清空显示
      if (error.response?.status === 404) {
        currentParagraph.value = null
        currentImageUrl.value = null
      } else {
        console.error('加载段落失败:', error)
      }
    }
  } catch (error) {
    console.error('加载段落失败:', error)
  } finally {
    clearTimeout(loadingTimeout)
    loadingParagraph.value = false
  }
}

// 切换到上一段
const prevParagraph = async () => {
  if (!currentProject.value || !canGoPrev.value || loadingParagraph.value) return

  try {
    let newChapter = currentProject.value.current_chapter
    let newLine = currentProject.value.current_line - 1

    if (newLine < 0 && newChapter > 0) {
      newChapter -= 1
      // 获取上一章的所有行，取最后一行的行号
      try {
        const response = await api.get('/context/lines', {
          params: {
            project_id: currentProject.value.project_id,
            chapter: newChapter
          }
        })
        const chapterLines = (response as any)?.data || response
        if (Array.isArray(chapterLines) && chapterLines.length > 0) {
          newLine = chapterLines[chapterLines.length - 1].line
        } else {
          newLine = 0
        }
      } catch (error) {
        console.error('获取上一章行数失败:', error)
        newLine = 0
      }
    }

    if (newLine >= 0 && newChapter >= 0) {
      // 更新项目进度
      await api.put(`/project/${currentProject.value.project_id}`, null, {
        params: {
          current_line: newLine,
          current_chapter: newChapter
        }
      })
      
      // 重新加载项目信息和段落
      await loadCurrentProject()
    }
  } catch (error) {
    console.error('切换到上一段失败:', error)
  }
}

// 切换到下一段
const nextParagraph = async () => {
  if (!currentProject.value || !canGoNext.value || loadingParagraph.value) return

  try {
    let newChapter = currentProject.value.current_chapter
    let newLine = currentProject.value.current_line + 1

    // 检查是否超出当前章节
    try {
      const response = await api.get('/context/lines', {
        params: {
          project_id: currentProject.value.project_id,
          chapter: newChapter
        }
      })
      const chapterLines = (response as any)?.data || response
      if (Array.isArray(chapterLines) && chapterLines.length > 0) {
        const maxLine = chapterLines[chapterLines.length - 1].line
        if (newLine > maxLine && newChapter < currentProject.value.total_chapters - 1) {
          newChapter += 1
          newLine = 0
        } else if (newLine > maxLine) {
          // 已经是最后一章的最后一行，不更新
          return
        }
      } else if (newChapter < currentProject.value.total_chapters - 1) {
        // 当前章节没有内容，切换到下一章
        newChapter += 1
        newLine = 0
      } else {
        // 已经是最后一章，不更新
        return
      }
    } catch (error) {
      console.error('检查章节行数失败:', error)
      // 如果查询失败，尝试直接更新（可能章节不存在）
    }

    // 更新项目进度
    await api.put(`/project/${currentProject.value.project_id}`, null, {
      params: {
        current_line: newLine,
        current_chapter: newChapter
      }
    })
    
    // 重新加载项目信息和段落
    await loadCurrentProject()
  } catch (error) {
    console.error('切换到下一段失败:', error)
  }
}

// 调整章节（用于快捷键和按钮）
const adjustChapter = (delta: number) => {
  if (!jumpChapter.value || !currentProject.value) return
  
  const newChapter = jumpChapter.value + delta
  if (newChapter >= 1 && newChapter <= currentProject.value.total_chapters) {
    jumpChapter.value = newChapter
  }
}

// 处理跳转对话框的键盘事件
const handleJumpDialogKeydown = (event: KeyboardEvent) => {
  // 只在输入框没有焦点时处理快捷键
  const activeElement = document.activeElement
  const isInputFocused = activeElement === jumpChapterInputRef.value || 
                         activeElement === jumpLineInputRef.value ||
                         activeElement?.tagName === 'INPUT'
  
  if (isInputFocused) {
    // 如果输入框有焦点，只在特定情况下处理
    if (event.key === 'ArrowLeft' && activeElement === jumpChapterInputRef.value) {
      event.preventDefault()
      adjustChapter(-1)
    } else if (event.key === 'ArrowRight' && activeElement === jumpChapterInputRef.value) {
      event.preventDefault()
      adjustChapter(1)
    } else if (event.key === 'Escape') {
      showJumpDialog.value = false
    }
    return
  }
  
  // 如果输入框没有焦点，处理快捷键
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      adjustChapter(-1)
      break
    case 'ArrowRight':
      event.preventDefault()
      adjustChapter(1)
      break
    case 'Escape':
      event.preventDefault()
      showJumpDialog.value = false
      break
    case 'Enter':
      event.preventDefault()
      jumpToPosition()
      break
  }
}

// 监听对话框显示，初始化输入值
watch(showJumpDialog, (newVal) => {
  if (newVal && currentParagraph.value) {
    // 初始化输入值为当前值（转换为1-based）
    jumpChapter.value = currentParagraph.value.chapter + 1
    jumpLine.value = currentParagraph.value.line + 1
    
    // 聚焦到章节输入框
    nextTick(() => {
      jumpChapterInputRef.value?.focus()
      jumpChapterInputRef.value?.select()
    })
  } else {
    // 关闭对话框时清空
    jumpChapter.value = null
    jumpLine.value = null
  }
})

// 手动跳转到指定位置
const jumpToPosition = async () => {
  if (!currentProject.value || loadingParagraph.value) return
  
  // 验证输入
  if (jumpChapter.value === null || jumpLine.value === null) {
    alert('请输入章节和行号')
    return
  }
  
  // 转换为0-based索引
  const targetChapter = jumpChapter.value - 1
  const targetLine = jumpLine.value - 1
  
  // 验证范围
  if (targetChapter < 0 || targetChapter >= currentProject.value.total_chapters) {
    alert(`章节号必须在 1-${currentProject.value.total_chapters} 之间`)
    return
  }
  
  if (targetLine < 0 || targetLine >= currentProject.value.total_lines) {
    alert(`行号必须在 1-${currentProject.value.total_lines} 之间`)
    return
  }
  
  try {
    // 更新项目进度
    await api.put(`/project/${currentProject.value.project_id}`, null, {
      params: {
        current_line: targetLine,
        current_chapter: targetChapter
      }
    })
    
    // 关闭对话框
    showJumpDialog.value = false
    
    // 重新加载项目信息和段落
    await loadCurrentProject()
  } catch (error: any) {
    console.error('跳转失败:', error)
    const message = error.response?.data?.detail || error.message || '跳转失败'
    alert(message)
  }
}

// 图片加载错误处理（未使用，保留以备将来使用）
// @ts-expect-error - 未使用的函数，保留以备将来使用
const _handleImageError = () => {
  currentImageUrl.value = null
}

// 项目选择变化（使用 store）
const onProjectChange = () => {
  // 关闭跳转对话框
  showJumpDialog.value = false
  if (selectedProjectId.value) {
    projectStore.setSelectedProjectId(selectedProjectId.value)
  }
  loadCurrentProject()
}

// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

// 处理拖拽
const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    processFile(file)
  }
}

// 处理文件（验证和上传）
const processFile = async (file: File) => {
  // 验证文件类型
  const allowedExtensions = ['.txt', '.pdf', '.doc', '.docx', '.md']
  const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
  
  if (!allowedExtensions.includes(fileExt)) {
    alert(`不支持的文件格式: ${fileExt}。支持格式: ${allowedExtensions.join(', ')}`)
    return
  }
  
  // 验证文件大小（限制为100MB）
  const maxSize = 100 * 1024 * 1024
  if (file.size > maxSize) {
    alert('文件大小不能超过100MB')
    return
  }
  
  selectedFile.value = file
  selectedFileName.value = file.name
  
  // 如果项目标题为空，从文件名自动解析
  if (!projectForm.value.title.trim()) {
    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '')
    projectForm.value.title = nameWithoutExt
  }
  
  // 上传文件
  await uploadFile(file)
}

// 上传文件到后端
const uploadFile = async (file: File) => {
  isUploading.value = true
  try {
    // 创建 FormData
    const formData = new FormData()
    formData.append('file', file)
    
    // 上传文件到后端（FormData 会自动设置正确的 Content-Type）
    const response = await api.post('/file/upload', formData)
    const responseData = (response as any)?.data || response
    
    // 保存文件路径到表单
    if (responseData?.file_path) {
      projectForm.value.novel_path = responseData.file_path
      console.log('文件上传成功:', responseData.file_path)
    } else {
      throw new Error('服务器未返回文件路径')
    }
  } catch (error: any) {
    console.error('文件上传失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '文件上传失败，请检查文件是否有效'
    alert(errorMessage)
    projectForm.value.novel_path = ''
    selectedFile.value = null
    selectedFileName.value = ''
  } finally {
    isUploading.value = false
  }
}

// 清除文件选择
const clearFile = () => {
  selectedFile.value = null
  selectedFileName.value = ''
  projectForm.value.novel_path = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// 编辑项目
const editProject = () => {
  if (!currentProject.value) return
  editingProject.value = currentProject.value
  projectForm.value = {
    title: currentProject.value.title,
    novel_path: currentProject.value.novel_path || ''
  }
  // 如果有文件路径，显示文件名
  if (currentProject.value.novel_path) {
    const pathParts = currentProject.value.novel_path.split(/[/\\]/)
    selectedFileName.value = pathParts[pathParts.length - 1] || ''
  } else {
    selectedFileName.value = ''
  }
  selectedFile.value = null
  showProjectDialog.value = true
}

// 保存项目（创建或更新）
const saveProject = async () => {
  if (!projectForm.value.title.trim()) return

  try {
    if (editingProject.value) {
      // 更新项目
      const updateData: any = {
        title: projectForm.value.title.trim()
      }
      await api.put(`/project/${editingProject.value.project_id}`, null, { params: updateData })
    } else {
      // 创建项目
      const params: any = {
        title: projectForm.value.title.trim()
      }
      if (projectForm.value.novel_path.trim()) {
        params.novel_path = projectForm.value.novel_path.trim()
      }

      const response = await api.post('/project/create', null, { params })
      // 后端直接返回 project_id 字符串，不是字典
      const projectId = (response as any)?.data || response
      if (typeof projectId === 'string') {
        selectedProjectId.value = projectId
      } else if (projectId?.project_id) {
        // 兼容旧格式（字典）
        selectedProjectId.value = projectId.project_id
      } else {
        throw new Error('创建项目失败：未返回 project_id')
      }
    }
    
    // 重置表单
    projectForm.value = { title: '', novel_path: '' }
    selectedFile.value = null
    selectedFileName.value = ''
    isDragging.value = false
    isUploading.value = false
    editingProject.value = null
    showProjectDialog.value = false
    
    // 重新加载列表和当前项目
    await loadProjects()
    await loadCurrentProject()
  } catch (error: any) {
    console.error('保存项目失败:', error)
    const message = error.response?.data?.detail || error.message || '保存项目失败'
    alert(message)
  }
}

// 确认删除
const confirmDelete = () => {
  if (!selectedProject.value) return
  projectToDelete.value = selectedProject.value
}

// 删除项目
const deleteProject = async () => {
  if (!projectToDelete.value) return

  const projectId = projectToDelete.value.project_id
  
  try {
    await api.delete(`/project/${projectId}`)
    
    projectToDelete.value = null
    
    // 如果删除的是当前选中的项目，清除选中状态
    if (selectedProjectId.value === projectId) {
      projectStore.setSelectedProjectId('')
      currentParagraph.value = null
      currentImageUrl.value = null
    }
    
    // 重新加载列表
    await loadProjects()
    
    // 如果还有项目，选中第一个
    if (projectStore.projects.length > 0 && projectStore.projects[0]) {
      projectStore.setSelectedProjectId(projectStore.projects[0].project_id)
      await loadCurrentProject()
    } else {
      projectStore.setSelectedProjectId('')
    }
  } catch (error: any) {
    console.error('删除项目失败:', error)
    const message = error.response?.data?.detail || error.message || '删除项目失败'
    alert(message)
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 监听选中项目变化（使用 store）
watch(() => selectedProjectId.value, (newId) => {
  if (newId) {
    loadCurrentProject()
  } else {
    currentParagraph.value = null
    currentImageUrl.value = null
  }
})

// 全局键盘事件处理函数（需要在 setup 顶层定义，以便在 onUnmounted 中访问）
const handleDocumentKeydown = (event: KeyboardEvent) => {
  // 如果焦点在输入框、文本区域或对话框上，不处理
  const activeElement = document.activeElement
  const tagName = activeElement?.tagName.toLowerCase()
  const isInputFocused = tagName === 'input' || 
                         tagName === 'textarea' ||
                         activeElement?.getAttribute('contenteditable') === 'true'
  
  // 如果对话框打开，也不处理
  if (showJumpDialog.value || showProjectDialog.value || projectToDelete.value) {
    return
  }
  
  // 如果焦点在输入框，不处理
  if (isInputFocused) {
    return
  }
  
  // 处理左右箭头键
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      event.stopPropagation()
      if (canGoPrev.value && !loadingParagraph.value) {
        prevParagraph()
      }
      break
    case 'ArrowRight':
      event.preventDefault()
      event.stopPropagation()
      if (canGoNext.value && !loadingParagraph.value) {
        nextParagraph()
      }
      break
  }
}

// 初始化
onMounted(async () => {
  await loadProjects()
  if (selectedProjectId.value) {
    await loadCurrentProject()
  }
  
  // 添加全局事件监听
  document.addEventListener('keydown', handleDocumentKeydown)
})

// 组件卸载时移除监听（必须在 setup 顶层调用）
onUnmounted(() => {
  document.removeEventListener('keydown', handleDocumentKeydown)
})
</script>