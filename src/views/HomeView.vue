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
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1">
              <label :class="['text-sm font-medium', isDark ? 'text-gray-400' : 'text-gray-500']">
                项目标题
              </label>
              <p :class="['mt-1', isDark ? 'text-white' : 'text-gray-900']">
                {{ currentProject.title }}
              </p>
                </div>
                <div class="text-right text-xs" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                  <div>创建于 {{ formatDateTime(currentProject.created_at) }}</div>
                  <div class="mt-1">更新于 {{ formatDateTime(currentProject.updated_at) }}</div>
                </div>
              </div>
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

            <!-- 分割线 -->
            <div class="pt-3 border-t" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
              <!-- 文章摘要 -->
              <div v-if="fullSummary">
                <div class="flex items-center justify-between mb-2">
                  <label :class="['text-sm font-medium', isDark ? 'text-gray-400' : 'text-gray-500']">
                    文章摘要
                  </label>
                  <button
                    @click.stop="confirmDeleteSummary"
                    :disabled="deletingSummary"
                    :class="[
                      'p-1 rounded transition-colors',
                      deletingSummary
                        ? isDark
                          ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : isDark
                          ? 'hover:bg-gray-700 text-gray-400 hover:text-red-400'
                          : 'hover:bg-gray-100 text-gray-500 hover:text-red-600'
                    ]"
                    title="删除摘要"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
                <div 
                  @click="showSummaryDialog = true"
                  class="cursor-pointer rounded-lg p-3 transition-colors"
                  :class="isDark 
                    ? 'bg-gray-700/50 hover:bg-gray-700 text-gray-300' 
                    : 'bg-gray-50 hover:bg-gray-100 text-gray-700'"
                >
                  <p 
                    class="text-sm overflow-hidden"
                    :style="{ 
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      textOverflow: 'ellipsis'
                    }"
                    :class="isDark ? 'text-gray-300' : 'text-gray-700'"
                  >
                    {{ fullSummary.summary }}
                  </p>
                  <p class="text-xs mt-2" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                    点击查看完整摘要
                  </p>
                </div>
              </div>
              <div v-else>
                <label :class="['text-sm font-medium mb-2 block', isDark ? 'text-gray-400' : 'text-gray-500']">
                  文章摘要
                </label>
                <div 
                  @click="generateFullSummary"
                  :class="[
                    'rounded-lg border p-8 cursor-pointer transition-colors text-center',
                    generatingSummary
                      ? isDark
                        ? 'bg-gray-700 border-gray-600 cursor-not-allowed'
                        : 'bg-gray-100 border-gray-300 cursor-not-allowed'
                      : isDark
                        ? 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600'
                        : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                  ]"
                >
                  <svg 
                    class="w-16 h-16 mx-auto mb-4"
                    :class="generatingSummary 
                      ? (isDark ? 'text-gray-600' : 'text-gray-400')
                      : (isDark ? 'text-gray-600' : 'text-gray-400')"
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 
                    :class="[
                      'text-lg font-semibold mb-2',
                      generatingSummary
                        ? (isDark ? 'text-gray-500' : 'text-gray-400')
                        : (isDark ? 'text-gray-300' : 'text-gray-700')
                    ]"
                  >
                    {{ generatingSummary ? '正在生成摘要...' : '暂无文章摘要' }}
                  </h3>
                  <p 
                    :class="[
                      'text-sm',
                      generatingSummary
                        ? (isDark ? 'text-gray-600' : 'text-gray-500')
                        : (isDark ? 'text-gray-500' : 'text-gray-500')
                    ]"
                  >
                    {{ generatingSummary ? '请稍候，摘要生成中' : '点击此处生成文章摘要' }}
                  </p>
                  <div v-if="generatingSummary" class="mt-4">
                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 mx-auto" 
                         :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：当前段落卡片（包含图像） -->
        <div class="xl:col-span-2">
          <!-- 当前段落卡片（包含图像） -->
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
                <!-- 清空按钮 -->
                <button
                  @click="showClearAllConfirm = true"
                  :class="[
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-gray-900'
                  ]"
                  title="清空全部段落图像"
                >
                  清空
                </button>
                <!-- 开始迭代按钮 -->
                <button
                  @click="startFullIteration"
                  :disabled="generatingImage || !currentProject || currentParagraphIndex === null"
                  :class="[
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    (generatingImage || !currentProject || currentParagraphIndex === null)
                      ? isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                  ]"
                  title="开始迭代（生成全部图像）"
                >
                  开始迭代
                </button>
                <!-- 停止迭代按钮 -->
                <button
                  @click="stopIteration"
                  :disabled="!autoMonitoringEnabled"
                  :class="[
                    'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                    !autoMonitoringEnabled
                      ? isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : isDark
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-red-600 hover:bg-red-700 text-white'
                  ]"
                  title="停止迭代"
                >
                  停止迭代
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
              </div>
                </div>
                
            <!-- 图像显示区域（上方） -->
            <div class="mb-6 pb-6 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
              <!-- 如果有图片，显示图片 -->
              <div v-if="currentImageUrl && !generatingImage" class="relative group flex items-center justify-between min-h-[300px] gap-4">
                <!-- 左侧导航按钮 -->
                <button
                  @click="prevParagraph"
                  :disabled="!canGoPrev"
                  :class="[
                    'p-3 rounded-full transition-colors flex-shrink-0',
                    canGoPrev
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                  ]"
                  title="上一段"
                >
                  <ChevronLeftIcon class="w-6 h-6" />
                </button>

                <!-- 图片容器 -->
                <div class="relative flex-1 flex justify-center items-start">
                  <div class="relative flex items-start">
                    <img
                      :src="currentImageUrl"
                      alt="当前段落图片"
                      @click="openParagraphImageGallery"
                      @error="handleImageError"
                      :class="[
                        'h-[300px] w-auto aspect-square object-cover rounded-lg cursor-pointer',
                        isDark ? 'border border-gray-700' : 'border border-gray-200'
                      ]"
                    />
                    <!-- 紧贴图片右上角外部的操作按钮 -->
                    <div class="absolute -right-12 top-0 flex flex-col gap-2 opacity-100">
                      <!-- 显示参数按钮（蓝色） -->
                      <button
                        @click.stop="showDrawArgs"
                        :class="[
                          'p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors hover:bg-blue-600'
                        ]"
                        title="查看生成参数"
                      >
                        <Cog6ToothIcon class="w-5 h-5" />
                      </button>
                      <!-- 查看摘要按钮（绿色） -->
                      <button
                        @click.stop="showDrawSummary"
                        :class="[
                          'p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors hover:bg-green-600'
                        ]"
                        title="查看摘要"
                      >
                        <DocumentTextIcon class="w-5 h-5" />
                      </button>
                      <!-- 重新生成按钮（黄色/橙色） -->
                      <button
                        @click.stop="regenerateImage"
                        :class="[
                          'p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors hover:bg-yellow-600'
                        ]"
                        title="重新生成图片"
                      >
                        <ArrowPathIcon class="w-5 h-5" />
                      </button>
                      <!-- 删除按钮（红色） -->
                      <button
                        @click.stop="confirmDeleteImage"
                        :class="[
                          'p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-colors hover:bg-red-600'
                        ]"
                        title="删除图片"
                      >
                        <TrashIcon class="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 右侧导航按钮 -->
                <button
                  @click="nextParagraph"
                  :disabled="!canGoNext"
                  :class="[
                    'p-3 rounded-full transition-colors flex-shrink-0',
                    canGoNext
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                  ]"
                  title="下一段"
                >
                  <ChevronRightIcon class="w-6 h-6" />
                </button>
            </div>

              <!-- 如果没有图片且正在生成，显示Loading -->
              <div v-else-if="generatingImage" 
                   class="flex items-center justify-between min-h-[300px] gap-4"
              >
                <!-- 左侧占位按钮（保持布局一致） -->
                <div class="w-[52px] flex-shrink-0"></div>
                
                <!-- Loading 内容 -->
                <div class="flex-1 flex items-center justify-center">
                  <div class="h-[300px] w-[300px] flex flex-col items-center justify-center text-center"
                       :class="isDark ? 'text-gray-400' : 'text-gray-500'"
                  >
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 mb-4" 
                   :class="isDark ? 'border-blue-500' : 'border-blue-600'"></div>
                    <p class="text-sm">正在生成图片...</p>
                    <p class="text-xs mt-1 opacity-75">请稍候，图片生成中</p>
            </div>
                </div>
                
                <!-- 右侧占位按钮（保持布局一致） -->
                <div class="w-[52px] flex-shrink-0"></div>
              </div>

              <!-- 如果没有图片且未生成，显示可点击卡片 -->
              <div 
                v-else
                class="flex items-center justify-between min-h-[300px] gap-4"
              >
                <!-- 左侧导航按钮 -->
                <button
                  @click="prevParagraph"
                  :disabled="!canGoPrev"
                 :class="[
                    'p-3 rounded-full transition-colors flex-shrink-0',
                    canGoPrev
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                  ]"
                  title="上一段"
                >
                  <ChevronLeftIcon class="w-6 h-6" />
                </button>

                <!-- 中间：可点击卡片 -->
                <div 
                  @click="generateImage"
                  class="flex-1 flex items-center justify-center"
                >
                  <div 
                    class="h-[300px] w-[300px] flex flex-col items-center justify-center text-center cursor-pointer transition-colors rounded-lg border-2 border-dashed"
                    :class="isDark
                      ? 'border-gray-700 hover:border-gray-600 hover:bg-gray-700/50 text-gray-400 hover:text-gray-300'
                      : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50 text-gray-500 hover:text-gray-600'"
                  >
                    <PhotoIcon class="w-16 h-16 mb-2 opacity-50" />
                    <p class="text-sm font-medium">点击生成图片</p>
                    <p class="text-xs mt-1 opacity-75">为当前段落生成图像</p>
            </div>
                </div>

                <!-- 右侧导航按钮 -->
                <button
                  @click="nextParagraph"
                  :disabled="!canGoNext"
                 :class="[
                    'p-3 rounded-full transition-colors flex-shrink-0',
                    canGoNext
                      ? isDark
                        ? 'bg-gray-700 hover:bg-gray-600 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                      : isDark
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                  ]"
                  title="下一段"
                >
                  <ChevronRightIcon class="w-6 h-6" />
                </button>
            </div>
          </div>

            <!-- 段落内容（下方）- 高度固定为10行，默认上对齐 -->
          <div 
            :class="[
                   'h-[240px] overflow-y-auto',
                   isDark ? 'bg-gray-800' : 'bg-gray-50'
                 ]"
            >
              <div v-if="currentParagraph" 
              :class="[
                     'prose max-w-none p-4',
                     isDark ? 'text-gray-300' : 'text-gray-700'
                   ]"
              >
                <p class="whitespace-pre-wrap">{{ currentParagraph.content }}</p>
              </div>
              <div v-else 
                   :class="[
                     'flex items-center justify-center h-full text-center text-sm',
                isDark ? 'text-gray-500' : 'text-gray-400'
              ]"
            >
                暂无段落内容
              </div>
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

    <!-- 文章摘要对话框 -->
    <div
      v-if="showSummaryDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showSummaryDialog = false"
    >
      <div
        @click.stop
        :class="[
          'w-full max-w-3xl max-h-[80vh] rounded-lg shadow-xl flex flex-col',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <div class="p-6 flex-shrink-0 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <div class="flex items-center justify-between">
            <h2 :class="['text-xl font-bold', isDark ? 'text-white' : 'text-gray-900']">
              文章摘要
            </h2>
            <button
              @click="showSummaryDialog = false"
              :class="[
                'p-1 rounded transition-colors',
                isDark 
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
              ]"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6">
          <div v-if="editingSummary">
            <textarea
              v-model="summaryEditText"
              rows="15"
              :class="[
                'w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 resize-none',
                isDark
                  ? 'bg-gray-700 border-gray-600 text-white focus:ring-blue-500'
                  : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
              ]"
              placeholder="请输入文章摘要..."
            ></textarea>
          </div>
          <div v-else>
            <p 
              class="whitespace-pre-wrap text-sm"
              :class="isDark ? 'text-gray-300' : 'text-gray-700'"
            >
              {{ fullSummary?.summary || '暂无摘要' }}
            </p>
          </div>
        </div>
        
        <div class="p-6 flex-shrink-0 border-t flex justify-end gap-3" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <button
            v-if="!editingSummary"
            @click="editingSummary = true; summaryEditText = fullSummary?.summary || ''"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            ]"
          >
            编辑
          </button>
          <template v-else>
            <button
              @click="editingSummary = false; summaryEditText = ''"
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
              @click="saveSummary"
              :disabled="savingSummary"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                savingSummary
                  ? isDark
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              ]"
            >
              {{ savingSummary ? '保存中...' : '保存' }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- 删除摘要确认对话框 -->
    <div
      v-if="showDeleteSummaryConfirm"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showDeleteSummaryConfirm = false"
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
            确认删除摘要
          </h2>
          <p :class="['mb-6', isDark ? 'text-gray-300' : 'text-gray-700']">
            确定要删除文章摘要吗？
            <br />
            <span class="text-sm text-red-600">此操作不可恢复。</span>
          </p>
          <div class="flex justify-end gap-3">
            <button
              @click="showDeleteSummaryConfirm = false"
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
              @click="deleteSummary"
              :disabled="deletingSummary"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                deletingSummary
                  ? isDark
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              ]"
            >
              {{ deletingSummary ? '删除中...' : '删除' }}
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

    <!-- 图片查看大图对话框 -->
    <ImageGalleryDialog
      :visible="showImageGallery"
      :images="allParagraphImageUrls"
      :initial-index="paragraphGalleryInitialIndex"
      :job-ids="[]"
      @close="showImageGallery = false"
      @show-params="handleShowParams"
    />

    <!-- 参数对话框 -->
    <ModelParamsDialog
      v-if="showParamsDialog && currentDrawArgs"
      :params="currentDrawArgs"
      :title="`段落图像生成参数（第 ${currentParagraphIndex !== null ? currentParagraphIndex + 1 : '?'} 行）`"
      @close="showParamsDialog = false; currentDrawArgs = null"
    />

    <!-- 绘图摘要对话框 -->
    <div
      v-if="showDrawSummaryDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showDrawSummaryDialog = false; currentDrawSummary = null"
    >
      <div
        @click.stop
        :class="[
          'w-full max-w-3xl max-h-[80vh] rounded-lg shadow-xl flex flex-col',
          isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
        ]"
      >
        <div class="p-6 flex-shrink-0 border-b" :class="isDark ? 'border-gray-700' : 'border-gray-200'">
          <div class="flex items-center justify-between">
            <h2 :class="['text-xl font-bold', isDark ? 'text-white' : 'text-gray-900']">
              段落摘要（第 {{ currentParagraphIndex !== null ? currentParagraphIndex + 1 : '?' }} 行）
            </h2>
            <button
              @click="showDrawSummaryDialog = false; currentDrawSummary = null"
              :class="[
                'p-1 rounded transition-colors',
                isDark 
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
              ]"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
  </div>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6">
          <p 
            class="whitespace-pre-wrap text-sm"
            :class="isDark ? 'text-gray-300' : 'text-gray-700'"
          >
            {{ currentDrawSummary || '暂无摘要' }}
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- 清空全部段落图像确认对话框 -->
  <ConfirmDialog
    :show="showClearAllConfirm"
    title="清空全部段落图像"
    message="确定要清空该项目的所有段落图像吗？此操作不可恢复。"
    confirm-text="清空"
    cancel-text="取消"
    type="danger"
    @confirm="clearAllDrawIterations"
    @cancel="showClearAllConfirm = false"
  />
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
  XMarkIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  DocumentTextIcon
} from '@heroicons/vue/24/outline'
import ImageGalleryDialog from '../components/ImageGalleryDialog.vue'
import ModelParamsDialog from '../components/ModelParamsDialog.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { getApiBaseURL } from '../utils/apiConfig'
import { imageCache } from '../utils/imageCache'
import { textCache } from '../utils/textCache'
import { toast } from 'vue-sonner'

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

