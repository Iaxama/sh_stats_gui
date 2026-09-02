import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:5001',
      '/avatars': process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:5001',
    },
  },
  build: { outDir: 'dist' },
})
