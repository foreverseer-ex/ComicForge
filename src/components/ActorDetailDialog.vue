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
                  'w-full h-96 rounded-lg overflow-hidden border flex flex-col cursor-pointer relative',
                  isDark ? 'border-gray-600 bg-gray-900' : 'border-gray-200 bg-gray-50'
                ]"
                @click="openImageGallery"
              >
                <div class="flex-1 flex items-center justify-center">
                  <img
                    v-if="!privacyMode"
                    :src="exampleBlobUrls[currentExampleIndex] || ''"
                    :alt="currentExample.title || actor.name"
                    class="w-full h-full object-contain"
                    @error="handleCurrentImageError"
                    @load="handleCurrentImageLoad"
                  />
                  <div v-else class="flex flex-col items-center justify-center">
                    <PhotoIcon class="w-16 h-16 mb-2" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
                    <span :class="['text-sm', isDark ? 'text-gray-500' : 'text-gray-500']">隐私模式</span>
                  </div>
                </div>
                <!-- 标题（浮动在图片下方） -->
                <div 
                  v-if="currentExample.title"
                  :class="[
                    'absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-sm px-3 py-2 text-center',
                    isDark ? 'bg-opacity-80' : 'bg-opacity-70'
                  ]"
                >
                  {{ currentExample.title }}
                </div>
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
                <div class="flex items-center gap-2">
                  <button
                    v-if="exampleCount > 0"
                    @click="clearAllExamples"
                    :class="[
                      'p-2 rounded-lg transition-colors',
                      isDark
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-red-500 hover:bg-red-600 text-white'
                    ]"
                    title="清空所有立绘"
                  >
                    <TrashIcon class="w-5 h-5" />
                  </button>
                  <button
                    v-if="exampleCount > 0"
                    @click="openGenerateDialog"
                    :class="[
                      'p-2 rounded-lg transition-colors',
                      isDark
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                    ]"
                    title="生成新立绘"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="exampleCount > 0" class="overflow-x-auto">
                <div class="flex gap-4 pb-2">
                  <div
                    v-for="(example, index) in actor.examples"
                    :key="index"
                    class="flex-shrink-0"
                    style="width: 120px;"
                  >
                    <!-- 图片容器 -->
                    <div
                      :class="[
                        'relative rounded-lg overflow-hidden border cursor-pointer',
                        isDark ? 'border-gray-600' : 'border-gray-200'
                      ]"
                      style="width: 120px; height: 120px;"
                      @click="viewExample(index)"
                      @contextmenu.prevent="showExampleContextMenu($event, example, index)"
                    >
                      <!-- 有图片路径时显示图片 -->
                      <template v-if="example.image_path">
                        <img
                          v-if="!privacyMode"
                          :src="exampleBlobUrls[index] || ''"
                          :alt="example.title || `立绘 ${index + 1}`"
                          class="w-full h-full object-cover"
                          @error="(e) => handleExampleImageError(e, index)"
                          @load="(e) => handleExampleImageLoad(e, index)"
                        />
                        <div v-else :class="['w-full h-full flex flex-col items-center justify-center', isDark ? 'bg-gray-800' : 'bg-gray-100']">
                          <PhotoIcon class="w-8 h-8 mb-1" :class="isDark ? 'text-gray-600' : 'text-gray-400'" />
                          <span :class="['text-xs', isDark ? 'text-gray-500' : 'text-gray-500']">隐私模式</span>
                        </div>
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
                    </div>
                    <!-- 标题（在图片下方，不是浮动） -->
                    <div
                      v-if="example.title"
                      @click.stop="viewExampleParams(index)"
                      :class="[
                        'mt-2 text-xs text-center cursor-pointer truncate px-1',
                        isDark ? 'text-gray-300' : 'text-gray-600'
                      ]"
                      :title="example.title"
                    >
                      {{ example.title }}
                    </div>
                    <div
                      v-else
                      :class="[
                        'mt-2 text-xs text-center text-gray-500 px-1'
                      ]"
                    >
                      立绘 {{ index + 1 }}
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
        v-if="exampleCount > 1"
        @click="deleteOtherExamples"
        :class="[
          'w-full px-4 py-2 text-left text-sm transition-colors',
          isDark 
            ? 'text-gray-300 hover:bg-orange-600 hover:text-white' 
            : 'text-gray-700 hover:bg-orange-500 hover:text-white'
        ]"
      >
        删除其他立绘
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
      :project-id="actor?.project_id || null"
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
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :show="confirmDialog.show"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :type="confirmDialog.type"
      :items="confirmDialog.items"
      :warning-text="confirmDialog.warningText"
      @confirm="confirmDialog.onConfirm"
      @cancel="confirmDialog.show = false"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch, onUnmounted, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'
