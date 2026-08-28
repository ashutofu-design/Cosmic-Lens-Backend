/**
 * Start Metro so a physical phone (dev client APK) loads the SAME bundle as web.
 *
 * Flags:
 *   --tunnel   Try Cloudflare quick tunnel; falls back to LAN if api.trycloudflare.com is blocked
 *   --usb      adb reverse (USB debugging, no QR needed)
 *   --clear    Clear Metro cache on start
 */
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { ensureCloudflared, localCloudflaredPath } from "./ensure-cloudflared.mjs";
import { applyWindowsMetroConfigEnv } from "./lib/metro-env.mjs";

const PORT = process.env.EXPO_METRO_PORT || "8081";
const isWin = process.platform === "win32";
const useTunnel = process.argv.includes("--tunnel");
const useUsb = process.argv.includes("--usb");
const useClear = process.argv.includes("--clear");

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
    ["node_modules", "expo", "bin", "cli"],
    ["node_modules", "expo", "bin", "cli.js"],
    ["node_modules", "expo", "bin", "cli.cjs"],
    ["node_modules", "@expo", "cli", "build", "bin", "cli"],
    ["node_modules", "@expo", "cli", "build", "bin", "cli.js"],
  ];
  const out = [];
  for (const root of roots) {
    for (const parts of rel) {
      out.push(path.resolve(root, ...parts));
    }
  }
  return out;
}

function findCloudflared(cwd) {
  const candidates = [localCloudflaredPath(cwd)];

  const tryNames = isWin ? ["cloudflared.exe", "cloudflared"] : ["cloudflared"];
  for (const name of tryNames) {
    const r = spawnSync(isWin ? "where" : "which", [name], {
      encoding: "utf8",
      shell: isWin,
    });
    if (r.status === 0 && r.stdout?.trim()) {
      for (const line of r.stdout.trim().split(/\r?\n/)) {
        const p = line.trim();
        if (p) candidates.push(p);
      }
    }
  }

  if (isWin) {
    const pf = process.env.ProgramFiles || "C:\\Program Files";
    const pf86 = process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)";
    const local = process.env.LOCALAPPDATA || "";
    candidates.push(
      path.join(pf, "cloudflared", "cloudflared.exe"),
      path.join(pf86, "cloudflared", "cloudflared.exe"),
      path.join(local, "Microsoft", "WinGet", "Links", "cloudflared.exe"),
      path.join(local, "Programs", "cloudflared", "cloudflared.exe"),
    );
  }

  for (const p of candidates) {
    try {
      if (p && fs.existsSync(p)) return p;
    } catch {
      /* ignore */
    }
  }
  return null;
}

function startCloudflaredTunnel(port, bin) {
  console.log("[dev:phone:tunnel] using cloudflared at:", bin);

  return new Promise((resolve, reject) => {
    const proc = spawn(
      bin,
      ["tunnel", "--no-autoupdate", "--protocol", "http2", "--url", `http://127.0.0.1:${port}`],
      { stdio: ["ignore", "pipe", "pipe"], shell: false },
    );

    let buf = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      proc.kill();
      reject(new Error("cloudflared took too long (>90s)"));
    }, 90000);

    const onChunk = (chunk) => {
      const text = chunk.toString();
      process.stderr.write(text.replace(/^/gm, "[cloudflared] "));
      buf += text;
      const urlMatch = buf.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
      const registered = buf.includes("Registered tunnel connection");
      if (urlMatch && registered && !settled) {
        settled = true;
        clearTimeout(timer);
        const url = urlMatch[0];
        resolve({ url, hostname: url.replace(/^https:\/\//, ""), proc });
      }
    };

    proc.stdout.on("data", onChunk);
    proc.stderr.on("data", onChunk);
    proc.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(err);
    });
    proc.on("exit", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(new Error(`cloudflared exited (${code ?? "?"}) before tunnel was ready`));
    });
  });
}

