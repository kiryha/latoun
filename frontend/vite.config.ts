import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend API base can be overridden with VITE_API_BASE. When left empty
// the frontend calls "/api/..." and Vite proxies it to the FastAPI server so
// there are no CORS surprises during local development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