import { usePrivacyStore } from '../stores/privacy'
import { storeToRefs } from 'pinia'
import { 
  PhotoIcon, 
  PencilIcon, 
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  ClipboardIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import api from '../api'
import { getApiBaseURL } from '../utils/apiConfig'
import GeneratePortraitDialog from './GeneratePortraitDialog.vue'
import ModelParamsDialog from './ModelParamsDialog.vue'
import ImageGalleryDialog from './ImageGalleryDialog.vue'
import ConfirmDialog from './ConfirmDialog.vue'
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

const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

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

// 确认对话框状态
const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  type: 'default' as 'default' | 'danger',
  items: [] as string[],
  warningText: '',
  onConfirm: () => {}
})

// 当前example
const currentExample = computed(() => {
  if (!props.actor?.examples || currentExampleIndex.value >= props.actor.examples.length) {
    return null
  }
  return props.actor.examples[currentExampleIndex.value]
})

// 受保护图片的 blob URL 缓存（索引 -> blob URL）
const exampleBlobUrls = ref<string[]>([])

// 依据 index 生成后端受保护图片 URL
const buildProtectedExampleUrl = (index: number) => {
  if (!props.actor?.examples?.[index]?.image_path || !props.actor) return ''
  const example = props.actor.examples[index]
  const baseURL = getApiBaseURL()
  return `${baseURL}/actor/${props.actor.actor_id}/image?example_index=${index}&path=${encodeURIComponent(example.image_path)}`
}

// 加载单个 example 的 blob URL（带鉴权）
const ensureExampleBlobLoaded = async (index: number) => {
  if (!props.actor?.examples?.[index]?.image_path) return
  if (exampleBlobUrls.value[index]) return
  try {
    const apiBase = getApiBaseURL()
    const fullUrl = buildProtectedExampleUrl(index)
    const relative = fullUrl.replace(apiBase, '')
    const resp = await api.get(relative, { responseType: 'blob' })
    const blobUrl = URL.createObjectURL(resp as any)
    exampleBlobUrls.value[index] = blobUrl
  } catch (e) {
    console.error('加载受保护图片失败:', index, e)
  }
}

// 批量加载全部（数量通常不大）
const loadAllExampleBlobs = async () => {
  if (!props.actor?.examples) return
  exampleBlobUrls.value = new Array(props.actor.examples.length).fill('')
  await Promise.all(props.actor.examples.map((_ex, i) => ensureExampleBlobLoaded(i)))
}

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

// const firstExample = computed(() => {
//   if (!props.actor?.examples || props.actor.examples.length === 0) return null
//   return props.actor.examples[0]
// })

const getExampleImageUrl = (example: any, index: number) => {
  if (!example?.image_path || !props.actor) return ''
  const baseURL = getApiBaseURL()
  // 通过 actor-example 端点获取图片
  // 使用 image_path 作为缓存破坏参数，确保不同图片使用不同的 URL
  // 这样即使两个 job 名称相同，只要 image_path 不同，URL 就不同
  return `${baseURL}/actor/${props.actor.actor_id}/image?example_index=${index}&path=${encodeURIComponent(example.image_path)}`
}

// 图片重试相关状态
const currentImageRetryCount = ref(0)
const currentImageLoadKey = ref(0)
const currentImageTimestamp = ref(Date.now())
const exampleImageRetryCounts = ref<Record<number, number>>({})
const exampleImageLoadKeys = ref<Record<number, number>>({})
const exampleImageTimestamps = ref<Record<number, number>>({})

// 已改为通过 ensureExampleBlobLoaded 加载 blob URL，这里不再需要基于查询参数的重试 URL 生成

// 当前图片错误处理
const handleCurrentImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (currentImageRetryCount.value < 3) {
    currentImageRetryCount.value++
    currentImageLoadKey.value++
    currentImageTimestamp.value = Date.now() // 更新时间戳，强制重新加载
    setTimeout(async () => {
      await ensureExampleBlobLoaded(currentExampleIndex.value)
      if (img) {
        img.src = exampleBlobUrls.value[currentExampleIndex.value] || ''
      }
    }, 500)
  } else {
    console.error('当前图片加载失败，已重试3次:', buildProtectedExampleUrl(currentExampleIndex.value))
  }
}

