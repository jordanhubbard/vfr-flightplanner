import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: parseInt(process.env.REACT_DEV_PORT || '3000'),
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.PORT || '8080'}`,
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: `http://localhost:${process.env.PORT || '8080'}`,
        changeOrigin: true,
        secure: false,
      }
    },
  },
  build: {
    outDir: '../app/static/dist',
    emptyOutDir: true,
    sourcemap: true,
  },
})
