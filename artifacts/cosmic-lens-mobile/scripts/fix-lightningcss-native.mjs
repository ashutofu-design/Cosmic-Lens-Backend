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

try {
  const winPkgDir = path.dirname(require.resolve("lightningcss-win32-x64-msvc/package.json"));
  const source = path.join(winPkgDir, "lightningcss.win32-x64-msvc.node");
  const lightningDir = path.dirname(require.resolve("lightningcss/package.json"));
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
