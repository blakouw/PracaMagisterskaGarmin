import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: false,
        secure: false
      }
    }
  },
  preview: {
    host: '127.0.0.1',
    port: 5173
  },
  resolve: {
    preserveSymlinks: true
  },
  test: {
    globals: true,
    setupFiles: './src/test/setup.ts',
    environment: 'jsdom',
    pool: 'threads'
  }
});