interface ChapterSummary {
  id?: number
  project_id: string
  chapter_index: number
  title: string
  summary?: string
  start_line: number
  end_line: number
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
const currentParagraphIndex = ref<number | null>(null) // 当前段落的全局索引
const generatingImage = ref(false) // 是否正在生成图片
const imageGeneratingPollingInterval = ref<number | null>(null) // 图片生成轮询
const monitoringIndex = ref<number | null>(null) // 正在监控的段落索引
const autoMonitoringEnabled = ref(false) // 是否启用自动监控
const showClearAllConfirm = ref(false) // 是否显示清空全部确认对话框
const showImageGallery = ref(false) // 是否显示图片查看大图
const paragraphGalleryInitialIndex = ref(0) // 段落图片画廊的初始索引
const showParamsDialog = ref(false) // 是否显示参数对话框
const currentDrawArgs = ref<any>(null) // 当前绘图参数
const showDrawSummaryDialog = ref(false) // 是否显示绘图摘要对话框
const currentDrawSummary = ref<string | null>(null) // 当前绘图摘要

// 文章摘要相关
const fullSummary = ref<ChapterSummary | null>(null)
const showSummaryDialog = ref(false)
const editingSummary = ref(false)
const summaryEditText = ref('')
const savingSummary = ref(false)
const generatingSummary = ref(false)
const deletingSummary = ref(false)
const showDeleteSummaryConfirm = ref(false)
const summaryPollingInterval = ref<number | null>(null)
const llmTimeout = ref<number>(120000) // LLM 请求超时时间（毫秒），默认2分钟

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
    
