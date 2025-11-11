/**
 * 图片缓存工具
 * 
 * 实现 LRU（最近最少使用）缓存策略，加速图片显示
 */

interface ImageCacheEntry {
  url: string
  blobUrl: string
  timestamp: number
}

class ImageCache {
  private cache: Map<string, ImageCacheEntry> = new Map()
  private maxSize: number = 100

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

    // 检查缓存
    const cached = this.cache.get(cacheKey)
    if (cached) {
      // 移动到末尾（标记为最近使用）
      this.cache.delete(cacheKey)
      this.cache.set(cacheKey, cached)
      return cached.blobUrl
    }

    // 缓存未命中，从后端获取
    const blobUrl = await this.fetchImage(versionId, filename)
    
    // 如果获取成功，添加到缓存
    if (blobUrl) {
      this.addToCache(cacheKey, blobUrl)
    }
    
    return blobUrl
  }

  /**
   * 从后端获取图片（通过 version_id + filename）
   * 如果图片不存在（404），静默返回 null，不输出错误
   * 
   * 注意：浏览器控制台可能会显示 404 请求，这是浏览器的默认行为，无法完全阻止
   * 但代码中已经正确处理了这种情况，不会影响功能
   */
  private async fetchImage(versionId: number, filename: string): Promise<string | null> {
    // 使用原始的 axios 实例，绕过响应拦截器，避免触发全局错误处理
    const axios = (await import('axios')).default
    const { getApiBaseURL } = await import('./apiConfig')
    
    try {
      const response = await axios.get('/model-meta/image', {
        baseURL: getApiBaseURL(),
        params: {
          version_id: versionId,
          filename: filename
        },
        responseType: 'blob',
        // 设置 validateStatus，让 404 和其他 4xx 状态码不被视为错误
        // 这样 axios 不会抛出异常，浏览器控制台也不会显示为红色错误
        validateStatus: (status) => {
          // 允许 2xx（成功）和 4xx（客户端错误，包括 404）
          // 不允许 5xx（服务器错误）和网络错误
          return status >= 200 && status < 500
        },
        // 不输出错误到控制台
        // 注意：浏览器开发工具的网络标签页仍会显示请求，但不会显示为错误
      })
      
      // 如果返回 404，静默返回 null（图片不存在是正常情况）
      if (response.status === 404) {
        return null
      }
      
      // 如果返回其他 4xx 状态码，也返回 null（但不输出错误）
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
      if (error.name === 'CanceledError' || error.code === 'ECONNABORTED') {
        // 请求被取消，静默返回 null
        return null
      }
      
      // 其他错误（网络错误等），也静默返回 null
      return null
    }
  }

  /**
   * 添加到缓存
   */
  private addToCache(imageUrl: string, blobUrl: string) {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      this.evictOldest()
    }

    // 添加到缓存
    this.cache.set(imageUrl, {
      url: imageUrl,
      blobUrl: blobUrl,
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
      if (entry) {
        // 释放 blob URL
        URL.revokeObjectURL(entry.blobUrl)
      }
      this.cache.delete(oldestKey)
    }
  }

  /**
   * 清空缓存
   */
  clear() {
    // 释放所有 blob URL
    for (const entry of this.cache.values()) {
      URL.revokeObjectURL(entry.blobUrl)
    }
    this.cache.clear()
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

