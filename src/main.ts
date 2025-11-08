import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { initImageCache } from './utils/imageCache'

// PWA 注册
import { registerSW } from 'virtual:pwa-register'

// Vue app 初始化
try {
  const app = createApp(App)
  
  app.use(pinia)
  app.use(router)
  
  // 初始化图片缓存（从 localStorage 读取）
  initImageCache()
  
  // 注册 PWA Service Worker
  registerSW({
    immediate: true,
    onNeedRefresh() {
      console.log('新的内容可用，请刷新页面')
    },
    onOfflineReady() {
      console.log('应用已准备好离线使用')
    },
  })
  
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
