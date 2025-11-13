/**
 * 图片缓存工具
 * 
 * 实现 LRU（最近最少使用）缓存策略，加速图片显示
 */

interface ImageCacheEntry {
  url: string
  blobUrl: string | null  // null 表示图片不存在（404）
  timestamp: number
}

class ImageCache {
  private cache: Map<string, ImageCacheEntry> = new Map()
  private maxSize: number = 100
  // 失败的图片缓存（记录已确认不存在的图片，避免重复请求）
  private failedCache: Map<string, number> = new Map() // Map<cacheKey, timestamp>
  private failedCacheExpiry: number = 24 * 60 * 60 * 1000 // 24小时过期

  constructor(maxSize: number = 100) {
    this.maxSize = maxSize
  }

  /**
   * 设置最大缓存数量
   */
  setMaxSize(size: number) {
    this.maxSize = size
    // 如果当前缓存超过新的大小，删除最旧的项
    while (this.cache.size >= this.maxSize) {
      this.evictOldest()
    }
  }

  /**
   * 获取模型示例图片 URL（通过 version_id + filename）
   * 
   * @param cacheKey 缓存 key（格式：model:versionId:filename）
   * @param versionId 模型版本 ID（必需）
   * @param filename 示例图片文件名（必需）
   */
  async get(cacheKey: string, versionId: number, filename: string): Promise<string | null> {
    if (!versionId || !filename) {
      return null
    }

    // 检查失败缓存（避免重复请求已确认不存在的图片）
    const failedTimestamp = this.failedCache.get(cacheKey)
    if (failedTimestamp) {
      const now = Date.now()
      // 如果失败缓存未过期，直接返回 null（不再请求）
      if (now - failedTimestamp < this.failedCacheExpiry) {
        return null
      } else {
        // 失败缓存已过期，清除它，允许重新尝试
        this.failedCache.delete(cacheKey)
      }
    }

    // 检查成功缓存
    const cached = this.cache.get(cacheKey)
    if (cached) {
      // 移动到末尾（标记为最近使用）
      this.cache.delete(cacheKey)
      this.cache.set(cacheKey, cached)
      return cached.blobUrl  // 可能是 null（已记录失败）
    }

    // 缓存未命中，从后端获取
    const blobUrl = await this.fetchImage(versionId, filename, cacheKey)
    
    // 记录到缓存（无论成功或失败）
    this.addToCache(cacheKey, blobUrl)
    
    return blobUrl
  }

  /**
   * 从后端获取图片（通过 version_id + filename）
   * 如果图片不存在（404），静默返回 null，不输出错误
   * 
   * 注意：浏览器控制台可能会显示 404 请求，这是浏览器的默认行为，无法完全阻止
   * 但代码中已经正确处理了这种情况，不会影响功能
   * 
   * @param versionId 模型版本 ID
   * @param filename 图片文件名
   * @param cacheKey 缓存 key（用于记录失败状态）
   */
  private async fetchImage(versionId: number, filename: string, cacheKey: string): Promise<string | null> {
    // 使用原始的 axios 实例，创建一个专门用于图片请求的实例，绕过响应拦截器
    const axios = (await import('axios')).default
    const { getApiBaseURL } = await import('./apiConfig')
    
    // 创建一个自定义的 axios 实例，专门用于图片请求，完全静默处理 404
    const imageAxios = axios.create({
      baseURL: getApiBaseURL(),
      timeout: 10000, // 10秒超时
      validateStatus: (status) => {
        // 允许所有 2xx 和 4xx 状态码（包括 404）
        // 这样 axios 不会抛出异常，浏览器控制台也不会显示为红色错误
        return status >= 200 && status < 500
      },
    })
    
    try {
      const response = await imageAxios.get('/model-meta/image', {
        params: {
          version_id: versionId,
          filename: filename
        },
        responseType: 'blob',
        // 静默处理错误，不输出到控制台
      })
      
      // 如果返回 404，静默返回 null（图片不存在是正常情况）
      // 注意：浏览器网络标签页仍会显示请求，但不会显示为错误
      // 记录到失败缓存，避免重复请求
      if (response.status === 404) {
        this.failedCache.set(cacheKey, Date.now())
        return null
      }
      
      // 如果返回其他 4xx 状态码，也返回 null（但不输出错误）
      // 不记录到失败缓存（可能只是临时错误）
      if (response.status >= 400) {
        return null
      }
      
      // 验证响应数据是否为有效的 blob
      if (!(response.data instanceof Blob)) {
        return null
      }
      
      // 创建 blob URL
      const blobUrl = URL.createObjectURL(response.data)
      return blobUrl
    } catch (error: any) {
      // 捕获所有错误（包括网络错误、取消请求等），静默返回 null
      // 不输出错误日志，因为图片不存在是正常情况
      // 注意：如果请求被取消或网络错误，axios 会抛出异常，但我们已经捕获了
      // 完全静默处理，不输出任何错误信息到控制台
      return null
    }
  }

  /**
   * 添加到缓存
   * @param cacheKey 缓存 key
   * @param blobUrl blob URL，如果为 null 表示图片不存在
   */
  private addToCache(cacheKey: string, blobUrl: string | null) {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      this.evictOldest()
    }

    // 添加到缓存（无论成功或失败都记录，避免重复请求）
    this.cache.set(cacheKey, {
      url: cacheKey,
      blobUrl: blobUrl,  // 可能是 null
      timestamp: Date.now()
    })
  }

  /**
   * 删除最旧的缓存项
   */
  private evictOldest() {
    if (this.cache.size === 0) return

    // 找到最旧的项（第一个）
    const oldestKey = this.cache.keys().next().value
    if (oldestKey) {
      const entry = this.cache.get(oldestKey)
      if (entry && entry.blobUrl) {
        // 只释放有效的 blob URL（失败项 blobUrl 为 null）
        URL.revokeObjectURL(entry.blobUrl)
      }
      this.cache.delete(oldestKey)
    }
  }
  
  /**
   * 清理过期的失败缓存
   */
  private cleanFailedCache() {
    const now = Date.now()
    for (const [key, timestamp] of this.failedCache.entries()) {
      if (now - timestamp >= this.failedCacheExpiry) {
        this.failedCache.delete(key)
      }
    }
  }

  /**
   * 清空缓存
   */
  clear() {
    // 释放所有 blob URL
    for (const entry of this.cache.values()) {
      if (entry.blobUrl) {
        URL.revokeObjectURL(entry.blobUrl)
      }
    }
    this.cache.clear()
    this.failedCache.clear()
  }
  
  /**
   * 清理过期的失败缓存（定期调用）
   */
  cleanup() {
    this.cleanFailedCache()
  }

  /**
   * 获取缓存大小
   */
  get size(): number {
    return this.cache.size
  }
}

// 全局图片缓存实例
export const imageCache = new ImageCache(100)

// 初始化：从 localStorage 加载缓存大小
export function initImageCache() {
  const saved = localStorage.getItem('imageCacheSize')
  if (saved !== null) {
    const value = parseInt(saved)
    if (!isNaN(value) && value >= 10 && value <= 1000) {
      imageCache.setMaxSize(value)
    }
  }
  // 如果没有保存的值，使用默认值 100
}

// 监听设置变化
export function updateImageCacheSize(size: number) {
  imageCache.setMaxSize(size)
  localStorage.setItem('imageCacheSize', String(size))
}