    // 加载全文摘要
    await loadFullSummary()
  } catch (error) {
    console.error('加载项目详情失败:', error)
  }
}

// 加载当前段落（使用文字缓存，不显示loading，直接替换内容）
const loadCurrentParagraph = async () => {
  if (!currentProject.value) {
    currentParagraph.value = null
    currentImageUrl.value = null
    currentParagraphIndex.value = null
    return
  }

  try {
    const chapter = currentProject.value.current_chapter
    const line = currentProject.value.current_line
    const projectId = currentProject.value.project_id
    
    // 确保参数是有效的（避免 undefined 或 null）
    if (chapter === undefined || chapter === null || line === undefined || line === null) {
      currentParagraph.value = null
      currentImageUrl.value = null
      currentParagraphIndex.value = null
      return
    }
    
    // 构建缓存 key（确保格式一致）
    const cacheKey = `text:${projectId}:${chapter}:${line}`
    
    // 从缓存获取段落内容和索引
    const cachedData = await textCache.get(
      cacheKey,
      projectId,
      chapter,
      line,
      async (projectId: string, chapter: number, line: number) => {
        // 缓存未命中，从后端获取
    // 获取当前段落内容
        const content = await api.get('/content/line', {
        params: {
            project_id: projectId,
          chapter,
          line
        }
      })
      const contentData = (content as any)?.data || content
        
        // 获取全局索引
        const indexResponse = await api.get('/content/paragraph_index', {
          params: {
            project_id: projectId,
            chapter,
            line
          }
        })
        const indexData = (indexResponse as any)?.data || indexResponse
        
        return {
          paragraphIndex: indexData.index,
          paragraphContent: contentData
        }
      }
    )
    
    if (cachedData) {
      // 缓存命中，直接更新内容，不显示loading
      currentParagraph.value = cachedData.paragraphContent
      currentParagraphIndex.value = cachedData.paragraphIndex
      
      // 加载图片（如果有）
      await loadParagraphImage(cachedData.paragraphIndex)
    } else {
      // 缓存获取失败，清空显示
      currentParagraph.value = null
      currentImageUrl.value = null
      currentParagraphIndex.value = null
    }
    } catch (error: any) {
      // 如果段落不存在，清空显示
      if (error.response?.status === 404) {
        currentParagraph.value = null
        currentImageUrl.value = null
      currentParagraphIndex.value = null
      } else {
        console.error('加载段落失败:', error)
      }
  }
}

