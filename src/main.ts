import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { initImageCache } from './utils/imageCache'

// Vue app 初始化
(async () => {
  try {
    const app = createApp(App)
    
    app.use(pinia)
    app.use(router)
    
    // 初始化图片缓存（从 localStorage 读取）
    initImageCache()
    
    // 注册 PWA Service Worker（如果可用）
    try {
      // @ts-ignore - virtual:pwa-register 是 Vite 插件生成的虚拟模块
      const { registerSW } = await import('virtual:pwa-register')
      registerSW({
        immediate: true,
        onNeedRefresh() {
          console.log('新的内容可用，请刷新页面')
        },
        onOfflineReady() {
          console.log('应用已准备好离线使用')
        },
      })
    } catch (e) {
      // PWA 模块不可用时忽略
      console.warn('PWA module not available:', e)
    }
    
    app.mount('#app')
  } catch (error) {
    console.error('Error mounting Vue app:', error)
    // 显示错误信息到页面
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.innerHTML = `
        <div style="padding: 20px; color: red;">
          <h1>Error Loading Application</h1>
          <pre>${error instanceof Error ? error.message : String(error)}</pre>
          <p>Check browser console for details.</p>
        </div>
      `
    }
  }
})()
