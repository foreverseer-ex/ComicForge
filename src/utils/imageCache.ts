/**
 * 图片缓存工具
 * 
 * 实现 LRU（最近最少使用）缓存策略，加速图片显示
 */
import api from '../api'

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
   * 获取缓存的图片 URL
   */
  async get(imageUrl: string): Promise<string> {
    // 如果是远程 URL，直接返回
    if (!imageUrl.startsWith('file://')) {
      return imageUrl
    }

    // 检查缓存
    const cached = this.cache.get(imageUrl)
    if (cached) {
      // 移动到末尾（标记为最近使用）
      this.cache.delete(imageUrl)
      this.cache.set(imageUrl, cached)
      return cached.blobUrl
    }

    // 缓存未命中，从后端获取
    try {
      const blobUrl = await this.fetchImage(imageUrl)
      
      // 添加到缓存
      this.addToCache(imageUrl, blobUrl)
      
      return blobUrl
    } catch (error) {
      console.error('获取图片失败:', imageUrl, error)
      throw error
    }
  }

  /**
   * 从后端获取图片
   */
  private async fetchImage(imageUrl: string): Promise<string> {
    // 使用原始的 axios 实例，绕过响应拦截器
    const axios = (await import('axios')).default
    
    const response = await axios.get('/model-meta/image', {
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:7864',
      params: { image_url: imageUrl },
      responseType: 'blob'
    })
    
    // 创建 blob URL
    const blobUrl = URL.createObjectURL(response.data)
    return blobUrl
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

// 初始化：从设置加载缓存大小
export async function initImageCache() {
  try {
    const settings = await api.get('/settings/frontend')
    imageCache.setMaxSize(settings.image_cache_size || 100)
  } catch (error) {
    console.warn('加载图片缓存设置失败，使用默认值:', error)
  }
}

// 监听设置变化
export async function updateImageCacheSize(size: number) {
  imageCache.setMaxSize(size)
}

