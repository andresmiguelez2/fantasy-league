import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import fs from "fs";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    https: fs.existsSync("./certs/localhost-key.pem") && fs.existsSync("./certs/localhost.pem")
      ? {
          key: fs.readFileSync("./certs/localhost-key.pem"),
          cert: fs.readFileSync("./certs/localhost.pem"),
        }
      : false,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
