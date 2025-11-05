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
          <div class="flex items-center gap-2">
            <button
              @click="openGenerateDialog"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-300'
                  : 'hover:bg-gray-100 text-gray-600'
              ]"
              title="生成立绘"
            >
              <PhotoIcon class="w-5 h-5" />
            </button>
            <button
              @click="openEditDialog"
              :class="[
                'p-2 rounded-lg transition-colors',
                isDark
                  ? 'hover:bg-gray-700 text-gray-300'
                  : 'hover:bg-gray-100 text-gray-600'
              ]"
              title="编辑"
            >
              <PencilIcon class="w-5 h-5" />
            </button>
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
        </div>

        <!-- 内容区域 -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-6">
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
              <div class="space-y-2">
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0', isDark ? 'text-gray-300' : 'text-gray-700']">
                    名称:
                  </span>
                  <span :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ actor.name }}
                  </span>
                </div>
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0', isDark ? 'text-gray-300' : 'text-gray-700']">
                    描述:
                  </span>
                  <span :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ actor.desc || '无' }}
                  </span>
                </div>
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0', isDark ? 'text-gray-300' : 'text-gray-700']">
                    颜色:
                  </span>
                  <div class="flex items-center gap-2">
                    <div 
                      class="w-8 h-8 rounded border"
                      :style="{ backgroundColor: actor.color || '#808080' }"
                    ></div>
                    <span :class="['text-sm', isDark ? 'text-gray-400' : 'text-gray-600']">
                      {{ actor.color || '#808080' }}
                    </span>
                  </div>
                </div>
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0', isDark ? 'text-gray-300' : 'text-gray-700']">
                    Actor ID:
                  </span>
                  <span :class="['text-sm break-all', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ actor.actor_id }}
                  </span>
                </div>
                <div class="flex items-start gap-2">
                  <span :class="['font-semibold text-sm w-24 flex-shrink-0', isDark ? 'text-gray-300' : 'text-gray-700']">
                    项目 ID:
                  </span>
                  <span :class="['text-sm break-all', isDark ? 'text-gray-400' : 'text-gray-600']">
                    {{ actor.project_id }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 统计信息 -->
            <div>
              <h3 
                :class="[
                  'text-lg font-semibold mb-3',
                  isDark ? 'text-white' : 'text-gray-900'
                ]"
              >
                统计信息
              </h3>
              <div class="grid grid-cols-2 gap-4">
                <div 
                  :class="[
                    'p-4 rounded-lg border',
                    isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <PhotoIcon class="w-5 h-5" :class="isDark ? 'text-blue-400' : 'text-blue-600'" />
                    <span :class="['font-semibold', isDark ? 'text-white' : 'text-gray-900']">
                      示例图数量
                    </span>
                  </div>
                  <p :class="['text-2xl font-bold mt-2', isDark ? 'text-white' : 'text-gray-900']">
                    {{ exampleCount }}
                  </p>
                </div>
                <div 
                  :class="[
                    'p-4 rounded-lg border',
                    isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                  ]"
                >
                  <div class="flex items-center gap-2">
                    <TagIcon class="w-5 h-5" :class="isDark ? 'text-green-400' : 'text-green-600'" />
                    <span :class="['font-semibold', isDark ? 'text-white' : 'text-gray-900']">
                      标签数量
                    </span>
                  </div>
                  <p :class="['text-2xl font-bold mt-2', isDark ? 'text-white' : 'text-gray-900']">
                    {{ tagCount }}
                  </p>
                </div>
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
              <div v-if="tagCount > 0" class="space-y-2">
                <div
                  v-for="(value, key) in actor.tags"
                  :key="key"
                  :class="[
                    'p-3 rounded-lg border',
                    isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
                  ]"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex-1">
                      <p :class="['font-semibold text-sm', isDark ? 'text-gray-300' : 'text-gray-700']">
                        {{ key }}
                      </p>
                      <p :class="['text-sm mt-1', isDark ? 'text-gray-400' : 'text-gray-600']">
                        {{ value }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <p 
                v-else
                :class="[
                  'text-sm italic',
                  isDark ? 'text-gray-400' : 'text-gray-500'
                ]"
              >
                暂无标签
              </p>
            </div>

            <!-- 示例图 -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h3 
                  :class="[
                    'text-lg font-semibold',
                    isDark ? 'text-white' : 'text-gray-900'
                  ]"
                >
                  示例图
                </h3>
                <button
                  v-if="exampleCount > 0"
                  @click="openExamplesDialog"
                  :class="[
                    'text-sm px-3 py-1 rounded-lg transition-colors',
                    isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  ]"
                >
                  查看全部
                </button>
              </div>
              <div v-if="exampleCount > 0" class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div
                  v-for="(example, index) in actor.examples.slice(0, 6)"
                  :key="index"
                  :class="[
                    'relative rounded-lg overflow-hidden border cursor-pointer group',
                    isDark ? 'border-gray-600' : 'border-gray-200'
                  ]"
                  @click="openExamplesDialog"
                >
                  <img
                    :src="getExampleImageUrl(example)"
                    :alt="example.title || `示例图 ${index + 1}`"
                    class="w-full h-32 object-cover"
                    @error="handleImageError"
                  />
                  <div 
                    :class="[
                      'absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center',
                      isDark ? 'text-gray-300' : 'text-white'
                    ]"
                  >
                    <span class="text-xs opacity-0 group-hover:opacity-100">
                      {{ example.title || `示例图 ${index + 1}` }}
                    </span>
                  </div>
                </div>
              </div>
              <p 
                v-else
                :class="[
                  'text-sm italic',
                  isDark ? 'text-gray-400' : 'text-gray-500'
                ]"
              >
                暂无示例图
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '../stores/theme'
import { storeToRefs } from 'pinia'
import { PhotoIcon, TagIcon, PencilIcon, XMarkIcon } from '@heroicons/vue/24/outline'

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
}>()

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const exampleCount = computed(() => props.actor?.examples?.length || 0)
const tagCount = computed(() => Object.keys(props.actor?.tags || {}).length)

const getExampleImageUrl = (example: any) => {
  if (!example?.image_path || !props.actor) return ''
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:7864'
  return `${baseURL}/file/image/${props.actor.project_id}/${example.image_path}`
}

const handleImageError = () => {
  // 图片加载失败处理
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
  if (props.actor) {
    emit('generate', props.actor)
  }
}

const openExamplesDialog = () => {
  if (props.actor) {
    emit('examples', props.actor)
  }
}
</script>

