// Audit translations: count keys identical to EN per language.
// Some identical values are legitimate (brand terms, emojis, numbers).
// Heuristic: a value is "suspicious" if it contains Latin letters AND
// it's not purely an emoji/number/brand-only string.

import fs from "node:fs";
import path from "node:path";

const ROOT    = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const EN_PATH = path.join(ROOT, "en.json");
const OUT_DIR = path.join(ROOT, "out");

const en = JSON.parse(fs.readFileSync(EN_PATH, "utf8"));

const TARGET_LANGS = [
  "bn","mr","ta","te","gu","kn","ml","pa","or","as",
  "zh","es","ar","fr","pt","de","ru","ja","id","ko","tr",
];

// Brand / Sanskrit terms that may legitimately remain in Latin script
// (we keep this list aligned with the prompt in translate.mjs).
const PROTECTED = new Set([
  "Cosmic Lens","PRO","PREMIUM","FREE","AstroVastu","BASIC","BEST VALUE",
  "Kundli","Rashi","Nakshatra","Tithi","Yoga","Karana","Dasha","Mahadasha",
  "Antardasha","Pratyantardasha","Vrat","Pooja","Vastu","Muhurat","Manglik",
  "Nadi","Bhakut","Gana","Yoni","Tara","Vasya","Varna","Atmakaraka",
  "Navatara","Jaimini","Ashtakavarga","Pitra","Rahukaal","Lagna","Panchang",
  "Pradosh","Ekadashi","Amavasya","Purnima","Paksha","Shukla","Krishna",
  "Sade Sati","Janeu","Mundan","Mantra","Karma","Dharma","Yantra","Rudraksha",
  "Tarot","Hawan","Yagya","Sankalp","Bhakti","Moksha",
]);

// Strip emojis and whitespace; if remainder is empty, value is brand-passthrough
function stripEmojiWhitespace(s) {
  return s
    .replace(/[\p{Extended_Pictographic}\p{Emoji_Presentation}\u{FE0F}\u{200D}]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

function isProtectedOnly(s) {
  const stripped = stripEmojiWhitespace(s);
  if (!stripped) return true; // pure emoji
  if (/^\d+([.,]\d+)?%?$/.test(stripped)) return true; // pure number
  // tokenize on non-letters and check if all alphabetic tokens are PROTECTED
  const alphaTokens = stripped.match(/[A-Za-z][A-Za-z' ]{0,30}/g) || [];
  if (alphaTokens.length === 0) return true; // no Latin letters
  return alphaTokens.every(tok => PROTECTED.has(tok.trim()));
}

const summary = {};
const flagged = {};

for (const lang of TARGET_LANGS) {
  const p = path.join(OUT_DIR, `${lang}.json`);
  if (!fs.existsSync(p)) { summary[lang] = { error: "missing" }; continue; }
  const dict = JSON.parse(fs.readFileSync(p, "utf8"));
  let total = 0, identical = 0, suspicious = 0;
  const flag = [];
  for (const k of Object.keys(en)) {
    const v = dict[k];
    if (typeof v !== "string") continue;
    total++;
    if (v === en[k]) {
      identical++;
      // suspicious if EN has translatable content (not just brand/emoji)
      if (!isProtectedOnly(en[k])) {
        suspicious++;
        flag.push(k);
      }
    }
  }
  summary[lang] = { total, identical, suspicious };
  flagged[lang] = flag;
}

console.log("=== Audit summary ===");
for (const [lang, s] of Object.entries(summary)) {
  console.log(`${lang}: total=${s.total} identical=${s.identical} suspicious=${s.suspicious}`);
}

fs.writeFileSync(path.join(ROOT, "audit.json"), JSON.stringify({ summary, flagged }, null, 2));
console.log("Wrote audit.json");
