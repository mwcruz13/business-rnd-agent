import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      include: '**/*.{jsx,tsx,js,ts}',
    }),
  ],
  server: {
    port: 8080,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      host: 'localhost',
      port: 8501,
    },
    proxy: {
      '/api': {
        target: 'http://bmi-backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    target: 'esnext',
    outDir: 'dist',
  },
});
