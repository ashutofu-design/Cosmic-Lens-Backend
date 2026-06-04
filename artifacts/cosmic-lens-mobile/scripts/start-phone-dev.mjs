/**
 * Start Metro so a physical phone (dev client APK) loads the SAME bundle as web.
 * Uses LAN IP — not 127.0.0.1 (phone cannot reach your PC's localhost).
 *
 * Flags:
 *   --tunnel   ngrok tunnel (Wi‑Fi / firewall issues)
 *   --usb      adb reverse (USB debugging, no QR needed)
 */
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const PORT = process.env.EXPO_METRO_PORT || "8081";
const isWin = process.platform === "win32";
const useTunnel = process.argv.includes("--tunnel");
const useUsb = process.argv.includes("--usb");

function listLanIps() {
  const out = [];
  for (const [name, ifaces] of Object.entries(os.networkInterfaces())) {
    for (const iface of ifaces ?? []) {
      if (iface.family !== "IPv4" || iface.internal) continue;
      const ip = iface.address;
      if (ip.startsWith("169.254.")) continue;
      let score = 10;
      if (ip.startsWith("192.168.")) score = 100;
      else if (ip.startsWith("10.")) score = 80;
      else if (ip.startsWith("172.")) score = 30;
      out.push({ ip, score, name });
    }
  }
  out.sort((a, b) => b.score - a.score);
  return out;
}

function detectLanIp() {
  return listLanIps()[0]?.ip ?? null;
}

function findMonorepoRoot(startDir) {
  let dir = startDir;
  for (let i = 0; i < 8; i++) {
    if (fs.existsSync(path.join(dir, "pnpm-workspace.yaml"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return startDir;
}

function expoCliCandidates(...roots) {
  const rel = [
    ["node_modules", "expo", "bin", "cli.js"],
    ["node_modules", "expo", "bin", "cli.cjs"],
    ["node_modules", "@expo", "cli", "build", "bin", "cli.js"],
    ["node_modules", "@expo", "cli", "build", "bin", "cli"],
  ];
  const out = [];
  for (const root of roots) {
    for (const parts of rel) {
      out.push(path.resolve(root, ...parts));
    }
  }
  return out;
}

function runAdbReverse() {
  const r = spawnSync("adb", ["reverse", `tcp:${PORT}`, `tcp:${PORT}`], {
    encoding: "utf8",
    shell: isWin,
  });
  if (r.status !== 0) {
    console.error("[dev:phone:usb] adb reverse failed.");
    console.error("  Enable USB debugging on phone, connect USB, run: adb devices");
    console.error(r.stderr || r.stdout || "");
    process.exit(1);
  }
  console.log(`[dev:phone:usb] adb reverse tcp:${PORT} tcp:${PORT} OK`);
}

const lanCandidates = listLanIps();
let packagerHost = process.env.REACT_NATIVE_PACKAGER_HOSTNAME;

if (useUsb) {
  runAdbReverse();
  packagerHost = "127.0.0.1";
} else if (!packagerHost) {
  packagerHost = detectLanIp();
}

if (!useTunnel && !packagerHost) {
  console.error("[dev:phone] No LAN IPv4 found. Try:");
  console.error("  pnpm run dev:phone:tunnel");
  console.error("  or set REACT_NATIVE_PACKAGER_HOSTNAME=your.pc.wifi.ip");
  process.exit(1);
}

const cwd = process.cwd();
const monorepoRoot = findMonorepoRoot(cwd);
const cliPath = expoCliCandidates(cwd, monorepoRoot).find((p) => fs.existsSync(p)) ?? null;

const env = {
  ...process.env,
  ...(packagerHost ? { REACT_NATIVE_PACKAGER_HOSTNAME: packagerHost } : {}),
  EXPO_PUBLIC_ENABLE_DEMO_LOGIN: "1",
  ...(isWin
    ? {
        TEMP: process.env.TEMP || "D:\\Temp",
        TMP: process.env.TMP || "D:\\Temp",
      }
    : {}),
};

const manualUrl = useUsb
  ? `http://127.0.0.1:${PORT}`
  : useTunnel
    ? "(see exp:// URL in Metro after tunnel starts)"
    : `http://${packagerHost}:${PORT}`;

const devClientUrl = useUsb
  ? `exp+cosmic-lens://expo-development-client/?url=${encodeURIComponent(manualUrl)}`
  : packagerHost
    ? `exp+cosmic-lens://expo-development-client/?url=${encodeURIComponent(`http://${packagerHost}:${PORT}`)}`
    : null;

console.log("");
console.log("=== Cosmic Lens — phone dev (latest code from this PC) ===");
console.log("");
if (useTunnel) {
  console.log("Mode: TUNNEL (works across Wi‑Fi / firewall issues — scan QR when it appears)");
} else if (useUsb) {
  console.log("Mode: USB (adb reverse — QR not needed)");
} else {
  console.log("Mode: LAN (phone + PC on same Wi‑Fi)");
}
console.log("");
console.log("1) Open Cosmic Lens *development* APK (NOT Expo Go, NOT phone Camera app).");
console.log("2) Dev app → Scan QR Code → scan QR in THIS terminal only.");
console.log("3) If QR fails → shake phone → Dev menu → Enter URL manually:");
console.log("     ", manualUrl);
if (devClientUrl && !useTunnel) {
  console.log("   Or paste this deep link in Chrome on phone (opens dev app):");
  console.log("     ", devClientUrl);
}
console.log("");
if (!useTunnel && lanCandidates.length > 1) {
  console.log("Detected network IPs (first one is used for QR):");
  for (const c of lanCandidates.slice(0, 5)) {
    const mark = c.ip === packagerHost ? " ← using" : "";
    console.log(`   ${c.ip}  (${c.name})${mark}`);
  }
  console.log("   Wrong IP? Stop Metro and run:");
  console.log(`   set REACT_NATIVE_PACKAGER_HOSTNAME=192.168.x.x && pnpm run dev:phone`);
  console.log("");
}
if (!useTunnel && !useUsb) {
  console.log("   Metro URL for phone:", `http://${packagerHost}:${PORT}`);
}
console.log("   Web on this PC:      ", `http://127.0.0.1:${PORT}`);
console.log("");
console.log("QR not working? Try:");
console.log("  pnpm run dev:phone:usb     (USB cable + USB debugging)");
console.log("  pnpm run dev:phone:tunnel  (ngrok — slow but reliable)");
console.log("  Allow port", PORT, "in Windows Firewall (Private network)");
console.log("");

let cmd;
let args;

const startMode = useTunnel ? "--tunnel" : "--lan";

if (cliPath) {
  console.log("[dev:phone] expo cli =", cliPath);
  cmd = process.execPath;
  args = [cliPath, "start", "--dev-client", startMode, "--port", String(PORT)];
} else {
  console.warn("[dev:phone] expo cli not in node_modules — trying pnpm exec expo …");
  cmd = isWin ? (process.env.ComSpec || "cmd.exe") : "pnpm";
  args = isWin
    ? ["/d", "/s", "/c", `pnpm exec expo start --dev-client ${startMode} --port ${PORT}`]
    : ["exec", "expo", "start", "--dev-client", startMode, "--port", String(PORT)];
}

const child = spawn(cmd, args, { stdio: "inherit", env, shell: false, cwd });
child.on("exit", (code) => process.exit(code ?? 0));
child.on("error", (err) => {
  console.error("[dev:phone] failed to start expo:", err?.message || err);
  process.exit(1);
});
