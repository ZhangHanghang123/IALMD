import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 本地可设 VITE_API_TARGET 环境变量覆盖后端端口，默认 8002（IALMD 独立端口，与 ALMD 8000 并存）
const apiTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:8002'

export default defineConfig({
  plugins: [react()],
  base: '/ialmd/',
  server: {
    port: 5174,
    proxy: {
      '/ialmd/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ialmd/, ''),
      },
    },
  },
  build: {
    emptyOutDir: false,
  },
})
