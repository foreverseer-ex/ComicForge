/**
 * 获取图片 URL 的工具函数
 * 
 * 处理 file:// URL 和远程 URL，统一转换为可通过 API 访问的 URL
 */
import { imageCache } from './imageCache'

/**
 * 获取图片 URL（支持缓存）
 * 
 * @param imageUrl 原始图片 URL（可能是 file:// URL）
 * @returns Promise<string> 可用的图片 URL（blob URL 或原始 URL）
 */
export async function getImageUrl(imageUrl: string | null | undefined): Promise<string | null> {
  if (!imageUrl) {
    return null
  }

  // 如果是远程 URL，直接返回
  if (!imageUrl.startsWith('file://')) {
    return imageUrl
  }

  // 如果是本地 file:// URL，使用缓存获取
  try {
    return await imageCache.get(imageUrl)
  } catch (error) {
    console.error('获取图片失败:', imageUrl, error)
    return null
  }
}

