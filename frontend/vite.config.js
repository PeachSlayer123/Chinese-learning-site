import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// /api gaat naar de FastAPI-backend, zodat de frontend relatieve paden kan gebruiken.
// Andere backend? Zet API_URL, bv. API_URL=http://localhost:8001 npm run dev
const proxy = { '/api': process.env.API_URL || 'http://localhost:8000' }

export default defineConfig({
  plugins: [svelte()],
  server: { port: 5173, proxy },
  preview: { port: 4173, proxy },
})
