// C5-REAL EXERGY CERTIFIED
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
    target: 'esnext',
    // Minify with esbuild for speed & small bundle
    minify: 'esbuild'
  }
})
