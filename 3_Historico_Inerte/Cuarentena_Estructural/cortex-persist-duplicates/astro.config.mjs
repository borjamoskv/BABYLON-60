import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import cloudflare from '@astrojs/cloudflare';

// CORTEX Unified Substrate — v1.0.0 Configuration
export default defineConfig({
  output: 'server',
  adapter: cloudflare(),
  integrations: [
    react(),
  ],
  vite: {
    resolve: {
      preserveSymlinks: true
    },
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('three') || id.includes('@react-three')) return 'three-vendor';
              if (id.includes('framer-motion')) return 'framer-motion';
              if (id.includes('gsap')) return 'gsap';
              return 'vendor';
            }
          }
        }
      }
    }
  }
});
