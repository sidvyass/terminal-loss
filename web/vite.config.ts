import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, /api goes to `market-api` on its default port; in production that server also serves dist/.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
