import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: '.',
  base: '/',
  server: {
    port: 5173,
    host: true,
    cors: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})