// C5-REAL EXERGY CERTIFIED
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import wasm from 'vite-plugin-wasm'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    wasm()
  ],
  build: {
    // Enable aggressive tree‑shaking and manual chunking for vendor libs
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor';
          }
        }
      }
    },
    // Target modern browsers / Safari on macOS (Ω13)
    target: 'esnext'
  }
})
