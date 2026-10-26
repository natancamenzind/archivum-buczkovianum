/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Django runs on this address in development (`make dev`).
const DJANGO_URL = "http://localhost:8000";

export default defineConfig(({ command }) => ({
  // Django serves the build through WhiteNoise under STATIC_URL (architecture §8, Serving).
  base: command === "build" ? "/static/" : "/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    proxy: Object.fromEntries(
      ["/api", "/admin", "/media", "/static"].map((prefix) => [prefix, DJANGO_URL]),
    ),
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      // The generated client, test helpers and the browser entry point are not unit-tested.
      exclude: ["src/api/**", "src/test/**", "src/main.tsx", "src/**/*.test.{ts,tsx}"],
      thresholds: { lines: 90, functions: 90, branches: 90, statements: 90 },
    },
  },
}));
