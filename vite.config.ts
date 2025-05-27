import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve, join } from 'path'
import { writeFileSync } from 'fs'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'write-port',
      configureServer(server) {
        // Hook into the server listen event
        const originalListen = server.listen.bind(server);
        server.listen = async (...args) => {
          const result = await originalListen(...args);
          
          // Write port file after server starts
          setTimeout(() => {
            const address = server.httpServer?.address();
            if (address && typeof address === 'object') {
              const actualPort = address.port;
              const portFile = join(__dirname, '.vite-port');
              const portData = {
                port: actualPort,
                timestamp: Date.now(),
                url: `http://localhost:${actualPort}`,
                pid: process.pid
              };
              
              try {
                writeFileSync(portFile, JSON.stringify(portData, null, 2));
                console.log(`📝 Vite server listening on port ${actualPort}, written to .vite-port file`);
              } catch (error) {
                console.error('❌ Failed to write port file:', error);
              }
            }
          }, 100); // Small delay to ensure server is fully started
          
          return result;
        };
        
        // Add endpoint to get current port info
        server.middlewares.use('/__port', (req, res) => {
          const address = server.httpServer?.address();
          const port = typeof address === 'object' && address ? address.port : server.config.server.port || 3001;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ port, url: `http://localhost:${port}` }));
        });
      }
    }
  ],
  base: './',
  build: {
    outDir: 'dist/renderer',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3001,
    strictPort: false, // Allow port auto-increment
    host: 'localhost'
  },
}) 