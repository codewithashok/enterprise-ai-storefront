import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Same-origin /api in dev, mirroring CloudFront's /api/* → backend routing in prod
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