// 加载段落图片（使用缓存）
const loadParagraphImage = async (index: number) => {
  if (!selectedProjectId.value || index === null || index === undefined) {
    currentImageUrl.value = null
    return
  }

  try {
    // 构建缓存 key
    const cacheKey = `paragraph:${selectedProjectId.value}:${index}`
    
    // 从缓存获取图片
    const blobUrl = await imageCache.getParagraphImage(cacheKey, selectedProjectId.value, index)
    
    if (blobUrl) {
      // 图片存在，使用 blob URL
      currentImageUrl.value = blobUrl
    } else {
      // 图片不存在
      currentImageUrl.value = null
    }
  } catch (error) {
    // 静默处理错误，图片不存在是正常现象
    currentImageUrl.value = null
  }
}

// 生成图片
const generateImage = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null || generatingImage.value) return

  generatingImage.value = true
  try {
    // 调用绑定段落图像API（start_index=None, end_index=index+1）
    await api.post('/llm/bind-paragraph-images', {
      project_id: selectedProjectId.value,
      start_index: null,
      end_index: currentParagraphIndex.value
    })

    // 启动自动监控逻辑
    startAutoMonitoring()
  } catch (error: any) {
    console.error('生成图片失败:', error)
    const message = error.response?.data?.detail || error.message || '生成图片失败'
    alert(message)
    generatingImage.value = false
  }
}

