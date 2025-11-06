import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { isMobile } from '../utils/device'

export const useNavigationStore = defineStore('navigation', () => {
  // 导航栏折叠状态
  // 如果是移动端，默认折叠；否则从 localStorage 读取
  const savedCollapsed = localStorage.getItem('navigationCollapsed')
  const isCollapsed = ref<boolean>(
    savedCollapsed === null 
      ? isMobile()  // 如果没有保存的状态，移动端默认折叠
      : savedCollapsed === 'true'
  )
  
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

