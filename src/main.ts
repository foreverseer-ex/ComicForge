import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'

// Vue app 初始化
try {
  const app = createApp(App)
  
  app.use(pinia)
  app.use(router)
  
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
