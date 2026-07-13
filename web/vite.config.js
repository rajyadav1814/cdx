import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import dotenv from 'dotenv'

dotenv.config({ path: path.resolve(__dirname, './.env')})

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `${process.env.VITE_BACKEND_URL}`,
        changeOrigin: true,
      }
    }
  },
  build: { outDir: 'dist' }
})
