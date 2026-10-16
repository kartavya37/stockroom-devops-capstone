import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The development server sends every /api request to the backend.
// In a container, Nginx does this work instead.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
