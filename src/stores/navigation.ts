import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNavigationStore = defineStore('navigation', () => {
  // 导航栏折叠状态
  const savedCollapsed = localStorage.getItem('navigationCollapsed')
  const isCollapsed = ref<boolean>(savedCollapsed === 'true')
  
  const toggleCollapse = () => {
    isCollapsed.value = !isCollapsed.value
    localStorage.setItem('navigationCollapsed', String(isCollapsed.value))
  }
  
  // 导航栏宽度（px）
  const width = computed(() => isCollapsed.value ? 64 : 192)
  
  return {
    isCollapsed,
    toggleCollapse,
    width
  }
})

