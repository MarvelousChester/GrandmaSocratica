import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // The backend (uvicorn's default port) serves POST /api/simulate; proxying
    // keeps the browser same-origin so no CORS setup is needed in dev.
    proxy: { '/api': 'http://localhost:8000' },
  },
})