// 启动自动监控逻辑
const startAutoMonitoring = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null) return

  // 清除之前的轮询
  stopImagePolling()

  // 查找上一个有图像的页面（completed 状态的 DrawIteration）
  let lastCompletedIndex: number | null = null
  try {
    // 从当前索引往前查找，找到第一个 completed 状态的 DrawIteration
    for (let i = currentParagraphIndex.value - 1; i >= 0; i--) {
      const response = await api.get('/content/draw_iteration', {
        params: {
          project_id: selectedProjectId.value,
          index: i
        }
      })
      const data = (response as any)?.data || response
      if (data.status === 'completed') {
        lastCompletedIndex = i
        break
      }
    }
  } catch (error) {
    // 静默处理错误
  }

  // 如果找到了上一个有图像的页面，跳转到该页面
  if (lastCompletedIndex !== null && lastCompletedIndex !== currentParagraphIndex.value) {
    // 跳转到上一个有图像的页面
    // 跳转到上一个有图像的页面（通过更新项目位置）
    if (currentProject.value) {
      // 需要根据 lastCompletedIndex 计算对应的 chapter 和 line
      // 这里简化处理：直接使用全局索引跳转
      // 注意：jumpToPosition 函数需要接受 index 参数，如果不存在则使用另一种方式
      // 暂时直接调用 loadCurrentParagraph，因为监控会在当前段落开始
      // 更好的方式是找到 lastCompletedIndex 对应的 chapter 和 line
      await loadCurrentParagraph()
    }
  }

  // 开始监控下一个页面（当前页面）
  monitoringIndex.value = currentParagraphIndex.value
  autoMonitoringEnabled.value = true

  // 立即检查一次
  await checkDrawIterationStatus(monitoringIndex.value)

  // 每2秒轮询一次
  imageGeneratingPollingInterval.value = window.setInterval(async () => {
    if (monitoringIndex.value !== null && autoMonitoringEnabled.value) {
      await checkDrawIterationStatus(monitoringIndex.value)
    }
  }, 2000)
}

// 检查 DrawIteration 状态
const checkDrawIterationStatus = async (index: number) => {
  if (!selectedProjectId.value) return

  try {
    const response = await api.get('/content/draw_iteration', {
      params: {
        project_id: selectedProjectId.value,
        index: index
      }
    })
    const data = (response as any)?.data || response

    if (data.status === 'completed') {
      // 状态为 completed，加载图片
      const cacheKey = `paragraph:${selectedProjectId.value}:${index}`
      imageCache.delete(cacheKey) // 清除缓存，确保获取最新图片
      await loadParagraphImage(index)

      // 如果当前监控的索引就是当前显示的段落，停止生成状态
      if (index === currentParagraphIndex.value) {
        generatingImage.value = false
      }

      // 检查是否有下一个需要监控的段落
      if (monitoringIndex.value !== null && monitoringIndex.value < index) {
        // 继续监控下一个段落
        monitoringIndex.value = index + 1
        // 检查下一个段落是否存在
        if (currentProject.value && monitoringIndex.value < currentProject.value.total_lines) {
          // 下一个段落存在，继续监控
          await checkDrawIterationStatus(monitoringIndex.value)
        } else {
          // 没有下一个段落了，停止监控
          stopImagePolling()
          // 如果下一个段落就是目标段落，自动跳转
          if (monitoringIndex.value === currentParagraphIndex.value) {
            await loadCurrentParagraph()
          }
        }
      } else if (monitoringIndex.value === index) {
        // 当前监控的段落已完成，检查是否有下一个段落
        const nextIndex = index + 1
        if (currentProject.value && nextIndex < currentProject.value.total_lines) {
          // 有下一个段落，继续监控
          monitoringIndex.value = nextIndex
          await checkDrawIterationStatus(monitoringIndex.value)
        } else {
          // 没有下一个段落了，停止监控
          stopImagePolling()
          // 如果目标段落已完成，自动跳转
          if (index === currentParagraphIndex.value) {
            await loadCurrentParagraph()
          }
        }
      }
    } else if (data.status === 'pending' || data.status === 'drawing') {
      // 状态为 pending 或 drawing，继续等待
      // 如果当前监控的索引就是当前显示的段落，显示生成中状态
      if (index === currentParagraphIndex.value) {
        generatingImage.value = true
      }
    } else if (data.status === 'cancelled') {
      // 状态为 cancelled，停止监控
      stopImagePolling()
      if (index === currentParagraphIndex.value) {
        generatingImage.value = false
      }
    }
  } catch (error) {
    // 静默处理错误（DrawIteration 可能不存在）
    if (monitoringIndex.value === index) {
      // 如果当前监控的段落不存在，停止监控
      stopImagePolling()
    }
  }
}

// 停止图片生成轮询
const stopImagePolling = () => {
  if (imageGeneratingPollingInterval.value !== null) {
    clearInterval(imageGeneratingPollingInterval.value)
    imageGeneratingPollingInterval.value = null
  }
  autoMonitoringEnabled.value = false
  monitoringIndex.value = null
}

