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
  // 并在模块级缓存中缓存 blob URL（key 使用相对路径，确保缩略图与大图共用）
  try {
    const base = getApiBaseURL()
    if (imageUrl.startsWith(base) && (/\/draw\/.+\/image/.test(imageUrl) || /\/actor\/.+\/image/.test(imageUrl))) {
      const relativeUrl = imageUrl.replace(base, '')
      // 命中缓存直接返回
      const cached = protectedBlobCache.get(relativeUrl)
      if (cached) return cached
      // 请求并缓存
      const resp = await api.get(relativeUrl, { responseType: 'blob' })
      const blob: Blob = (resp as any)?.data ?? resp
      const blobUrl = URL.createObjectURL(blob)
      protectedBlobCache.set(relativeUrl, blobUrl)
      return blobUrl
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

// 模块级受保护图片缓存（相对路径 -> blob URL）
// 说明：用于共享 /actor/.../image 与 /draw/.../image 的 blob 以避免重复请求
const protectedBlobCache: Map<string, string> = new Map()
