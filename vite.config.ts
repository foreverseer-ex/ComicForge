import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 7863,
    host: '0.0.0.0', // 监听所有网络接口，允许局域网访问
    proxy: {
      // 将所有 /api 开头的请求代理到后端
      '/api': {
        target: 'http://127.0.0.1:7864',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''), // 去掉 /api 前缀
      },
    },
  },
})
