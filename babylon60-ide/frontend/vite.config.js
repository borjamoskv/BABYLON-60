import { defineConfig } from 'vite';
export default defineConfig({
  root: '.',
  cacheDir: 'vite_cache',
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8060',
      '/ws': { target: 'ws://localhost:8060', ws: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
