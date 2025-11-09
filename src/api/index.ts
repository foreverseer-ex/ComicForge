import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { getApiBaseURL } from '../utils/apiConfig'
import router from '../router'

const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 允许跨域携带 Cookie（用于 /auth/refresh）
api.defaults.withCredentials = true

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 对于 FormData，不要设置 Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    // 注入 Bearer 访问令牌
    try {
      const auth = useAuthStore()
      if (auth.accessToken) {
        config.headers = config.headers || {}
        ;(config.headers as any)['Authorization'] = `Bearer ${auth.accessToken}`
      }
    } catch {}
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const original = error.config
    const status = error?.response?.status
    if (status === 401) {
      const auth = useAuthStore()
      const isRefresh = (original?.url?.includes('/auth/refresh'))
      const isLogin = (original?.url?.includes('/auth/login'))
      // 仅当已有 accessToken 且不是刷新/登录请求时尝试刷新
      if (auth.accessToken && !isRefresh && !isLogin && !original._retried) {
        original._retried = true
        try {
          const refreshResp = await api.post<{ access_token: string; expires_in: number }>('/auth/refresh') as any
          const access = (refreshResp?.access_token) ?? (refreshResp?.data?.access_token)
          if (access) {
            auth.setToken(access)
            original.headers = original.headers || {}
            original.headers['Authorization'] = `Bearer ${access}`
            return api(original)
          }
        } catch {}
      }
      // 刷新失败或无 token：登出并跳转登录
      auth.logout()
      if (router.currentRoute.value.name !== 'Login') {
        router.replace({ name: 'Login' })
      }
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api