// 清空全部段落图像
const clearAllDrawIterations = async () => {
  if (!selectedProjectId.value) return

  try {
    await api.delete('/content/draw_iteration/all', {
      params: {
        project_id: selectedProjectId.value
      }
    })

    // 清空图片缓存
    imageCache.clear()

    // 清空当前图片
    currentImageUrl.value = null

    // 显示成功提示
    toast.success('已清空全部段落图像')
    showClearAllConfirm.value = false

    // 重新加载当前段落
    await loadCurrentParagraph()
  } catch (error: any) {
    console.error('清空全部段落图像失败:', error)
    const message = error.response?.data?.detail || error.message || '清空失败'
    toast.error(`清空失败: ${message}`)
  }
}

// 开始全文迭代
const startFullIteration = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null || generatingImage.value || !currentProject.value) return

  generatingImage.value = true
  try {
    // 调用绑定段落图像API（start_index=当前索引, end_index=文章段落数-1）
    await api.post('/llm/bind-paragraph-images', {
      project_id: selectedProjectId.value,
      start_index: currentParagraphIndex.value,
      end_index: currentProject.value.total_lines - 1
    })

    // 启动自动监控逻辑
    startAutoMonitoring()
  } catch (error: any) {
    console.error('开始全文迭代失败:', error)
    const message = error.response?.data?.detail || error.message || '开始迭代失败'
    toast.error(`开始迭代失败: ${message}`)
    generatingImage.value = false
  }
}

// 停止迭代
const stopIteration = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null || !autoMonitoringEnabled.value) return

  try {
    // 调用停止迭代API，将当前索引之后的所有 pending 状态的任务设置为 cancelled
    await api.post('/content/draw_iteration/cancel', {
      project_id: selectedProjectId.value,
      start_index: currentParagraphIndex.value
    })

    // 停止监控
    stopImagePolling()

    // 显示成功提示
    toast.success('已停止迭代')
  } catch (error: any) {
    console.error('停止迭代失败:', error)
    const message = error.response?.data?.detail || error.message || '停止迭代失败'
    toast.error(`停止迭代失败: ${message}`)
  }
}

// 显示生成参数
const showDrawArgs = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null) return

  try {
    const response = await api.get('/content/draw_iteration', {
      params: {
        project_id: selectedProjectId.value,
        index: currentParagraphIndex.value
      }
    })
    const data = (response as any)?.data || response
    currentDrawArgs.value = data.draw_args
    showParamsDialog.value = true
  } catch (error: any) {
    console.error('获取生成参数失败:', error)
    if (error.response?.status === 404) {
      alert('未找到生成参数')
    } else {
      const message = error.response?.data?.detail || error.message || '获取生成参数失败'
      alert(message)
    }
  }
}

// 显示绘图摘要
const showDrawSummary = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null) return

  try {
    const response = await api.get('/content/draw_iteration', {
      params: {
        project_id: selectedProjectId.value,
        index: currentParagraphIndex.value
      }
    })
    const data = (response as any)?.data || response
    currentDrawSummary.value = data.summary || '暂无摘要'
    showDrawSummaryDialog.value = true
  } catch (error: any) {
    console.error('获取摘要失败:', error)
    if (error.response?.status === 404) {
      alert('未找到摘要')
    } else {
      const message = error.response?.data?.detail || error.message || '获取摘要失败'
      alert(message)
    }
  }
}

// 获取所有段落的图片 URL 列表（用于图片画廊）
const allParagraphImageUrls = computed(() => {
  // 这个计算属性会在需要时动态生成
  // 但为了性能，我们只在打开画廊时才加载
  return paragraphImageUrls.value
})

// 段落图片 URL 列表（缓存）
const paragraphImageUrls = ref<string[]>([])
const paragraphImageUrlToIndex = ref<Map<string, number>>(new Map()) // URL 到原始段落索引的映射

// 加载所有段落图片 URL（异步）
const loadAllParagraphImageUrls = async () => {
  if (!selectedProjectId.value || !currentProject.value) {
    paragraphImageUrls.value = []
    paragraphImageUrlToIndex.value.clear()
    return
  }

  const totalLines = currentProject.value.total_lines || 0
  if (totalLines === 0) {
    paragraphImageUrls.value = []
    paragraphImageUrlToIndex.value.clear()
    return
  }

  // 清空之前的列表
  const urls: string[] = []
  const urlToIndexMap = new Map<string, number>()

  // 首先尝试从缓存中获取已存在的图片
  // imageCache 内部维护了缓存，我们可以先检查已缓存的图片
  // 然后对于未缓存的，只检查附近的段落（避免加载所有段落）
  
  // 获取当前段落索引附近的段落图片（前后各 20 个段落）
  const currentIndex = currentParagraphIndex.value ?? 0
  const startIndex = Math.max(0, currentIndex - 20)
  const endIndex = Math.min(totalLines, currentIndex + 21)
  
  // 并行加载当前段落附近的图片
  const concurrency = 10 // 每次最多 10 个并发请求
  for (let i = startIndex; i < endIndex; i += concurrency) {
    const batch = []
    for (let j = i; j < Math.min(i + concurrency, endIndex); j++) {
      batch.push(
        (async () => {
          try {
            const cacheKey = `paragraph:${selectedProjectId.value}:${j}`
            const blobUrl = await imageCache.getParagraphImage(cacheKey, selectedProjectId.value!, j)
            if (blobUrl) {
              urls.push(blobUrl)
              urlToIndexMap.set(blobUrl, j)
            }
          } catch (error) {
            // 静默处理错误，图片不存在是正常现象
          }
        })()
      )
    }
    await Promise.all(batch)
  }

  // 按照索引顺序排序（确保画廊中的图片顺序正确）
  urls.sort((a, b) => {
    const indexA = urlToIndexMap.get(a) || 0
    const indexB = urlToIndexMap.get(b) || 0
    return indexA - indexB
  })

  paragraphImageUrls.value = urls
  paragraphImageUrlToIndex.value = urlToIndexMap
}

