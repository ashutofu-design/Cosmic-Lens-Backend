/**
 * Cross-platform `pnpm run dev`:
 * - Windows laptop → Expo web + API proxy (dev:web)
 * - elsewhere → Replit tunnel script
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";

if (isWin) {
  const child = spawn(
    process.execPath,
    [path.join(__dirname, "dev-web-with-proxy.mjs")],
    { stdio: "inherit", cwd: ROOT, env: process.env },
  );
  child.on("exit", (code) => process.exit(code ?? 0));
  child.on("error", (err) => {
    console.error("[dev] failed:", err.message);
    process.exit(1);
  });
} else {
  const child = spawn(
    "bash",
    [path.join(__dirname, "start-tunnel.sh")],
    {
      stdio: "inherit",
      cwd: ROOT,
      env: {
        ...process.env,
        EXPO_PUBLIC_REPL_ID: process.env.REPL_ID || process.env.EXPO_PUBLIC_REPL_ID || "",
      },
    },
  );
  child.on("exit", (code) => process.exit(code ?? 0));
  child.on("error", (err) => {
    console.error("[dev] bash/tunnel failed:", err.message);
    console.error("[dev] Web fallback: pnpm run dev:web");
    process.exit(1);
  });
}
