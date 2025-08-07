import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'https://6d3ff40450cc.ngrok-free.app', // меняется на твой backend ngrok-домен
        changeOrigin: true,
        secure: false,
      }
    },
    hmr: {
      clientPort: 443,
    },
    allowedHosts: [
      '77575e4d233f.ngrok-free.app', // ⚠️ Меняй каждый раз на актуальный ngrok-домен
    ],
  },
})