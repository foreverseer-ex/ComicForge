/**
 * API 配置工具
 * 
 * 统一管理 API baseURL，支持开发环境代理和生产环境配置
 */

/**
 * 获取 API 基础 URL
 * 
 * 开发环境：返回 '/api'（通过 Vite 代理转发到后端）
 * 生产环境：使用环境变量 VITE_API_BASE_URL，如果没有则使用 '/api'（通过 nginx 代理）
 */
const TAURI_BACKEND_URL = 'http://127.0.0.1:7864'

function isTauriRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI__' in window
}

export function getApiBaseURL(): string {
  // 桌面端（Tauri）始终访问本地后端
  if (isTauriRuntime()) {
    return TAURI_BACKEND_URL
  }

  // 开发环境：使用相对路径，通过 Vite 代理转发
  if (import.meta.env.DEV) {
    return '/api'
  }

  // 生产环境：使用环境变量或默认值 '/api'（通过 nginx 代理）
  return import.meta.env.VITE_API_BASE_URL || '/api'
}

