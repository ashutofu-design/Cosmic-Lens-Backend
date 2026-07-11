import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

/** Read .env file directly — ignores stale shell VITE_* vars (Windows PowerShell). */
function readDotenvValue(key: string, dir: string): string {
  const file = resolve(dir, ".env");
  if (!existsSync(file)) return "";
  const text = readFileSync(file, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const i = t.indexOf("=");
    if (i <= 0) continue;
    if (t.slice(0, i).trim() === key) return t.slice(i + 1).trim();
  }
  return "";
}

export default defineConfig(({ mode }) => {
  const cwd = process.cwd();
  const env = loadEnv(mode, cwd, "");
  const apiTarget =
    readDotenvValue("VITE_API_PROXY_TARGET", cwd) ||
    env.VITE_API_PROXY_TARGET?.trim() ||
    "http://187.127.174.55";

  console.log(`[admin-web] API proxy target: ${apiTarget}`);

  return {
    plugins: [react()],
    server: {
      port: Number(env.PORT) || 5174,
      host: "127.0.0.1",
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          timeout: 120_000,
        },
      },
    },
  };
});
