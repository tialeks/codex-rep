import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: { entry: resolve(import.meta.dirname, "src/index.ts"), name: "LoopframeDesignSystem", fileName: "loopframe-design-system", formats: ["es"] },
    rollupOptions: { external: ["react", "react-dom", "motion", "motion/react"] },
    cssFileName: "styles"
  }
});
