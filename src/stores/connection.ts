import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useConnectionStore = defineStore('connection', () => {
  // 连接状态
  const isConnected = ref<boolean>(false)
  // 是否正在检查连接
  const isChecking = ref<boolean>(false)
  // 检查间隔（毫秒）
  const checkInterval = ref<number>(5000)
  // 定时器 ID
  let intervalId: number | null = null

  // 检查连接状态
  const checkConnection = async () => {
    if (isChecking.value) return
    
    isChecking.value = true
    try {
      await api.get('/health', { timeout: 3000 })
      isConnected.value = true
    } catch (error) {
      isConnected.value = false
    } finally {
      isChecking.value = false
    }
  }

  // 开始定期检查
  const startChecking = () => {
    // 立即检查一次
    checkConnection()
    
    // 清除之前的定时器
    if (intervalId !== null) {
      clearInterval(intervalId)
    }
    
    // 设置定期检查
    intervalId = window.setInterval(() => {
      checkConnection()
    }, checkInterval.value)
  }

  // 停止检查
  const stopChecking = () => {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  return {
    isConnected,
    isChecking,
    checkConnection,
    startChecking,
    stopChecking
  }
})