// 打开段落图片画廊
const openParagraphImageGallery = async () => {
  if (!currentImageUrl.value) return

  // 加载所有段落图片 URL
  await loadAllParagraphImageUrls()

  // 找到当前图片在列表中的索引
  const currentIndex = paragraphImageUrls.value.indexOf(currentImageUrl.value)
  if (currentIndex >= 0) {
    paragraphGalleryInitialIndex.value = currentIndex
  } else {
    // 如果当前图片不在列表中（可能是因为缓存问题），尝试重新加载
    // 或者直接添加到列表开头
    if (currentImageUrl.value) {
      paragraphImageUrls.value = [currentImageUrl.value, ...paragraphImageUrls.value]
      paragraphGalleryInitialIndex.value = 0
    }
  }

  showImageGallery.value = true
}

// 处理显示参数（来自ImageGalleryDialog）
const handleShowParams = () => {
  // 段落图片的参数来自DrawIteration，不是job，所以直接调用showDrawArgs
  showDrawArgs()
}

// 处理图片加载错误（静默处理404）
const handleImageError = (event: Event) => {
  // 静默处理404错误，图片不存在是正常现象，不需要报错或显示错误
  // 只需要清空图片URL，让界面显示"点击生成图片"状态
  currentImageUrl.value = null
  // 阻止默认的错误行为，避免浏览器控制台显示错误
  event.preventDefault?.()
  event.stopPropagation?.()
}

// 删除图片
const confirmDeleteImage = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null || !currentProject.value) return

  try {
    await api.delete('/content/draw_iteration', {
      params: {
        project_id: selectedProjectId.value,
        index: currentParagraphIndex.value
      }
    })

    // 清除图片缓存
    const imageCacheKey = `paragraph:${selectedProjectId.value}:${currentParagraphIndex.value}`
    imageCache.delete(imageCacheKey)

    // 清除文字缓存
    const textCacheKey = `text:${selectedProjectId.value}:${currentProject.value.current_chapter}:${currentProject.value.current_line}`
    textCache.delete(textCacheKey)

    // 清空图片URL
    currentImageUrl.value = null

    // 显示成功提示
    toast.success('图片已删除')
  } catch (error: any) {
    console.error('删除图片失败:', error)
    const message = error.response?.data?.detail || error.message || '删除图片失败'
    toast.error(`删除失败: ${message}`)
  }
}

// 重新生成图片
const regenerateImage = async () => {
  if (!selectedProjectId.value || currentParagraphIndex.value === null || generatingImage.value || !currentProject.value) return
  
  // 清除图片缓存
  const imageCacheKey = `paragraph:${selectedProjectId.value}:${currentParagraphIndex.value}`
  imageCache.delete(imageCacheKey)
  
  // 清除文字缓存（因为重新生成可能会更新内容）
  const textCacheKey = `text:${selectedProjectId.value}:${currentProject.value.current_chapter}:${currentProject.value.current_line}`
  textCache.delete(textCacheKey)
  
  // 清空当前图片URL
  currentImageUrl.value = null
  
  // 调用生成图片函数
  await generateImage()
}

