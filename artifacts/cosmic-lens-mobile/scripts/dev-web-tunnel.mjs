/**
 * Laptop web dev: SSH tunnel → VPS API (port 22 open, raw IP :80/:8080 often blocked on WiFi).
 *
 * Usage: pnpm dev:web
 * Requires: ssh root@187.127.174.55 works (same as VPS terminal login).
 */
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const VPS_SSH = process.env.VPS_SSH?.trim() || "root@187.127.174.55";
const LOCAL_PORT = Number(process.env.DEV_API_TUNNEL_PORT || "18080");
const REMOTE_API = process.env.DEV_API_TUNNEL_REMOTE?.trim() || "127.0.0.1:8080";
const useClear = process.argv.includes("--clear");

function waitForPort(port, ms = 20000) {
  const deadline = Date.now() + ms;
  return new Promise((resolve, reject) => {
    const probe = () => {
      const sock = net.connect(port, "127.0.0.1");
      sock.once("connect", () => {
        sock.destroy();
        resolve();
      });
      sock.once("error", () => {
        sock.destroy();
        if (Date.now() > deadline) {
          reject(new Error(`Tunnel port ${port} not ready after ${ms}ms`));
          return;
        }
        setTimeout(probe, 400);
      });
    };
    probe();
  });
}

console.log("[dev:web] Starting SSH tunnel:");
console.log(`  localhost:${LOCAL_PORT} → ${VPS_SSH} (${REMOTE_API})`);

const ssh = spawn(
  "ssh",
  [
    "-N",
    "-L",
    `${LOCAL_PORT}:${REMOTE_API}`,
    "-o",
    "ExitOnForwardFailure=yes",
    "-o",
    "ServerAliveInterval=30",
    VPS_SSH,
  ],
  { stdio: ["ignore", "pipe", "pipe"] },
);

let sshErr = "";
ssh.stderr?.on("data", (d) => {
  sshErr += String(d);
  process.stderr.write(d);
});

ssh.on("error", (err) => {
  console.error("[dev:web] SSH failed:", err.message);
  console.error("Install OpenSSH client (Windows Settings → Optional features) or use Git Bash ssh.");
  process.exit(1);
});

ssh.on("exit", (code) => {
  if (code && code !== 0) {
    console.error("[dev:web] SSH tunnel exited:", code, sshErr.trim());
  }
});

function shutdown() {
  ssh.kill("SIGTERM");
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

try {
  await waitForPort(LOCAL_PORT);
  console.log(`[dev:web] Tunnel OK ✓  API → http://127.0.0.1:${LOCAL_PORT}`);
} catch (e) {
  console.error("[dev:web]", e.message);
  console.error("SSH login chahiye — pehle test: ssh root@187.127.174.55");
  ssh.kill();
  process.exit(1);
}

const apiUrl = `http://127.0.0.1:${LOCAL_PORT}`;
const devLocal = path.join(__dirname, "dev-local.mjs");
const expoArgs = ["--web"];
if (useClear) expoArgs.push("--clear");

const child = spawn(process.execPath, [devLocal, ...expoArgs], {
  stdio: "inherit",
  env: {
    ...process.env,
    EXPO_PUBLIC_API_URL: apiUrl,
    EXPO_PUBLIC_ALLOW_HTTP_API: "1",
    EXPO_PUBLIC_ENABLE_DEMO_LOGIN: "1",
  },
  cwd: ROOT,
});

child.on("exit", (code) => {
  ssh.kill();
  process.exit(code ?? 0);
});
