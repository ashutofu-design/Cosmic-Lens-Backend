/**
 * Download cloudflared into tools/ when winget/PATH does not expose it (common on Windows).
 */
import fs from "node:fs";
import https from "node:https";
import path from "node:path";
import { fileURLToPath } from "node:url";

const isWin = process.platform === "win32";
const VERSION = process.env.CLOUDFLARED_VERSION || "2026.5.2";

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const req = https.get(url, (res) => {
      if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        file.close();
        fs.unlinkSync(dest);
        downloadFile(res.headers.location, dest).then(resolve, reject);
        return;
      }
      if (res.statusCode !== 200) {
        file.close();
        fs.unlinkSync(dest);
        reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        return;
      }
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
    });
    req.on("error", reject);
    file.on("error", reject);
  });
}

export function localCloudflaredPath(cwd) {
  return path.join(cwd, "tools", isWin ? "cloudflared.exe" : "cloudflared");
}

export async function ensureCloudflared(cwd) {
  const dest = localCloudflaredPath(cwd);
  if (fs.existsSync(dest)) return dest;

  const asset = isWin ? "cloudflared-windows-amd64.exe" : "cloudflared-linux-amd64";
  const url = `https://github.com/cloudflare/cloudflared/releases/download/${VERSION}/${asset}`;
  fs.mkdirSync(path.dirname(dest), { recursive: true });

  console.log("[cloudflared] Not in PATH — downloading once to:", dest);
  console.log("[cloudflared]", url);
  await downloadFile(url, dest);
  if (!isWin) fs.chmodSync(dest, 0o755);
  console.log("[cloudflared] Ready.");
  return dest;
}

const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));

if (isMain) {
  ensureCloudflared(process.cwd())
    .then((p) => console.log("OK:", p))
    .catch((err) => {
      console.error(err?.message || err);
      process.exit(1);
    });
}