// 切换到上一段
const prevParagraph = async () => {
  if (!currentProject.value || !canGoPrev.value) return

  try {
    let newChapter = currentProject.value.current_chapter
    let newLine = currentProject.value.current_line - 1

    if (newLine < 0 && newChapter > 0) {
      newChapter -= 1
      // 获取上一章的所有行，取最后一行的行号
      try {
        const response = await api.get('/content/lines', {
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
      // 先直接更新本地项目状态，立即显示新内容（不等待PUT请求）
      if (currentProject.value) {
        currentProject.value.current_line = newLine
        currentProject.value.current_chapter = newChapter
      }
      
      // 加载新的段落内容（使用缓存，快速显示）
      await loadCurrentParagraph()
      
      // 后台更新项目进度（不阻塞UI）
      api.put(`/project/${currentProject.value.project_id}`, null, {
        params: {
          current_line: newLine,
          current_chapter: newChapter
        }
      }).catch((error) => {
        console.error('更新项目进度失败:', error)
      })
    }
  } catch (error) {
    console.error('切换到上一段失败:', error)
  }
}

// 切换到下一段
const nextParagraph = async () => {
  if (!currentProject.value || !canGoNext.value) return

  try {
    let newChapter = currentProject.value.current_chapter
    let newLine = currentProject.value.current_line + 1

    // 检查是否超出当前章节
    try {
      const response = await api.get('/content/lines', {
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

    // 先直接更新本地项目状态，立即显示新内容（不等待PUT请求）
    if (currentProject.value) {
      currentProject.value.current_line = newLine
      currentProject.value.current_chapter = newChapter
    }
    
    // 加载新的段落内容（使用缓存，快速显示）
    await loadCurrentParagraph()
    
    // 后台更新项目进度（不阻塞UI）
    api.put(`/project/${currentProject.value.project_id}`, null, {
      params: {
        current_line: newLine,
        current_chapter: newChapter
      }
    }).catch((error) => {
      console.error('更新项目进度失败:', error)
    })
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
    // 先直接更新本地项目状态，立即显示新内容（不等待PUT请求）
    if (currentProject.value) {
      currentProject.value.current_line = targetLine
      currentProject.value.current_chapter = targetChapter
    }
    
    // 关闭对话框
    showJumpDialog.value = false
    
    // 重新加载项目信息和段落（使用缓存，快速显示）
    await loadCurrentProject()
    
    // 后台更新项目进度（不阻塞UI）
    api.put(`/project/${currentProject.value.project_id}`, null, {
      params: {
        current_line: targetLine,
        current_chapter: targetChapter
      }
    }).catch((error) => {
      console.error('更新项目进度失败:', error)
    })
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

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载全文摘要
const loadFullSummary = async () => {
  if (!selectedProjectId.value) {
    fullSummary.value = null
    return
  }

  try {
    const response = await api.get('/summary/full', {
      params: {
        project_id: selectedProjectId.value
      }
    })
    const data = (response as any)?.data || response
    fullSummary.value = data || null
  } catch (error: any) {
    if (error.response?.status === 404) {
      fullSummary.value = null
    } else {
      console.error('加载全文摘要失败:', error)
    }
  }
}

// 生成全文摘要
// 加载 LLM 设置（获取超时时间）
const loadLlmSettings = async () => {
  try {
    const settings = await api.get('/settings/llm')
    if (settings && settings.timeout) {
      // 将秒转换为毫秒
      llmTimeout.value = settings.timeout * 1000
    }
  } catch (error) {
    console.error('加载 LLM 设置失败:', error)
    // 使用默认值，不中断流程
  }
}

const generateFullSummary = async () => {
  if (!selectedProjectId.value || generatingSummary.value) return

  generatingSummary.value = true
  try {
    // 调用生成摘要端点（默认使用直接模式），使用 LLM 设置中的超时时间
    await api.post('/llm/generate-full-summary', {
      project_id: selectedProjectId.value,
      direct_mode: true
    }, {
      timeout: llmTimeout.value
    })

    // 启动轮询监控
    startSummaryPolling()
  } catch (error: any) {
    console.error('生成全文摘要失败:', error)
    const message = error.response?.data?.detail || error.message || '生成摘要失败'
    alert(message)
    generatingSummary.value = false
  }
}

// 启动摘要轮询监控
const startSummaryPolling = () => {
  // 清除之前的轮询
  if (summaryPollingInterval.value !== null) {
    clearInterval(summaryPollingInterval.value)
  }

  // 立即加载一次
  loadFullSummary()

  // 每2秒轮询一次
  summaryPollingInterval.value = window.setInterval(async () => {
    await loadFullSummary()
    
    // 如果已经生成摘要，停止轮询
    if (fullSummary.value?.summary) {
      stopSummaryPolling()
      generatingSummary.value = false
    }
  }, 2000)
}

// 停止摘要轮询
const stopSummaryPolling = () => {
  if (summaryPollingInterval.value !== null) {
    clearInterval(summaryPollingInterval.value)
    summaryPollingInterval.value = null
  }
}

// 保存摘要
const saveSummary = async () => {
  if (!selectedProjectId.value || !fullSummary.value || savingSummary.value) return

  savingSummary.value = true
  try {
    await api.put(`/summary/-1`, {
      summary: summaryEditText.value
    }, {
      params: {
        project_id: selectedProjectId.value
      }
    })

    // 重新加载摘要
    await loadFullSummary()
    editingSummary.value = false
    summaryEditText.value = ''
  } catch (error: any) {
    console.error('保存摘要失败:', error)
    const message = error.response?.data?.detail || error.message || '保存摘要失败'
    alert(message)
  } finally {
    savingSummary.value = false
  }
}

// 确认删除摘要
const confirmDeleteSummary = () => {
  if (!fullSummary.value) return
  showDeleteSummaryConfirm.value = true
}

// 删除摘要
const deleteSummary = async () => {
  if (!selectedProjectId.value || !fullSummary.value || deletingSummary.value) return

  deletingSummary.value = true
  try {
    await api.delete(`/summary/-1`, {
      params: {
        project_id: selectedProjectId.value
      }
    })

    // 关闭对话框
    showDeleteSummaryConfirm.value = false
    
    // 清空摘要
    fullSummary.value = null
  } catch (error: any) {
    console.error('删除摘要失败:', error)
    const message = error.response?.data?.detail || error.message || '删除摘要失败'
    alert(message)
  } finally {
    deletingSummary.value = false
  }
}

// 监听选中项目变化（使用 store）
watch(() => selectedProjectId.value, (newId) => {
  // 停止之前的轮询
  stopSummaryPolling()
  stopImagePolling()
  generatingSummary.value = false
  generatingImage.value = false
  
  if (newId) {
    loadCurrentProject()
  } else {
    currentParagraph.value = null
    currentImageUrl.value = null
    currentParagraphIndex.value = null
    fullSummary.value = null
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
  // 加载 LLM 设置（获取超时时间）
  await loadLlmSettings()
  
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
  stopSummaryPolling()
  stopImagePolling()
})
</script>