function printLanFirewallHint(port) {
  console.log("LAN checklist (phone + PC on same Wi‑Fi):");
  console.log("  1) Windows Firewall — run once in Admin PowerShell:");
  console.log(
    `     netsh advfirewall firewall add rule name="Cosmic Lens Metro ${port}" dir=in action=allow protocol=TCP localport=${port} profile=private`,
  );
  console.log("  2) Phone must NOT use mobile data only — turn off VPN on phone/PC if LAN fails.");
  console.log("  3) Most reliable if LAN still fails: pnpm run dev:phone:usb");
  console.log("");
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

async function main() {
  const cwd = process.cwd();
  loadDotEnv(cwd);

  const lanCandidates = listLanIps();
  let packagerHost = process.env.REACT_NATIVE_PACKAGER_HOSTNAME;
  let tunnelPublicUrl = null;
  let cfProc = null;
  let tunnelActive = false;
  let tunnelFallbackToLan = false;

  if (useUsb) {
    runAdbReverse();
    packagerHost = "127.0.0.1";
  } else if (useTunnel) {
    try {
      let cfBin = findCloudflared(cwd);
      if (!cfBin) {
        cfBin = await ensureCloudflared(cwd);
      }
      const tunnel = await startCloudflaredTunnel(PORT, cfBin);
      cfProc = tunnel.proc;
      tunnelPublicUrl = tunnel.url;
      packagerHost = tunnel.hostname;
      tunnelActive = true;
      console.log("");
      console.log("[dev:phone:tunnel] READY:", tunnelPublicUrl);
      console.log("[dev:phone:tunnel] Dev app host:", tunnel.hostname);
      console.log("");
    } catch (err) {
      console.error("");
      console.error("[dev:phone:tunnel] Cloudflare tunnel failed:", err?.message || err);
      console.error("");
      console.error("This usually means api.trycloudflare.com is blocked or timing out on your network.");
      console.error("Continuing with LAN mode instead (same Wi‑Fi as this PC)…");
      console.error("");
      tunnelFallbackToLan = true;
      packagerHost = detectLanIp();
      if (!packagerHost) {
        console.error("No LAN IPv4 found — cannot fall back from tunnel.");
        console.error("");
        console.error("Try USB (most reliable):");
        console.error("  pnpm run dev:phone:usb");
        console.error("");
        process.exit(1);
      }
      printLanFirewallHint(PORT);
    }
  } else if (!packagerHost) {
    packagerHost = detectLanIp();
  }

  if (!tunnelActive && !useUsb && packagerHost) {
    printLanFirewallHint(PORT);
  }

  if (!tunnelActive && !useUsb && !packagerHost) {
    console.error("[dev:phone] No LAN IPv4 found. Try:");
    console.error("  pnpm run dev:phone:tunnel   (needs cloudflared — winget install Cloudflare.cloudflared)");
    console.error("  pnpm run dev:phone:usb");
    process.exit(1);
  }

  const monorepoRoot = findMonorepoRoot(cwd);
  const cliPath = expoCliCandidates(cwd, monorepoRoot).find((p) => fs.existsSync(p)) ?? null;

  const env = applyWindowsMetroConfigEnv(
    cwd,
    {
      ...process.env,
      EXPO_PUBLIC_ENABLE_DEMO_LOGIN: "1",
      ...(packagerHost ? { REACT_NATIVE_PACKAGER_HOSTNAME: packagerHost } : {}),
      ...(tunnelPublicUrl
        ? {
            EXPO_PACKAGER_PROXY_URL: tunnelPublicUrl,
            EXPO_MANIFEST_PROXY_URL: tunnelPublicUrl,
          }
        : {}),
      ...(isWin
        ? {
            TEMP: process.env.TEMP || "D:\\Temp",
            TMP: process.env.TMP || "D:\\Temp",
          }
        : {}),
    },
  );

  if (env.EXPO_OVERRIDE_METRO_CONFIG) {
    console.log("[dev:phone] Metro config override:", env.EXPO_OVERRIDE_METRO_CONFIG);
  }

  const manualUrl = useUsb
    ? `http://127.0.0.1:${PORT}`
    : tunnelPublicUrl
      ? tunnelPublicUrl
      : `http://${packagerHost}:${PORT}`;

  const devClientUrl = tunnelPublicUrl
    ? `exp+cosmic-lens://expo-development-client/?url=${encodeURIComponent(tunnelPublicUrl)}`
    : packagerHost
      ? `exp+cosmic-lens://expo-development-client/?url=${encodeURIComponent(`http://${packagerHost}:${PORT}`)}`
      : null;

  console.log("");
  console.log("=== Cosmic Lens — phone dev (latest code from this PC) ===");
  console.log("");
  console.log("IMPORTANT — Metro (JS bundle) is NOT the VPS API:");
  console.log("  • Phone dev URL uses port", PORT, "(Metro on YOUR PC)");
  console.log("  • Do NOT enter http://187.127.174.55:8080 here — that is the backend API only");
  console.log("  • API calls still go to EXPO_PUBLIC_API_URL from .env");
  console.log("    (current:", process.env.EXPO_PUBLIC_API_URL || "(not set)", ")");
  console.log("");
  console.log("WAIT before scanning: let Metro finish until you see 'Bundled' in this window.");
  console.log("First load can take 1–3 minutes — scanning too early causes 'timeout' errors.");
  console.log("");
  console.log("QR scan TIMEOUT? (phone cannot reach this PC)");
  console.log("  A) Best fix — USB (no Wi‑Fi needed):  pnpm run dev:phone:usb");
  console.log("  B) Allow port", PORT, "in Windows Firewall (see checklist above)");
  console.log("  C) Phone + PC same Wi‑Fi; turn OFF mobile data + VPN on both");
  console.log("  D) Router 'AP isolation' blocks LAN — use USB or:  pnpm run dev:phone:tunnel");
  console.log("");
  if (useClear) {
    console.log("Cache: clearing Metro cache (--clear) — first bundle will be slower.");
    console.log("");
  }
  if (tunnelActive) {
    console.log("Mode: CLOUDFLARE TUNNEL (no ngrok — works on Windows)");
  } else if (tunnelFallbackToLan) {
    console.log("Mode: LAN (Cloudflare tunnel unavailable — using Wi‑Fi IP", packagerHost + ")");
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
  if (devClientUrl) {
    console.log("   Or paste this deep link in Chrome on phone (opens dev app):");
    console.log("     ", devClientUrl);
  }
  console.log("");
  if (!tunnelActive && !useUsb && lanCandidates.length > 1) {
    console.log("Detected network IPs (first one is used for QR):");
    for (const c of lanCandidates.slice(0, 5)) {
      const mark = c.ip === packagerHost ? " ← using" : "";
      console.log(`   ${c.ip}  (${c.name})${mark}`);
    }
    console.log("");
  }
  if (!useUsb) {
    console.log("   Metro URL for phone:", manualUrl);
  }
  console.log("   Web on this PC:      ", `http://127.0.0.1:${PORT}`);
  console.log("");
  console.log("Still failing? Try:");
  console.log("  pnpm run dev:phone:usb");
  console.log("  Allow port", PORT, "in Windows Firewall (Private network)");
  console.log("");

  let cmd;
  let args;
  const startMode = "--lan";

  if (cliPath) {
    console.log("[dev:phone] expo cli =", cliPath);
    cmd = process.execPath;
    args = [cliPath, "start", "--dev-client", startMode, "--port", String(PORT)];
    if (useClear) args.push("--clear");
  } else {
    console.warn("[dev:phone] expo cli not in node_modules — trying pnpm exec expo …");
    cmd = isWin ? (process.env.ComSpec || "cmd.exe") : "pnpm";
    const clearFlag = useClear ? " --clear" : "";
    args = isWin
      ? ["/d", "/s", "/c", `pnpm exec expo start --dev-client ${startMode} --port ${PORT}${clearFlag}`]
      : ["exec", "expo", "start", "--dev-client", startMode, "--port", String(PORT), ...(useClear ? ["--clear"] : [])];
  }

  const child = spawn(cmd, args, { stdio: "inherit", env, shell: false, cwd });
  const cleanup = () => {
    if (cfProc && !cfProc.killed) cfProc.kill();
  };
  process.on("SIGINT", () => {
    cleanup();
    process.exit(0);
  });
  process.on("SIGTERM", cleanup);
  child.on("exit", (code) => {
    cleanup();
    process.exit(code ?? 0);
  });
  child.on("error", (err) => {
    cleanup();
    console.error("[dev:phone] failed to start expo:", err?.message || err);
    process.exit(1);
  });
}

main().catch((err) => {
  console.error("[dev:phone] fatal:", err?.message || err);
  process.exit(1);
});
