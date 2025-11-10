import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

const TOKEN_KEY = 'auth_token'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const user = ref<any | null>(null)
  const isInitialized = ref(false) // 标记是否已初始化

  const isAuthenticated = computed(() => !!accessToken.value)

  function setToken(token: string | null) {
    accessToken.value = token
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function setUser(u: any | null) {
    user.value = u
  }

  function logout() {
    accessToken.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  // 初始化：从 localStorage 恢复 token 并验证
  async function initialize() {
    if (isInitialized.value) return
    
    const savedToken = localStorage.getItem(TOKEN_KEY)
    if (savedToken) {
      try {
        // 验证 token 是否有效
        accessToken.value = savedToken
        const response = await api.get('/auth/me')
        user.value = response  // API 拦截器已经返回了 response.data
        isInitialized.value = true
      } catch (error) {
        // token 无效，清除
        console.error('Token 验证失败，清除登录状态:', error)
        logout()
        isInitialized.value = true
      }
    } else {
      isInitialized.value = true
    }
  }

  // 登录后调用，设置 token 和用户信息，并标记已初始化
  async function login(token: string) {
    setToken(token)
    try {
      const response = await api.get('/auth/me')
      user.value = response  // API 拦截器已经返回了 response.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
    isInitialized.value = true
  }

  return { 
    accessToken, 
    user, 
    isAuthenticated, 
    isInitialized,
    setToken, 
    setUser, 
    logout,
    initialize,
    login
  }
})
