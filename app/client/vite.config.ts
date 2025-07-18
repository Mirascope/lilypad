import tailwindcss from "@tailwindcss/vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { defineConfig, loadEnv } from "vite";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [
      TanStackRouterVite({
        routeFileIgnorePattern: "\\.(test|spec)\\.(ts|tsx)$",
      }),
      ,
      react(),
      tailwindcss(),
    ],
    build: {
      outDir: env["VITE_OUT_DIR"] || "../lilypad/server/static",
      rollupOptions: {
        external: ["bun:test"],
      },
    },
    server: {
      host: true,
      port: 5173,
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./"),
      },
    },
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV),
    },
  };
});
