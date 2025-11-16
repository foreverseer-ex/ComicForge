/**
 * 文字缓存工具
 * 
 * 实现 LRU（最近最少使用）缓存策略，加速段落内容显示
 */

interface TextCacheEntry {
  key: string
  paragraphIndex: number
  paragraphContent: any // 段落内容对象
  timestamp: number
}

class TextCache {
  private cache: Map<string, TextCacheEntry> = new Map()
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
   * 获取段落内容和索引（通过 project_id + chapter + line）
   * 
   * @param cacheKey 缓存 key（格式：text:projectId:chapter:line）
   * @param projectId 项目 ID（必需）
   * @param chapter 章节索引（必需）
   * @param line 行号（必需）
   * @param fetchFn 获取数据的函数（缓存未命中时调用）
   */
  async get(
    cacheKey: string,
    projectId: string,
    chapter: number,
    line: number,
    fetchFn: (projectId: string, chapter: number, line: number) => Promise<{ paragraphIndex: number, paragraphContent: any }>
  ): Promise<{ paragraphIndex: number, paragraphContent: any } | null> {
    if (!projectId || chapter === null || chapter === undefined || line === null || line === undefined) {
      return null
    }

    // 检查缓存
    const cached = this.cache.get(cacheKey)
    if (cached) {
      // 移动到末尾（标记为最近使用）
      this.cache.delete(cacheKey)
      this.cache.set(cacheKey, cached)
      return {
        paragraphIndex: cached.paragraphIndex,
        paragraphContent: cached.paragraphContent
      }
    }

    // 缓存未命中，从后端获取
    try {
      const data = await fetchFn(projectId, chapter, line)
      
      // 记录到缓存
      this.addToCache(cacheKey, data.paragraphIndex, data.paragraphContent)
      
      return data
    } catch (error) {
      console.error('获取段落内容失败:', error)
      return null
    }
  }

  /**
   * 添加到缓存
   * @param cacheKey 缓存 key
   * @param paragraphIndex 段落索引
   * @param paragraphContent 段落内容
   */
  private addToCache(cacheKey: string, paragraphIndex: number, paragraphContent: any) {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      this.evictOldest()
    }

    // 添加到缓存
    this.cache.set(cacheKey, {
      key: cacheKey,
      paragraphIndex,
      paragraphContent,
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
      this.cache.delete(oldestKey)
    }
  }

  /**
   * 删除指定的缓存项
   * @param cacheKey 缓存 key（格式：text:projectId:chapter:line 或 text:projectId:*）
   */
  delete(cacheKey: string) {
    if (cacheKey.endsWith(':*')) {
      // 删除某个项目的所有缓存
      const prefix = cacheKey.slice(0, -2)
      for (const key of this.cache.keys()) {
        if (key.startsWith(prefix)) {
          this.cache.delete(key)
        }
      }
    } else {
      // 删除指定的缓存项
      this.cache.delete(cacheKey)
    }
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache.clear()
  }

  /**
   * 获取缓存大小
   */
  get size(): number {
    return this.cache.size
  }

  /**
   * 获取所有缓存条目
   */
  getAllEntries(): Array<{ key: string, paragraphIndex: number, paragraphContent: any, timestamp: number }> {
    return Array.from(this.cache.values())
  }

  /**
   * 获取缓存的键列表
   */
  getKeys(): string[] {
    return Array.from(this.cache.keys())
  }
}

// 全局文字缓存实例
export const textCache = new TextCache(100)

// 初始化：从 localStorage 加载缓存大小
export function initTextCache() {
  const saved = localStorage.getItem('textCacheSize')
  if (saved !== null) {
    const value = parseInt(saved)
    if (!isNaN(value) && value >= 10 && value <= 1000) {
      textCache.setMaxSize(value)
    }
  }
}

// 监听设置变化
export function updateTextCacheSize(size: number) {
  textCache.setMaxSize(size)
  localStorage.setItem('textCacheSize', String(size))
}

