import path from "path";
import { defineConfig } from "vite";

import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig({
  base: "/lilypad/",
  plugins: [TanStackRouterVite(), react()],
  build: {
    outDir: "../lilypad/server/dist",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
