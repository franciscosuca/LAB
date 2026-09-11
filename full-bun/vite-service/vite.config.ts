import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { apiPlugin } from "./api-plugin.ts";

export default defineConfig({
  plugins: [react(), apiPlugin()],
  server: {
    port: 5173,
  },
  preview: {
    port: 4173,
  },
});
