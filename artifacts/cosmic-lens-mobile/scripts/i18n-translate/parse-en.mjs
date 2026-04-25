// Parse the EN block of lib/i18nMore.ts into a JSON file of {key: enValue}.
// Run from project root via:  node artifacts/cosmic-lens-mobile/scripts/i18n-translate/parse-en.mjs

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile");
const SRC  = path.join(ROOT, "lib/i18nMore.ts");
const OUT  = path.join(ROOT, "scripts/i18n-translate/en.json");

const src = fs.readFileSync(SRC, "utf8");

// Extract the EN block between `const EN: MoreT = {` and the matching `};`
const startMarker = /const EN:\s*MoreT\s*=\s*\{/;
const m = src.match(startMarker);
if (!m) { console.error("EN block start not found"); process.exit(1); }
const startIdx = m.index + m[0].length;

// Find the matching closing brace by depth tracking, treating strings carefully.
let depth = 1;
let i = startIdx;
let inStr = false;
let strCh = "";
let inLineComment = false;
let inBlockComment = false;

while (i < src.length && depth > 0) {
  const c = src[i];
  const nx = src[i + 1];
  if (inLineComment) {
    if (c === "\n") inLineComment = false;
  } else if (inBlockComment) {
    if (c === "*" && nx === "/") { inBlockComment = false; i++; }
  } else if (inStr) {
    if (c === "\\") { i++; } // skip next
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
const endIdx = i - 1; // position of matching `}`
const block = src.slice(startIdx, endIdx);

// Now extract key: "value" pairs.
// Keys are JS identifiers; values are double-quoted strings (with possible escapes).
const out = {};
const re = /([A-Za-z_][A-Za-z_0-9]*)\s*:\s*"((?:\\.|[^"\\])*)"/g;
let mm;
let count = 0;
while ((mm = re.exec(block)) !== null) {
  const key = mm[1];
  const raw = mm[2];
  // Decode standard JS string escapes
  const decoded = raw
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\")
    .replace(/\\'/g, "'");
  if (key in out) {
    console.error(`DUP key "${key}" — keeping first`);
    continue;
  }
  out[key] = decoded;
  count++;
}
console.log(`Parsed ${count} EN keys`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 2), "utf8");
console.log("Wrote", OUT);
