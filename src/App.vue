<template>
  <div 
    :class="[
      'min-h-screen transition-colors duration-300 relative',
      isDark ? 'bg-gray-900' : 'bg-gray-50'
    ]"
  >
    <!-- 已登录：显示导航 + 主内容 -->
    <template v-if="isAuthenticated">
      <Navigation />
      <!-- 主内容区域 -->
      <main 
        :class="[
          'transition-all duration-300 relative',
          isDark ? 'text-gray-100' : 'text-gray-900'
        ]"
        :style="{ marginLeft: `${navigationWidth}px` }"
      >
        <div class="p-8">
          <router-view />
        </div>
      </main>
    </template>

    <!-- 未登录：仅显示路由内容（登录页） -->
    <template v-else>
      <main :class="[ 'min-h-screen flex items-center justify-center', isDark ? 'text-gray-100' : 'text-gray-900' ]">
        <router-view />
      </main>
    </template>

    <!-- 服务端未连接遮罩层（仅登录后显示；检查进行中不显示，避免登录后闪现） -->
    <div 
      v-if="isAuthenticated && !isConnected && !isChecking"
      class="fixed inset-0 z-50 flex items-center justify-center"
      :class="isDark ? 'bg-gray-900/80 backdrop-blur-sm' : 'bg-gray-50/80 backdrop-blur-sm'"
    >
      <div 
        class="rounded-lg p-8 max-w-md mx-4 shadow-2xl border-2"
        :class="isDark ? 'bg-gray-800 border-red-500' : 'bg-white border-red-500'"
      >
        <div class="flex flex-col items-center text-center">
          <div class="w-16 h-16 rounded-full flex items-center justify-center mb-4"
               :class="isDark ? 'bg-red-900/30' : 'bg-red-50'">
            <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 
            class="text-xl font-bold mb-2"
            :class="isDark ? 'text-white' : 'text-gray-900'"
          >
            服务端未连接
          </h2>
          <p 
            class="text-sm mb-4"
            :class="isDark ? 'text-gray-400' : 'text-gray-600'"
          >
            无法连接到后端服务，请确保后端服务正在运行。
          </p>
          <p 
            class="text-xs"
            :class="isDark ? 'text-gray-500' : 'text-gray-500'"
          >
            后端地址：{{ apiBaseUrl }}
          </p>
          <button
            @click="checkConnection"
            :class="[
              'mt-4 px-4 py-2 rounded-lg transition-colors text-sm font-medium',
              isDark
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            ]"
          >
            重新检查连接
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import Navigation from './components/Navigation.vue'
import { useThemeStore } from './stores/theme'
import { useProjectStore } from './stores/project'
import { useConnectionStore } from './stores/connection'
import { useNavigationStore } from './stores/navigation'
import { storeToRefs } from 'pinia'
import { getApiBaseURL } from './utils/apiConfig'
import { useAuthStore } from './stores/auth'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()

const connectionStore = useConnectionStore()
const { isConnected, isChecking } = storeToRefs(connectionStore)
const { checkConnection } = connectionStore

const navigationStore = useNavigationStore()
const { width: navigationWidth } = storeToRefs(navigationStore)

const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

// 获取 API 基础 URL
const apiBaseUrl = computed(() => {
  return getApiBaseURL()
})

onMounted(() => {
  // 初始化主题
  themeStore.loadTheme()
})

// 登录后再初始化项目与连接检测
watch(isAuthenticated, (authed) => {
  if (authed) {
    checkConnection()
    projectStore.init()
    projectStore.loadProjects()
  }
}, { immediate: false })
</script>
