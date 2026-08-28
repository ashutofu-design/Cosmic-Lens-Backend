/**
 * Laptop web: local API proxy + Expo web (one command).
 * Always proxies to hosted API (https://admin.coosmic.icu) unless forced.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PROXY_PORT = process.env.DEV_API_PROXY_PORT || "18081";
// HTTPS required — HTTP redirects break POSTs (login shows "Not found").
const PRODUCTION_UPSTREAM = "https://admin.coosmic.icu";

async function pickUpstream() {
  const forced = process.env.DEV_API_PROXY_UPSTREAM?.trim();
  if (forced) {
    let upstream = forced.replace(/\/$/, "");
    if (/^http:\/\/admin\.coosmic\.icu/i.test(upstream)) {
      upstream = upstream.replace(/^http:/i, "https:");
    }
    console.log("[dev:web] Using forced upstream:", upstream);
    return upstream;
  }
  console.log("[dev:web] Proxy → hosted API", PRODUCTION_UPSTREAM);
  return PRODUCTION_UPSTREAM;
}

let UPSTREAM = await pickUpstream();
const useClear = process.argv.includes("--clear");
const apiUrl = `http://127.0.0.1:${PROXY_PORT}`;

async function waitForProxy(maxMs = 20000) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${apiUrl}/api/healthz`, {
        signal: AbortSignal.timeout(4000),
      });
      if (r.ok) {
        const j = await r.json().catch(() => null);
        if (j?.status === "ok") return true;
      }
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

console.log("[dev:web] Starting API proxy…");
const proxy = spawn(process.execPath, [path.join(__dirname, "api-proxy.mjs")], {
  stdio: "inherit",
  env: {
    ...process.env,
    DEV_API_PROXY_PORT: PROXY_PORT,
    DEV_API_PROXY_UPSTREAM: UPSTREAM,
  },
  cwd: ROOT,
});

proxy.on("error", (err) => {
  console.error("[dev:web] proxy failed:", err.message);
  process.exit(1);
});

const proxyOk = await waitForProxy();
if (!proxyOk) {
  console.error(
    "[dev:web] Proxy health check FAILED — http://127.0.0.1:" +
      PROXY_PORT +
      "/api/healthz",
  );
  console.error("[dev:web] Pehle yeh test karo: curl -sS https://admin.coosmic.icu/api/healthz");
  proxy.kill("SIGTERM");
  process.exit(1);
}

console.log("[dev:web] Proxy OK ✓  API =", apiUrl);
console.log("[dev:web] Upstream =", UPSTREAM);

const expoArgs = [path.join(__dirname, "dev-local.mjs"), "--web"];
if (useClear) expoArgs.push("--clear");

const child = spawn(process.execPath, expoArgs, {
  stdio: "inherit",
  env: {
    ...process.env,
    EXPO_PUBLIC_API_URL: apiUrl,
    EXPO_PUBLIC_ALLOW_HTTP_API: "1",
    EXPO_PUBLIC_ENABLE_DEMO_LOGIN: "1",
  },
  cwd: ROOT,
});

function shutdown() {
  child.kill("SIGTERM");
  proxy.kill("SIGTERM");
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

child.on("exit", (code) => {
  proxy.kill("SIGTERM");
  process.exit(code ?? 0);
});
