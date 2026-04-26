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
    watch: null,
    hmr: false,
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
