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

const API =
  process.env.EXPO_PUBLIC_API_URL?.trim() ||
  (useWeb ? "http://127.0.0.1:18081" : "http://187.127.174.55:8080");
const PORT = process.env.EXPO_METRO_PORT || "18987";
const useWeb = process.argv.includes("--web");
const useClear = process.argv.includes("--clear");

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

// Windows: Metro writes large caches under TEMP/TMP (often on C:).
// If C: is low on space, force caches to D:\Temp (user can override by setting TEMP/TMP).
const FALLBACK_TEMP = "D:\\Temp";
const env = applyWindowsMetroConfigEnv(process.cwd(), {
  ...process.env,
  EXPO_PUBLIC_API_URL: API,
  EXPO_PUBLIC_ENABLE_DEMO_LOGIN:
    process.env.EXPO_PUBLIC_ENABLE_DEMO_LOGIN?.trim() || "1",
  EXPO_PUBLIC_ALLOW_HTTP_API:
    process.env.EXPO_PUBLIC_ALLOW_HTTP_API?.trim() || "1",
  // Web + localtunnel: must listen on 127.0.0.1 (not LAN IP) or tunnel gets HTTP 408.
  REACT_NATIVE_PACKAGER_HOSTNAME: useWeb ? "127.0.0.1" : LAN_IP,
  ...(isWin
    ? {
        TEMP: process.env.TEMP || FALLBACK_TEMP,
        TMP: process.env.TMP || FALLBACK_TEMP,
      }
    : {}),
});

// Prefer running the Expo CLI JS entry via node (most reliable across shells/Windows).
// Avoids spawning .cmd / pnpm exec / npx which can fail with EINVAL/UNKNOWN.
const candidates = [
  path.resolve(process.cwd(), "node_modules", "expo", "bin", "cli.js"),
  path.resolve(process.cwd(), "node_modules", "expo", "bin", "cli.cjs"),
  path.resolve(process.cwd(), "node_modules", "@expo", "cli", "build", "bin", "cli"),
  path.resolve(process.cwd(), "node_modules", "@expo", "cli", "build", "bin", "cli.js"),
];

let cmd;
let args;

const cliPath = candidates.find(p => fs.existsSync(p)) || null;
if (cliPath) {
  cmd = process.execPath; // node
  const startMode = useWeb ? "--web" : "--lan";
  const hostFlag = useWeb ? ["--host", "localhost"] : [];
  args = [cliPath, "start", startMode, ...hostFlag, "--port", String(PORT)];
  if (useClear) args.push("--clear");
} else {
  // Last resort: fall back to npx
  const startMode = useWeb ? "--web" : "--lan";
  const hostFlag = useWeb ? "--host localhost" : "";
  cmd = isWin ? (process.env.ComSpec || "cmd.exe") : "npx";
  args = isWin
    ? ["/d", "/s", "/c", `npx expo start ${startMode} ${hostFlag} --port ${PORT}${useClear ? " --clear" : ""}`.trim()]
    : ["expo", "start", startMode, ...(useWeb ? ["--host", "localhost"] : []), "--port", String(PORT), ...(useClear ? ["--clear"] : [])];
}

console.log("[dev:local] EXPO_PUBLIC_API_URL =", API);
console.log("[dev:local] expo start", useWeb ? "--web" : "--lan", "--port", PORT);
if (!useWeb) {
  console.log("[dev:local] Phone LAN IP for QR:", LAN_IP);
  console.log("[dev:local] Manual URL:", `http://${LAN_IP}:${PORT}`);
  console.log(
    "[dev:local] Phone: install the Cosmic Lens *development* APK (EAS dev build), NOT Expo Go.",
  );
  console.log(
    "[dev:local] Open that app → scan the terminal QR (do not use the phone Camera app).",
  );
} else {
  console.log("[dev:local] Web: open http://127.0.0.1:" + PORT + " in this browser");
  console.log("[dev:local] Demo login API:", API);
  console.log("[dev:local] Browser console: localStorage.removeItem('cl_force_api_base') if old IP cached");
}
if (isWin) console.log("[dev:local] TEMP/TMP =", env.TEMP);
if (cliPath) console.log("[dev:local] expo cli =", cliPath);

const child = spawn(cmd, args, { stdio: "inherit", env, shell: false });
child.on("exit", (code) => process.exit(code ?? 0));
child.on("error", (err) => {
  console.error("[dev:local] failed to start expo:", err?.message || err);
  process.exit(1);
});

