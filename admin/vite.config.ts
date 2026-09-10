import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../core/app/web/static/admin',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  }
} as any)
