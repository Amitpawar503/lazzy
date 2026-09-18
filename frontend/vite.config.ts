import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy so the frontend can call the backend at /api without CORS pain.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
