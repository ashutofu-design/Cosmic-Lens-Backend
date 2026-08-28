/**
 * pnpm monorepo on Windows: lightningcss optional native binary is often not linked
 * next to the lightningcss package Metro uses. Copy the .node file where index.js expects it.
 */
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

if (process.platform !== "win32") {
  process.exit(0);
}

const require = createRequire(import.meta.url);

function pkgDir(name) {
  // Avoid require.resolve("pkg/package.json") — newer packages block ./package.json in exports.
  const entry = require.resolve(name);
  let dir = path.dirname(entry);
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(dir, "package.json"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error("package.json not found for " + name);
}

try {
  const winPkgDir = pkgDir("lightningcss-win32-x64-msvc");
  const source = path.join(winPkgDir, "lightningcss.win32-x64-msvc.node");
  const lightningDir = pkgDir("lightningcss");
  const target = path.join(lightningDir, "lightningcss.win32-x64-msvc.node");

  if (!fs.existsSync(source)) {
    console.warn("[fix-lightningcss] missing:", source);
    process.exit(0);
  }

  if (!fs.existsSync(target) || fs.statSync(target).size !== fs.statSync(source).size) {
    fs.copyFileSync(source, target);
    console.log("[fix-lightningcss] installed", target);
  }
} catch (err) {
  console.warn("[fix-lightningcss] skip:", err?.message || err);
}
