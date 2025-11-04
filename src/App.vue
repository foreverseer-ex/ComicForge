<template>
  <div 
    :class="[
      'min-h-screen transition-colors duration-300',
      isDark ? 'bg-gray-900' : 'bg-gray-50'
    ]"
  >
    <Navigation />
    
    <!-- 主内容区域 -->
    <main 
      :class="[
        'ml-56 transition-all duration-300',
        isDark ? 'text-gray-100' : 'text-gray-900'
      ]"
    >
      <div class="p-8">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Navigation from './components/Navigation.vue'
import { useThemeStore } from './stores/theme'
import { useProjectStore } from './stores/project'
import { storeToRefs } from 'pinia'

const themeStore = useThemeStore()
const { isDark } = storeToRefs(themeStore)

const projectStore = useProjectStore()

onMounted(() => {
  // 初始化主题
  themeStore.loadTheme()
  // 初始化项目 store
  projectStore.init()
  projectStore.loadProjects()
})
</script>
