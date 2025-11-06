/**
 * 移动端检测工具
 */

/**
 * 检测是否为移动设备
 */
export function isMobile(): boolean {
  if (typeof window === 'undefined') return false
  
  // 检测屏幕宽度（小于 768px 视为移动端）
  if (window.innerWidth < 768) return true
  
  // 检测 User Agent
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i
  return mobileRegex.test(userAgent)
}

/**
 * 响应式断点检测
 */
export function useBreakpoint() {
  if (typeof window === 'undefined') {
    return {
      isMobile: false,
      isTablet: false,
      isDesktop: true
    }
  }
  
  const width = window.innerWidth
  return {
    isMobile: width < 768,
    isTablet: width >= 768 && width < 1024,
    isDesktop: width >= 1024
  }
}

