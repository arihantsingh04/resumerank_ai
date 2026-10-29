import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The dev server proxies /api to the FastAPI backend so the SPA and API share one origin.
// That avoids CORS in development. API_TARGET overrides the backend address (e.g. another port).
const env = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env ?? {};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Allow temporary Cloudflare quick-tunnel URLs (scripts/share.ps1) for testing on other devices.
    allowedHosts: [".trycloudflare.com"],
    proxy: {
      "/api": { target: env.API_TARGET ?? "http://127.0.0.1:8000", changeOrigin: false },
    },
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        // Separate long-lived vendor chunks so app updates don't re-download the libraries.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom", "@tanstack/react-query"],
          gsap: ["gsap", "@gsap/react"],
          motion: ["motion"],
        },
      },
    },
  },
});
