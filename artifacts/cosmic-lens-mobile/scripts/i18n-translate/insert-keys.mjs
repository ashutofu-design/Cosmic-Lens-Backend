// Insert new keys into lib/i18nMore.ts:
//   1. Add to MoreT interface (with `: string;`)
//   2. Add to EN block
//   3. Add to HN block (only if HN value provided)
//   4. Add to HI block (only if HI value provided)
// Idempotent: if a key already exists in a section, replaces its value.
//
// Run from project root:
//   node artifacts/cosmic-lens-mobile/scripts/i18n-translate/insert-keys.mjs

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile");
const SRC  = path.join(ROOT, "lib/i18nMore.ts");
const SCRIPTS_DIR = path.join(ROOT, "scripts/i18n-translate");

const BATCH_FILES = ["new-keys-1.mjs", "new-keys-2.mjs", "new-keys-3.mjs", "new-keys-4.mjs"];

// ── Load all batches and merge ────────────────────────────────────────
const merged = {};
for (const f of BATCH_FILES) {
  const fp = path.join(SCRIPTS_DIR, f);
  if (!fs.existsSync(fp)) {
    console.warn(`[skip] ${f} missing`);
    continue;
  }
  const mod = await import(pathToFileURL(fp).href);
  const keys = mod.KEYS || {};
  for (const k of Object.keys(keys)) {
    if (k in merged) console.warn(`[dup] ${k} in ${f} (overriding earlier)`);
    merged[k] = keys[k];
  }
  console.log(`[load] ${f}: ${Object.keys(keys).length} keys`);
}
console.log(`[total] ${Object.keys(merged).length} unique new keys`);

let src = fs.readFileSync(SRC, "utf8");

// ── Helpers ───────────────────────────────────────────────────────────
function escTs(v) { return JSON.stringify(v); }

// Find a TypeScript block bounded by an opening declaration and matching `};`
// Returns {startContent, endContent} byte offsets of the inner content area.
function findBlock(src, openRegex) {
  const m = src.match(openRegex);
  if (!m) throw new Error(`Block not found: ${openRegex}`);
  const startIdx = m.index + m[0].length;
  // Find matching closing brace
  let depth = 1, i = startIdx;
  let inStr = false, strCh = "";
  let inLineComment = false, inBlockComment = false;
  while (i < src.length && depth > 0) {
    const c = src[i], nx = src[i + 1];
    if (inLineComment) {
      if (c === "\n") inLineComment = false;
    } else if (inBlockComment) {
      if (c === "*" && nx === "/") { inBlockComment = false; i++; }
    } else if (inStr) {
      if (c === "\\") { i++; }
      else if (c === strCh) { inStr = false; }
    } else {
      if (c === "/" && nx === "/") { inLineComment = true; i++; }
      else if (c === "/" && nx === "*") { inBlockComment = true; i++; }
      else if (c === '"' || c === "'" || c === "`") { inStr = true; strCh = c; }
      else if (c === "{") depth++;
      else if (c === "}") depth--;
    }
    i++;
  }
  return { startContent: startIdx, endContent: i - 1 };
}

// Read existing keys in a block (returns Map of key -> value range to remove)
function existingKeys(src, b, mode /* 'iface' | 'dict' */) {
  const block = src.slice(b.startContent, b.endContent);
  const keys = new Set();
  // For dict: `key: "value",`. For interface: `key: string;`
  const re = mode === "iface"
    ? /([A-Za-z_][A-Za-z_0-9]*)\s*:\s*string\s*;/g
    : /([A-Za-z_][A-Za-z_0-9]*)\s*:\s*"(?:\\.|[^"\\])*"\s*,?/g;
  let mm;
  while ((mm = re.exec(block)) !== null) keys.add(mm[1]);
  return keys;
}

function insertIntoBlock(src, blockOpenRe, lines, label) {
  const b = findBlock(src, blockOpenRe);
  const insertAt = b.endContent;
  // Ensure trailing newline before closing brace
  const before = src.slice(0, insertAt);
  const after  = src.slice(insertAt);
  const indent = "  ";
  const text = `\n${indent}// ── Phase 4 additions ─────────────────────────\n` +
               lines.map(l => `${indent}${l}`).join("\n") + "\n";
  console.log(`[insert] ${label}: +${lines.length} lines`);
  return before + text + after;
}

// ── Strip prior "Phase 4 additions" blocks (idempotent re-run) ────────
function stripPriorAdditions(src) {
  const re = /\n\s*\/\/ ── Phase 4 additions ─────────────────────────\n[\s\S]*?(?=\n\s*(?:\/\/ ── |\}|\}\;))/g;
  return src.replace(re, "");
}
src = stripPriorAdditions(src);

// ── Compute per-section additions ─────────────────────────────────────
const ifaceBlock = findBlock(src, /interface MoreT\s*\{/);
const ifaceExisting = existingKeys(src, ifaceBlock, "iface");

const enBlock = findBlock(src, /const EN:\s*MoreT\s*=\s*\{/);
const enExisting = existingKeys(src, enBlock, "dict");

const hnBlock = findBlock(src, /const HN:\s*Partial<MoreT>\s*=\s*\{/);
const hnExisting = existingKeys(src, hnBlock, "dict");

const hiBlock = findBlock(src, /const HI:\s*Partial<MoreT>\s*=\s*\{/);
const hiExisting = existingKeys(src, hiBlock, "dict");

const ifaceLines = [];
const enLines    = [];
const hnLines    = [];
const hiLines    = [];

for (const k of Object.keys(merged)) {
  const v = merged[k];
  if (!Array.isArray(v) || v.length === 0) {
    console.warn(`[skip] ${k}: value not array`);
    continue;
  }
  const [enV, hnV, hiV] = v;
  if (!ifaceExisting.has(k)) ifaceLines.push(`${k}: string;`);
  if (!enExisting.has(k))    enLines.push(`${k}: ${escTs(enV)},`);
  if (typeof hnV === "string" && !hnExisting.has(k)) hnLines.push(`${k}: ${escTs(hnV)},`);
  if (typeof hiV === "string" && !hiExisting.has(k)) hiLines.push(`${k}: ${escTs(hiV)},`);
}

// ── Apply insertions in REVERSE order so earlier offsets stay valid ──
// Order: HI, HN, EN, interface (interface is earliest in file)
src = insertIntoBlock(src, /const HI:\s*Partial<MoreT>\s*=\s*\{/, hiLines, "HI");
src = insertIntoBlock(src, /const HN:\s*Partial<MoreT>\s*=\s*\{/, hnLines, "HN");
src = insertIntoBlock(src, /const EN:\s*MoreT\s*=\s*\{/,           enLines, "EN");
src = insertIntoBlock(src, /interface MoreT\s*\{/,                  ifaceLines, "MoreT iface");

fs.writeFileSync(SRC, src, "utf8");
console.log("[done] inserted into", SRC);