// 当前图片加载成功
const handleCurrentImageLoad = () => {
  currentImageRetryCount.value = 0
  currentImageLoadKey.value = 0
}

// 立绘列表中图片错误处理
const handleExampleImageError = (event: Event, index: number) => {
  const img = event.target as HTMLImageElement
  const retryCount = exampleImageRetryCounts.value[index] || 0
  if (retryCount < 3) {
    exampleImageRetryCounts.value[index] = retryCount + 1
    exampleImageLoadKeys.value[index] = (exampleImageLoadKeys.value[index] || 0) + 1
    exampleImageTimestamps.value[index] = Date.now() // 更新时间戳，强制重新加载
    setTimeout(async () => {
      await ensureExampleBlobLoaded(index)
      if (img) {
        img.src = exampleBlobUrls.value[index] || ''
      }
    }, 500)
  } else {
    console.error(`立绘 ${index} 加载失败，已重试3次:`, buildProtectedExampleUrl(index))
  }
}

// 立绘列表中图片加载成功
const handleExampleImageLoad = (_event: Event, index: number) => {
  exampleImageRetryCounts.value[index] = 0
  exampleImageLoadKeys.value[index] = 0
}

// 检查是否有正在生成的立绘（image_path 为 None）
const hasGeneratingPortrait = computed(() => {
  if (!props.actor?.examples) return false
  return props.actor.examples.some((ex: any) => !ex.image_path)
})

// 每5秒检查一次正在生成的立绘状态（如果有正在生成的立绘）
let refreshTimer: ReturnType<typeof setInterval> | null = null
// 保存上一次的 examples 状态，用于比较是否有变化
const lastExamplesState = ref<string>('')

watch(() => props.actor, (newActor) => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  
  // 初始化状态快照
  if (newActor?.examples) {
    lastExamplesState.value = JSON.stringify(newActor.examples.map((ex: any) => ({
      image_path: ex.image_path,
      title: ex.title
    })))
  }
  
  // 如果有正在生成的立绘，启动定时检查（只检查状态变化，不刷新整个页面）
  if (newActor && hasGeneratingPortrait.value) {
    refreshTimer = setInterval(async () => {
      try {
        // 只获取 actor 数据，检查是否有变化
        const response = await api.get(`/actor/${newActor.actor_id}`)
        const actorData = (response as any)?.data || response
        if (actorData && actorData.examples) {
          // 比较当前状态和上次状态
          const currentState = JSON.stringify(actorData.examples.map((ex: any) => ({
            image_path: ex.image_path,
            title: ex.title
          })))
          
          // 如果有变化（比如 image_path 从 null 变成了有值），才更新
          if (currentState !== lastExamplesState.value) {
            lastExamplesState.value = currentState
            // 只更新 actor 数据，不触发整个页面刷新
            // 通过 emit('refresh') 让父组件更新，但父组件会智能更新，不会关闭对话框
            emit('refresh')
          }
          // 如果没有变化，不进行任何操作，避免刷新页面
        }
      } catch (error) {
        console.error('检查立绘状态失败:', error)
      }
    }, 5000) // 每5秒检查一次
  }
}, { immediate: true })

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

// const openEditDialog = () => {
//   if (props.actor) {
//     emit('edit', props.actor)
//   }
// }

const openGenerateDialog = () => {
  showGenerateDialog.value = true
}

const handleGenerated = () => {
  // 生成完成后刷新角色信息
  emit('refresh')
}

// const openExamplesDialog = () => {
//   if (props.actor) {
//     emit('examples', props.actor)
//   }
// }

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

// 监听角色变化，只在角色ID变化时重置索引（避免交换立绘时错误重置）
let lastActorId = ref<string | null>(null)
watch(() => props.actor, (newActor, oldActor) => {
  if (newActor) {
    // 只有在角色ID变化时才重置索引（新打开对话框时）
    if (lastActorId.value !== newActor.actor_id) {
      currentExampleIndex.value = 0
      lastActorId.value = newActor.actor_id
    } else if (oldActor && newActor.examples && oldActor.examples) {
      // 如果角色ID相同，但 examples 数组引用变化了，说明数据已更新
      // 保持当前索引不变（已经在 setAsDefaultExample 中更新了）
      // 这里不需要做任何操作，让 Vue 的响应式系统自动更新视图
    }
    showParamsDialog.value = false
    showImageGallery.value = false
  } else {
    lastActorId.value = null
  }
}, { immediate: true, deep: true })

