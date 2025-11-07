import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/**
 * 隐私模式 Store
 * 
 * 管理全局隐私模式状态，用于控制是否显示图片。
 * 在模型管理和角色管理页面之间保持同步。
 */
export const usePrivacyStore = defineStore('privacy', () => {
  // 隐私模式状态
  const privacyMode = ref(false)
  
  // 从 localStorage 初始化
  const initPrivacyMode = () => {
    const saved = localStorage.getItem('privacyMode')
    if (saved !== null) {
      privacyMode.value = saved === 'true'
    }
  }
  
  // 监听隐私模式变化，保存到 localStorage
  watch(privacyMode, (newVal) => {
    localStorage.setItem('privacyMode', String(newVal))
  }, { immediate: false })
  
  // 切换隐私模式
  const togglePrivacyMode = () => {
    privacyMode.value = !privacyMode.value
  }
  
  // 初始化（在 store 创建时调用）
  initPrivacyMode()
  
  return {
    privacyMode,
    togglePrivacyMode,
    initPrivacyMode
  }
})

