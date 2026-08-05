import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  root: path.resolve(__dirname, '../frontend'),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../frontend/src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            proxyRes.headers['X-Accel-Buffering'] = 'no'
            proxyRes.headers['Cache-Control'] = 'no-cache'
          })
        },
      },
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../frontend/dist'),
    emptyOutDir: true,
  },
})