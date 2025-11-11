/**
 * 获取图片 URL 的工具函数
 * 
 * 对于模型示例图片，只通过 version_id + filename 获取本地文件
 * URL 字段仅用于保存原始远程URL，不用于获取图片
 */
import { imageCache } from './imageCache'

/**
 * 获取模型示例图片 URL（支持缓存）
 * 
 * 注意：获取模型图片的唯一途径是依靠 filename（通过 version_id + filename）
 * URL 字段仅用于保存原始远程URL，不用于判断或获取图片
 * 
 * @param versionId 模型版本 ID（必需）
 * @param filename 示例图片文件名（必需）
 * @returns Promise<string | null> 可用的图片 URL（blob URL），如果文件不存在返回 null
 */
export async function getImageUrl(
  versionId: number,
  filename: string
): Promise<string | null> {
  if (!versionId || !filename) {
    return null
  }

  // 构建缓存 key
  const cacheKey = `model:${versionId}:${filename}`
  // imageCache.get 已经处理了所有错误（包括 404），不会抛出错误
  return await imageCache.get(cacheKey, versionId, filename)
}

