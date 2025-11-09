/**
 * 获取图片 URL 的工具函数
 * 
 * 处理 file:// URL 和远程 URL，统一转换为可通过 API 访问的 URL
 */
import { imageCache } from './imageCache'
import api from '../api'
import { getApiBaseURL } from './apiConfig'

/**
 * 获取图片 URL（支持缓存）
 * 
 * @param imageUrl 原始图片 URL（可能是 file:// URL 或远程 URL）
 * @param versionId 模型版本 ID（可选，用于模型示例图片）
 * @param filename 示例图片文件名（可选，用于模型示例图片）
 * @returns Promise<string> 可用的图片 URL（blob URL 或原始 URL）
 */
export async function getImageUrl(
  imageUrl: string | null | undefined,
  versionId?: number,
  filename?: string
): Promise<string | null> {
  if (!imageUrl) {
    return null
  }

  // 如果是受保护的后端 API 图片（/draw/.../image 或 /actor/.../image），使用带鉴权的请求获取 blob
  try {
    const base = getApiBaseURL()
    if (imageUrl.startsWith(base) && (/\/draw\/.+\/image/.test(imageUrl) || /\/actor\/.+\/image/.test(imageUrl))) {
      // 去掉 base，改用 axios 实例以便自动注入 Authorization
      const relativeUrl = imageUrl.replace(base, '')
      const resp = await api.get(relativeUrl, { responseType: 'blob' })
      return URL.createObjectURL(resp as any)
    }
  } catch (e) {
    console.error('获取受保护图片失败:', imageUrl, e)
    // 失败则回退为原始 URL（可能仍可匿名访问，或由 <img> 自行失败）
  }

  // 如果是远程公开 URL，直接返回
  if (!imageUrl.startsWith('file://')) {
    return imageUrl
  }

  // 如果是本地 file:// URL，使用缓存获取
  try {
    return await imageCache.get(imageUrl, versionId, filename)
  } catch (error) {
    console.error('获取图片失败:', imageUrl, error)
    return null
  }
}
