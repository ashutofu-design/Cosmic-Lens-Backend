import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { applyWindowsMetroConfigEnv } from "./lib/metro-env.mjs";

function loadDotEnv(cwd) {
  const envPath = path.join(cwd, ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const i = t.indexOf("=");
    if (i <= 0) continue;
    const key = t.slice(0, i).trim();
    let val = t.slice(i + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}

const cwd = process.cwd();
loadDotEnv(cwd);

const useWeb = process.argv.includes("--web");
const useClear = process.argv.includes("--clear");
const useLocalApi = (process.env.EXPO_PUBLIC_USE_LOCAL_API || "").trim() === "1";
const PROXY_PORT = process.env.DEV_API_PROXY_PORT || "18081";
const WEB_PROXY = `http://127.0.0.1:${PROXY_PORT}`;
// .env has https://api.coosmic.icu — that CORS-blocks localhost Google login.
if (useWeb && !useLocalApi) {
  process.env.EXPO_PUBLIC_API_URL = WEB_PROXY;
}
const API =
  process.env.EXPO_PUBLIC_API_URL?.trim() ||
  (useWeb ? WEB_PROXY : "http://187.127.174.55:8080");
const PORT = process.env.EXPO_METRO_PORT || "18987";
const isWin = process.platform === "win32";

function detectLanIp() {
  for (const ifaces of Object.values(os.networkInterfaces())) {
    for (const iface of ifaces ?? []) {
      if (iface.family === "IPv4" && !iface.internal) {
        return iface.address;
      }
    }
  }
  return "127.0.0.1";
}

const LAN_IP = process.env.REACT_NATIVE_PACKAGER_HOSTNAME || detectLanIp();
const FALLBACK_TEMP = "D:\\Temp";

const env = applyWindowsMetroConfigEnv(process.cwd(), {
  ...process.env,
  EXPO_PUBLIC_API_URL: API,
  EXPO_PUBLIC_ENABLE_DEMO_LOGIN:
    process.env.EXPO_PUBLIC_ENABLE_DEMO_LOGIN?.trim() || "1",
  EXPO_PUBLIC_ALLOW_HTTP_API:
    process.env.EXPO_PUBLIC_ALLOW_HTTP_API?.trim() || "1",
  REACT_NATIVE_PACKAGER_HOSTNAME: useWeb ? "localhost" : LAN_IP,
  ...(isWin
    ? {
        TEMP: process.env.TEMP || FALLBACK_TEMP,
        TMP: process.env.TMP || FALLBACK_TEMP,
      }
    : {}),
});
// One tab only — we open Chrome once after Metro is ready; Expo must not also open.
if (useWeb) {
  env.BROWSER = "none";
}

const candidates = [
  path.resolve(cwd, "node_modules", "expo", "bin", "cli"),
  path.resolve(cwd, "node_modules", "expo", "bin", "cli.js"),
  path.resolve(cwd, "node_modules", "expo", "bin", "cli.cjs"),
];

const cliPath = candidates.find((p) => fs.existsSync(p));
if (!cliPath) {
  console.error("[dev:local] expo CLI not found. Run: pnpm install (from repo root)");
  process.exit(1);
}

const args = [cliPath, "start", "--port", String(PORT)];
if (useWeb) {
  args.push("--web", "--host", "localhost");
} else {
  args.push("--lan");
}
if (useClear) args.push("--clear");

let browserOpened = false;

function openChrome(url) {
  if (browserOpened) return;
  browserOpened = true;
  try {
    if (isWin) {
      // Prefer Chrome; fall back to default browser.
      const chromePaths = [
        path.join(process.env["PROGRAMFILES"] || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env["PROGRAMFILES(X86)"] || "", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env.LOCALAPPDATA || "", "Google", "Chrome", "Application", "chrome.exe"),
      ];
      const chrome = chromePaths.find((p) => p && fs.existsSync(p));
      if (chrome) {
        spawn(chrome, [url], { stdio: "ignore", detached: true, windowsHide: true }).unref();
      } else {
        spawn("cmd.exe", ["/c", "start", "", url], {
          stdio: "ignore",
          detached: true,
          windowsHide: true,
        }).unref();
      }
    } else if (process.platform === "darwin") {
      spawn("open", [url], { stdio: "ignore", detached: true }).unref();
    } else {
      spawn("xdg-open", [url], { stdio: "ignore", detached: true }).unref();
    }
    console.log("[dev:local] Opened:", url);
  } catch (err) {
    console.warn("[dev:local] open browser failed:", err?.message || err);
  }
}

const webUrl = `http://localhost:${PORT}`;

async function waitForMetro(url, maxMs = 120000) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    try {
      await fetch(url, { signal: AbortSignal.timeout(2500) });
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
  return false;
}

async function proxyHealthy() {
  try {
    const r = await fetch(`${WEB_PROXY}/api/healthz`, {
      signal: AbortSignal.timeout(2500),
    });
    const j = await r.json().catch(() => null);
    return r.ok && j?.status === "ok";
  } catch {
    return false;
  }
}

async function ensureWebProxy() {
  if (!useWeb || useLocalApi) return null;
  if (await proxyHealthy()) {
    console.log("[dev:local] API proxy already up ✓", WEB_PROXY);
    return null;
  }
  console.log("[dev:local] Starting API proxy →", WEB_PROXY);
  const proxy = spawn(process.execPath, [path.join(cwd, "scripts", "api-proxy.mjs")], {
    stdio: "inherit",
    env: {
      ...process.env,
      DEV_API_PROXY_PORT: PROXY_PORT,
      DEV_API_PROXY_UPSTREAM:
        process.env.DEV_API_PROXY_UPSTREAM || "https://admin.coosmic.icu",
    },
    cwd,
  });
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (await proxyHealthy()) {
      console.log("[dev:local] API proxy OK ✓");
      return proxy;
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  console.error(
    "[dev:local] API proxy did not start. Google login will Failed to fetch.\n" +
      "  Check: curl -sS https://admin.coosmic.icu/api/healthz",
  );
  return proxy;
}

console.log("[dev:local] EXPO_PUBLIC_API_URL =", API);
console.log("[dev:local] starting:", "node", args.map((a) => (a.includes(" ") ? `"${a}"` : a)).join(" "));
console.log("[dev:local] TEMP =", env.TEMP || process.env.TEMP);
if (useWeb) {
  console.log("[dev:local] Web URL:", webUrl);
  console.log("[dev:local] Chrome will open once when Metro is ready — watch this window for Bundling %");
}

const proxyChild = await ensureWebProxy();

const child = spawn(process.execPath, args, {
  stdio: "inherit",
  env,
  shell: false,
  cwd,
});

function shutdown(code = 0) {
  try {
    child.kill("SIGTERM");
  } catch {
    /* ignore */
  }
  try {
    proxyChild?.kill("SIGTERM");
  } catch {
    /* ignore */
  }
  process.exit(code);
}

child.on("exit", (code) => shutdown(code ?? 0));
child.on("error", (err) => {
  console.error("[dev:local] failed:", err?.message || err);
  shutdown(1);
});
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

if (useWeb) {
  waitForMetro(webUrl).then((ready) => {
    if (ready) {
      openChrome(webUrl);
    } else {
      console.warn("[dev:local] Metro slow — open manually:", webUrl);
    }
  });
}
