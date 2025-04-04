import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Add the base configuration
  base: 'https://staging.arcanedm.com:8443/static/build/', // Ensures assets are loaded relative to this path
  build: {
    // Output directory relative to the frontend directory
    outDir: path.resolve(__dirname, '../app/static/build'), 
    // Optional: Clean the output directory before building
    emptyOutDir: true, 
    // Optional: Generate manifest for server integration (if needed later)
    manifest: true, 
    rollupOptions: {
         // Ensure entry point is correct (usually src/index.js or src/main.jsx)
         input: path.resolve(__dirname, 'src/index.jsx'), 
    }
  }
})