// 查看立绘（点击时）
const viewExample = (index: number) => {
  // 设置当前索引并打开大图
  currentExampleIndex.value = index
  if (props.actor?.examples[index]?.image_path) {
    openImageGallery()
  }
}

// 查看立绘参数（点击标题时）
const viewExampleParams = (index: number) => {
  if (!props.actor?.examples || index >= props.actor.examples.length) return
  const example = props.actor.examples[index]
  if (example?.draw_args) {
    // 设置当前索引（用于显示正确的参数）
    currentExampleIndex.value = index
    showParamsDialog.value = true
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
  
  const oldIndex = contextMenu.value.index
  
  try {
    // 调用交换API，将选中的立绘与index=0的立绘交换
    await api.post(`/actor/${props.actor.actor_id}/example/swap`, null, {
      params: {
        index1: oldIndex,
        index2: 0
      }
    })
    
    contextMenu.value.show = false
    
    // 设置默认图像后，切换到第0张图像（因为默认图像就是索引0）
    currentExampleIndex.value = 0
    
    // 触发刷新，让父组件重新加载 actor 数据
    emit('refresh')
    
    // 等待一小段时间，确保数据已更新
    await new Promise(resolve => setTimeout(resolve, 100))
    
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

// 清空所有立绘
const clearAllExamples = () => {
  if (!props.actor) return
  
  confirmDialog.value = {
    show: true,
    title: '确认清空',
    message: '确定要清空所有立绘吗？',
    type: 'danger',
    items: [],
    warningText: '此操作不可撤销。',
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        await api.delete(`/actor/${props.actor!.actor_id}/examples/clear`, {
          params: {
            project_id: props.actor!.project_id
          }
        })
        
        showToast('已清空所有立绘', 'success')
        emit('refresh')
      } catch (error: any) {
        console.error('清空立绘失败:', error)
        showToast('清空立绘失败: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  }
}

// 删除其他立绘（保留当前立绘）
const deleteOtherExamples = () => {
  if (!props.actor || contextMenu.value.index === -1) return
  
  confirmDialog.value = {
    show: true,
    title: '确认删除',
    message: '确定要删除除当前立绘外的所有其他立绘吗？',
    type: 'danger',
    items: [],
    warningText: '此操作不可撤销。',
    onConfirm: async () => {
      confirmDialog.value.show = false
      try {
        const currentIndex = contextMenu.value.index
        
        // 如果当前立绘不是 index=0，先将其移动到 index=0
        if (currentIndex !== 0) {
          await api.post(`/actor/${props.actor!.actor_id}/example/swap`, null, {
            params: {
              index1: 0,
              index2: currentIndex,
              project_id: props.actor!.project_id
            }
          })
        }
        
        // 计算要删除的索引列表（除了 index=0 之外的所有索引）
        // 需要先刷新 actor 数据以获取最新的 examples 列表
        const response = await api.get(`/actor/${props.actor!.actor_id}`)
        const updatedActor = (response as any)?.data || response
        const totalCount = updatedActor?.examples?.length || 0
        
        if (totalCount <= 1) {
          showToast('没有其他立绘需要删除', 'info')
          contextMenu.value.show = false
          return
        }
        
        // 要删除的索引：从 1 到 totalCount-1
        const indicesToDelete = Array.from({ length: totalCount - 1 }, (_, i) => i + 1)
        
        // 批量删除
        await api.post(`/actor/${props.actor!.actor_id}/examples/batch-remove`, indicesToDelete, {
          params: {
            project_id: props.actor!.project_id
          }
        })
        
        showToast('已删除其他立绘', 'success')
        contextMenu.value.show = false
        emit('refresh')
      } catch (error: any) {
        console.error('删除其他立绘失败:', error)
        showToast('删除其他立绘失败: ' + (error.response?.data?.detail || error.message), 'error')
        contextMenu.value.show = false
      }
    }
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
onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)
  if (props.actor) {
    await loadAllExampleBlobs()
  }
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

