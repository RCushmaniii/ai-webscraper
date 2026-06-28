/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// Migrated from Create React App (react-scripts) to Vite.
// - envPrefix keeps the existing REACT_APP_* variables working (no .env churn).
// - build.outDir 'build' preserves the deploy step (`scp build/* ...`).
// - '@' alias supports shadcn/ui component generation (components.json).
export default defineConfig({
  plugins: [react()],
  envPrefix: ["VITE_", "REACT_APP_"],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: "build",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
    css: true,
  },
});
