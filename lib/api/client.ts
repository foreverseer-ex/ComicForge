/**
 * API 客户端封装
 * 统一处理请求、响应、错误处理和 Token 注入
 */

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

class ApiClient {
  private getBaseURL(): string {
    if (typeof window === 'undefined') return '/api'
    // 在浏览器环境中，使用相对路径
    return '/api'
  }

  /**
   * 获取认证 Token
   */
  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    const authStorage = localStorage.getItem('auth-storage')
    if (!authStorage) return null
    try {
      const auth = JSON.parse(authStorage)
      return auth.state?.token || null
    } catch {
      return null
    }
  }

  /**
   * 处理响应
   */
  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const data = await response.json()
    
    if (!response.ok) {
      // 401 未授权，清除 token 并跳转登录
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth-storage')
          window.location.href = '/login'
        }
        return { success: false, error: '未授权，请重新登录' }
      }
      return { success: false, error: data.error || '请求失败' }
    }

    return data as ApiResponse<T>
  }

  /**
   * 构建 URL
   */
  private buildURL(path: string, params?: Record<string, string | number | boolean>): string {
    const baseURL = this.getBaseURL()
    // 确保 path 以 / 开头
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    // 构建完整路径
    const fullPath = `${baseURL}${normalizedPath}`
    
    // 如果有参数，添加到 URL
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value))
      })
      return `${fullPath}?${searchParams.toString()}`
    }
    
    return fullPath
  }

  /**
   * GET 请求
   */
  async get<T>(path: string, params?: Record<string, string | number | boolean>): Promise<ApiResponse<T>> {
    const url = this.buildURL(path, params)
    const token = this.getToken()
    const headers: HeadersInit = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : '网络错误' }
    }
  }

  /**
   * POST 请求
   */
  async post<T>(path: string, body?: any, isFormData = false): Promise<ApiResponse<T>> {
    const url = this.buildURL(path)
    const token = this.getToken()
    const headers: HeadersInit = {}

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    if (!isFormData && body) {
      headers['Content-Type'] = 'application/json'
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: isFormData ? body : (body ? JSON.stringify(body) : undefined),
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : '网络错误' }
    }
  }

  /**
   * PUT 请求
   */
  async put<T>(path: string, body?: any): Promise<ApiResponse<T>> {
    const url = this.buildURL(path)
    const token = this.getToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        method: 'PUT',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : '网络错误' }
    }
  }

  /**
   * DELETE 请求
   */
  async delete<T>(path: string): Promise<ApiResponse<T>> {
    const url = this.buildURL(path)
    const token = this.getToken()
    const headers: HeadersInit = {}

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers,
      })
      return this.handleResponse<T>(response)
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : '网络错误' }
    }
  }
}

export const apiClient = new ApiClient()
