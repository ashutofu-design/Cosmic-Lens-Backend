// Patch lib/i18nMore.ts to insert Partial<MoreT> blocks for all 21 translated
// languages and update getTM() to dispatch to them.
// Run from project root after translate.mjs has filled out/<lang>.json.

import fs from "node:fs";
import path from "node:path";

const ROOT      = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile");
const SRC       = path.join(ROOT, "lib/i18nMore.ts");
const OUT_DIR   = path.join(ROOT, "scripts/i18n-translate/out");
const EN_PATH   = path.join(ROOT, "scripts/i18n-translate/en.json");

const TARGET_LANGS = [
  "bn","mr","ta","te","gu","kn","ml","pa","or","as",
  "zh","es","ar","fr","pt","de","ru","ja","id","ko","tr",
];

const en = JSON.parse(fs.readFileSync(EN_PATH, "utf8"));

function escTsString(v) {
  // produce a double-quoted JS/TS string literal, properly escaped
  return JSON.stringify(v);
}

function buildBlock(code, dict) {
  const lines = [];
  lines.push(`const ${code.toUpperCase()}: Partial<MoreT> = {`);
  for (const k of Object.keys(en)) {
    const v = dict[k];
    if (typeof v !== "string") continue;
    if (v === en[k]) continue; // skip if identical to EN — let it fall back
    lines.push(`  ${k}: ${escTsString(v)},`);
  }
  lines.push("};");
  return lines.join("\n");
}

const dicts = {};
for (const lang of TARGET_LANGS) {
  const p = path.join(OUT_DIR, `${lang}.json`);
  if (!fs.existsSync(p)) {
    console.warn(`[skip] ${lang}.json not found`);
    continue;
  }
  const data = JSON.parse(fs.readFileSync(p, "utf8"));
  const have = Object.values(data).filter(v => typeof v === "string" && v.length).length;
  const total = Object.keys(en).length;
  console.log(`[${lang}] ${have}/${total} keys`);
  dicts[lang] = data;
}

const blocks = [];
for (const lang of TARGET_LANGS) {
  if (dicts[lang]) blocks.push(buildBlock(lang, dicts[lang]));
}

let src = fs.readFileSync(SRC, "utf8");

// Where to insert the new blocks: right before the existing getTM function.
const getTmRe = /\/\*\*\s*\n\s*\*\s*Get the additional translation table[\s\S]*?\*\/\s*\nexport function getTM\(/;
const getTmStartRe = /export function getTM\(/;

let insertIdx;
const docMatch = src.match(getTmRe);
if (docMatch) {
  insertIdx = docMatch.index;
} else {
  const m2 = src.match(getTmStartRe);
  if (!m2) { console.error("Cannot locate getTM"); process.exit(1); }
  insertIdx = m2.index;
}

// Strip any previously-inserted blocks for these lang codes (idempotent re-run).
for (const lang of TARGET_LANGS) {
  const re = new RegExp(`\\nconst ${lang.toUpperCase()}:\\s*Partial<MoreT>\\s*=\\s*\\{[\\s\\S]*?^\\};\\n`, "m");
  src = src.replace(re, "\n");
}

// Recompute insertion point after stripping
const docMatch2 = src.match(getTmRe);
const m2b = src.match(getTmStartRe);
insertIdx = (docMatch2 ? docMatch2.index : m2b.index);

const insertion = "\n// ── Auto-generated translations (21 langs) ──────────────────────\n" +
  blocks.join("\n\n") + "\n\n";

src = src.slice(0, insertIdx) + insertion + src.slice(insertIdx);

// Replace the getTM body with full dispatcher.
const newGetTM =
`export function getTM(lang: UILang): MoreT {
  switch (lang) {
    case "hn": return { ...EN, ...HN };
    case "hi": return { ...EN, ...HI };
${TARGET_LANGS.filter(l => dicts[l]).map(l => `    case "${l}": return { ...EN, ...${l.toUpperCase()} };`).join("\n")}
    default:   return EN;
  }
}`;

src = src.replace(
  /export function getTM\(lang: UILang\): MoreT \{[\s\S]*?\n\}/,
  newGetTM
);

fs.writeFileSync(SRC, src, "utf8");
console.log(`Patched ${SRC} with ${Object.keys(dicts).length} language blocks.`);
