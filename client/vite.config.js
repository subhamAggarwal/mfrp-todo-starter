import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Preview-proxy awareness
// -----------------------
// When this project runs inside the hiretriple IDE container, the backend
// exposes the Vite dev server via a path-prefixed reverse proxy at
//   http://<backend>/api/ide/<sid>/preview/5173/
// The backend injects that prefix as PREVIEW_BASE_5173 at container startup.
//
// Without `base` set to the prefix, Vite emits root-relative URLs
// (`<script src="/src/main.jsx">`) which escape the proxy mount and 404.
const PREVIEW_BASE = process.env.PREVIEW_BASE_5173 || '/';

// Backend-API prefix in the CLIENT's URL space. Must account for `base`.
const API_PREFIX_IN_CLIENT_URL = `${PREVIEW_BASE.replace(/\/$/, '')}/api`;
const API_PROXY_KEY = `^${API_PREFIX_IN_CLIENT_URL}(/|$)`;

export default defineConfig({
    plugins: [react()],
    base: PREVIEW_BASE,
    server: {
        port: 5173,
        host: '0.0.0.0',
        strictPort: true,
        proxy: {
            [API_PROXY_KEY]: {
                target: 'http://localhost:3000',
                changeOrigin: true,
                rewrite: (path) => path.replace(API_PREFIX_IN_CLIENT_URL, '/api'),
            },
        },
    },
});
