import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    target: 'es2018',
    minify: 'terser',
    sourcemap: false,
    cssMinify: false,
    // 机器内存受限时用轻量压缩：仅去空白+改名，关闭高内存的 compress 优化
    terserOptions: { compress: false, mangle: true, format: { comments: false } },
  },
})
