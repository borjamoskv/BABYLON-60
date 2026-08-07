// C5-REAL EXERGY CERTIFIED
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import wasm from 'vite-plugin-wasm'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    wasm()
  ],
  resolve: {
    alias: {
      'cortex-wasm': path.resolve(__dirname, '../../../cortex-wasm/pkg/cortex_wasm.js')
    }
  },
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
