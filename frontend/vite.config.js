import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const frontendPort = parseInt(env.FRONTEND_PORT || env.VITE_FRONTEND_PORT || '5174', 10)
  const backendPort  = parseInt(env.BACKEND_PORT  || env.VITE_BACKEND_PORT  || '8091', 10)

  return {
    plugins: [vue(), VueDevTools()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
    },
    server: {
      host: '0.0.0.0',
      port: frontendPort,
      proxy: {
        '/api': `http://localhost:${backendPort}`
      }
    }
  }
})
