// Regenerate lib/i18nVedic.ts with full 25-language support.
// Reads vedic-source.json (EN + hn/hi inline) and out-vedic/<lang>.json (22 auto-translated langs).
// Preserves RASHI emoji + lord fields.

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const OUT_DIR = path.join(ROOT, "out-vedic");
const SRC = JSON.parse(fs.readFileSync(path.join(ROOT, "vedic-source.json"), "utf8"));
const TARGET_TS = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/lib/i18nVedic.ts");

// 22 auto-translated langs
const AUTO_LANGS = ["bn","mr","ta","te","gu","kn","ml","pa","or","as","zh","es","ar","fr","pt","de","ru","ja","id","ko","tr"];
// Existing en/hn/hi values (preserved from prior i18nVedic.ts)
const HN_HI = {
  rashi: {
    mesh:      { hn: "Mesh",      hi: "मेष" },
    vrishabh:  { hn: "Vrishabh",  hi: "वृषभ" },
    mithun:    { hn: "Mithun",    hi: "मिथुन" },
    kark:      { hn: "Kark",      hi: "कर्क" },
    simha:     { hn: "Simha",     hi: "सिंह" },
    kanya:     { hn: "Kanya",     hi: "कन्या" },
    tula:      { hn: "Tula",      hi: "तुला" },
    vrishchik: { hn: "Vrishchik", hi: "वृश्चिक" },
    dhanu:     { hn: "Dhanu",     hi: "धनु" },
    makar:     { hn: "Makar",     hi: "मकर" },
    kumbh:     { hn: "Kumbh",     hi: "कुम्भ" },
    meen:      { hn: "Meen",      hi: "मीन" },
  },
  planet: {
    surya:   { hn: "Surya",   hi: "सूर्य" },
    chandra: { hn: "Chandra", hi: "चंद्र" },
    mangal:  { hn: "Mangal",  hi: "मंगल" },
    budh:    { hn: "Budh",    hi: "बुध" },
    guru:    { hn: "Guru",    hi: "गुरु" },
    shukra:  { hn: "Shukra",  hi: "शुक्र" },
    shani:   { hn: "Shani",   hi: "शनि" },
    rahu:    { hn: "Rahu",    hi: "राहु" },
    ketu:    { hn: "Ketu",    hi: "केतु" },
  },
  day: {
    sun: { hn: "Ravivaar",  hi: "रविवार" },
    mon: { hn: "Somvar",    hi: "सोमवार" },
    tue: { hn: "Mangalvar", hi: "मंगलवार" },
    wed: { hn: "Budhavar",  hi: "बुधवार" },
    thu: { hn: "Guruvaar",  hi: "गुरुवार" },
    fri: { hn: "Shukravar", hi: "शुक्रवार" },
    sat: { hn: "Shanivaar", hi: "शनिवार" },
  },
  direction: {
    N:  { hn: "Uttar",   hi: "उत्तर" },
    S:  { hn: "Dakshin", hi: "दक्षिण" },
    E:  { hn: "Purva",   hi: "पूर्व" },
    W:  { hn: "Paschim", hi: "पश्चिम" },
    NE: { hn: "Ishaan",  hi: "ईशान" },
    SE: { hn: "Agni",    hi: "अग्नि" },
    SW: { hn: "Niriti",  hi: "नैऋत्य" },
    NW: { hn: "Vayu",    hi: "वायव्य" },
  },
  color: {
    red: {hn:"Laal",hi:"लाल"}, orange:{hn:"Narangi",hi:"नारंगी"}, white:{hn:"Safed",hi:"सफेद"},
    pink:{hn:"Gulabi",hi:"गुलाबी"}, yellow:{hn:"Peela",hi:"पीला"}, green:{hn:"Hari",hi:"हरा"},
    blue:{hn:"Neela",hi:"नीला"}, gold:{hn:"Sona",hi:"सोना"}, silver:{hn:"Chandi",hi:"चांदी"},
    black:{hn:"Kaala",hi:"काला"}, maroon:{hn:"Maroon",hi:"मैरून"}, violet:{hn:"Baigani",hi:"बैंगनी"},
    lime:{hn:"Neebu",hi:"नींबू"}, seagreen:{hn:"Sea Green",hi:"सी-ग्रीन"}, skyblue:{hn:"Aasmani",hi:"आसमानी"},
    brown:{hn:"Bhura",hi:"भूरा"},
  },
  metal: {
    copper:{hn:"Tamba",hi:"तांबा"}, silver:{hn:"Chandi",hi:"चांदी"}, gold:{hn:"Sona",hi:"सोना"},
    iron:{hn:"Loha",hi:"लोहा"}, bronze:{hn:"Kaansa",hi:"कांसा"},
  },
  element: {
    fire:{hn:"Agni",hi:"अग्नि"}, earth:{hn:"Prithvi",hi:"पृथ्वी"}, air:{hn:"Vayu",hi:"वायु"},
    water:{hn:"Jal",hi:"जल"}, ether:{hn:"Akash",hi:"आकाश"},
  },
  gemstone: {
    ruby:{hn:"Manikya",hi:"माणिक्य"}, pearl:{hn:"Moti",hi:"मोती"}, coral:{hn:"Moonga",hi:"मूंगा"},
    emerald:{hn:"Panna",hi:"पन्ना"}, yellowsapphire:{hn:"Pukhraj",hi:"पुखराज"}, diamond:{hn:"Heera",hi:"हीरा"},
    bluesapphire:{hn:"Neelam",hi:"नीलम"}, hessonite:{hn:"Gomed",hi:"गोमेद"}, catseye:{hn:"Lahsuniya",hi:"लहसुनिया"},
  },
  deity: {
    hanuman:{hn:"Hanuman",hi:"हनुमान"}, lakshmi:{hn:"Lakshmi",hi:"लक्ष्मी"}, ganesh:{hn:"Ganesh",hi:"गणेश"},
    shiva:{hn:"Shiva",hi:"शिव"}, surya:{hn:"Surya",hi:"सूर्य देव"}, saraswati:{hn:"Saraswati",hi:"सरस्वती"},
    kali:{hn:"Kali",hi:"काली"}, vishnu:{hn:"Vishnu",hi:"विष्णु"}, shani:{hn:"Shani Dev",hi:"शनि देव"},
    durga:{hn:"Durga",hi:"दुर्गा"}, parvati:{hn:"Parvati",hi:"पार्वती"},
  },
  nakshatra: {
    n0:{hn:"Ashwini",hi:"अश्विनी"}, n1:{hn:"Bharani",hi:"भरणी"}, n2:{hn:"Krittika",hi:"कृत्तिका"},
    n3:{hn:"Rohini",hi:"रोहिणी"}, n4:{hn:"Mrigashira",hi:"मृगशिरा"}, n5:{hn:"Ardra",hi:"आर्द्रा"},
    n6:{hn:"Punarvasu",hi:"पुनर्वसु"}, n7:{hn:"Pushya",hi:"पुष्य"}, n8:{hn:"Ashlesha",hi:"आश्लेषा"},
    n9:{hn:"Magha",hi:"मघा"}, n10:{hn:"Purva Phalguni",hi:"पूर्व फाल्गुनी"}, n11:{hn:"Uttara Phalguni",hi:"उत्तर फाल्गुनी"},
    n12:{hn:"Hasta",hi:"हस्त"}, n13:{hn:"Chitra",hi:"चित्रा"}, n14:{hn:"Swati",hi:"स्वाति"},
    n15:{hn:"Vishakha",hi:"विशाखा"}, n16:{hn:"Anuradha",hi:"अनुराधा"}, n17:{hn:"Jyeshtha",hi:"ज्येष्ठा"},
    n18:{hn:"Mula",hi:"मूल"}, n19:{hn:"Purva Ashadha",hi:"पूर्वाषाढ़ा"}, n20:{hn:"Uttara Ashadha",hi:"उत्तराषाढ़ा"},
    n21:{hn:"Shravana",hi:"श्रवण"}, n22:{hn:"Dhanishtha",hi:"धनिष्ठा"}, n23:{hn:"Shatabhisha",hi:"शतभिषा"},
    n24:{hn:"Purva Bhadrapada",hi:"पूर्व भाद्रपद"}, n25:{hn:"Uttara Bhadrapada",hi:"उत्तर भाद्रपद"}, n26:{hn:"Revati",hi:"रेवती"},
  },
};

// Rashi extra fields (emoji + ruling planet)
const RASHI_META = {
  mesh: { emoji: "♈", lord: "mangal" }, vrishabh: { emoji: "♉", lord: "shukra" },
  mithun: { emoji: "♊", lord: "budh" }, kark: { emoji: "♋", lord: "chandra" },
  simha: { emoji: "♌", lord: "surya" }, kanya: { emoji: "♍", lord: "budh" },
  tula: { emoji: "♎", lord: "shukra" }, vrishchik: { emoji: "♏", lord: "mangal" },
  dhanu: { emoji: "♐", lord: "guru" }, makar: { emoji: "♑", lord: "shani" },
  kumbh: { emoji: "♒", lord: "shani" }, meen: { emoji: "♓", lord: "guru" },
};

// Load all 22 auto-translated langs
const TRANS = {};
for (const lang of AUTO_LANGS) {
  TRANS[lang] = JSON.parse(fs.readFileSync(path.join(OUT_DIR, `${lang}.json`), "utf8"));
}

function jsonEsc(s) { return JSON.stringify(s); }

function buildLangMap(cat, key, enValue) {
  const hnHi = HN_HI[cat]?.[key] || { hn: enValue, hi: enValue };
  const parts = [
    `en: ${jsonEsc(enValue)}`,
    `hn: ${jsonEsc(hnHi.hn)}`,
    `hi: ${jsonEsc(hnHi.hi)}`,
  ];
  for (const lang of AUTO_LANGS) {
    const v = TRANS[lang][`${cat}.${key}`] ?? enValue;
    parts.push(`${lang}: ${jsonEsc(v)}`);
  }
  return `{ ${parts.join(", ")} }`;
}

// Generate the file
let out = `// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Vedic Vocabulary Translations
// Central lookup for rashi names, planets, days, gemstones, directions, etc.
// FULL 25-language support: en, hn, hi + 22 auto-translated langs.
// AUTO-GENERATED — edit scripts/i18n-translate/vedic-source.json + out-vedic/*.json,
// then run: node scripts/i18n-translate/gen-i18nVedic.mjs
// ══════════════════════════════════════════════════════════════════════════════

import type { UILang } from "./i18n";

// VLang stays as 3-bucket for legacy paragraph content (rashifal, remedies, etc).
export type VLang = "en" | "hn" | "hi";

// 25 → 3 bucket mapper for legacy 3-bucket dictionaries.
export function vedicLang(l: UILang): VLang {
  if (l === "en") return "en";
  if (l === "hn") return "hn";
  if (["hi","bn","mr","ta","te","gu","kn","ml","pa","or","as"].includes(l as string)) return "hi";
  return "en";
}

// LangMap = string for every UILang (full 25-lang Vedic vocabulary).
export type LangMap = Record<UILang, string>;
// Triplet kept for legacy 3-bucket content blocks (paragraphs/themes/etc).
export type Triplet = { en: string; hn: string; hi: string };

// pick() works with either LangMap OR Triplet:
// - If lang exists in object → return it (LangMap path: full 25-lang lookup)
// - Otherwise fall back via vedicLang() bucket (Triplet path: 3-bucket lookup)
// - Final fallback: en
export function pick(lang: UILang | VLang, t: LangMap | Partial<LangMap> | Triplet): string {
  const direct = (t as any)[lang as string];
  if (typeof direct === "string" && direct.length > 0) return direct;
  const bucket = vedicLang(lang as UILang);
  const bv = (t as any)[bucket];
  if (typeof bv === "string" && bv.length > 0) return bv;
  return (t as any).en ?? "";
}

// ── Rashi (zodiac signs) ─────────────────────────────────────────────────────
export type RashiKey =
  | "mesh" | "vrishabh" | "mithun" | "kark" | "simha" | "kanya"
  | "tula" | "vrishchik" | "dhanu" | "makar" | "kumbh" | "meen";

export const RASHI: Record<RashiKey, LangMap & { emoji: string; lord: string }> = {
`;
for (const [k, v] of Object.entries(SRC.rashi)) {
  if (k.startsWith("_")) continue;
  const meta = RASHI_META[k];
  const lm = buildLangMap("rashi", k, v).slice(2, -2); // strip outer { }
  out += `  ${k.padEnd(10)}: { ${lm}, emoji: ${jsonEsc(meta.emoji)}, lord: ${jsonEsc(meta.lord)} },\n`;
}
out += `};\n\n`;

// ── Planets ─────────────────────────────────────────────────────────────────
out += `// ── Planets ──────────────────────────────────────────────────────────────────
export type PlanetKey =
  | "surya" | "chandra" | "mangal" | "budh" | "guru"
  | "shukra" | "shani" | "rahu" | "ketu";

export const PLANET: Record<PlanetKey, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.planet)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(8)}: ${buildLangMap("planet", k, v)},\n`;
}
out += `};\n\n`;

// ── Days ─────────────────────────────────────────────────────────────────
out += `// ── Days of week ─────────────────────────────────────────────────────────────
export type DayKey = "sun" | "mon" | "tue" | "wed" | "thu" | "fri" | "sat";

export const DAY: Record<DayKey, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.day)) {
  if (k.startsWith("_")) continue;
  out += `  ${k}: ${buildLangMap("day", k, v)},\n`;
}
out += `};\n\n`;

// ── Directions ─────────────────────────────────────────────────────────────
out += `// ── Directions (8-way) ───────────────────────────────────────────────────────
export type DirKey = "N" | "S" | "E" | "W" | "NE" | "SE" | "SW" | "NW";

export const DIRECTION: Record<DirKey, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.direction)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(2)}: ${buildLangMap("direction", k, v)},\n`;
}
out += `};\n\n`;

// ── Colors ─────────────────────────────────────────────────────────────
out += `// ── Colors ───────────────────────────────────────────────────────────────────
export const COLOR: Record<string, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.color)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(10)}: ${buildLangMap("color", k, v)},\n`;
}
out += `};\n\n`;

// ── Metals ─────────────────────────────────────────────────────────────
out += `// ── Metals ───────────────────────────────────────────────────────────────────
export const METAL: Record<string, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.metal)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(7)}: ${buildLangMap("metal", k, v)},\n`;
}
out += `};\n\n`;

// ── Elements ─────────────────────────────────────────────────────────────
out += `// ── 5 Elements (Pancha-mahabhuta) ─────────────────────────────────────────────
export const ELEMENT: Record<string, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.element)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(6)}: ${buildLangMap("element", k, v)},\n`;
}
out += `};\n\n`;

// ── Gemstones ─────────────────────────────────────────────────────────────
out += `// ── Gemstones ────────────────────────────────────────────────────────────────
export const GEMSTONE: Record<string, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.gemstone)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(15)}: ${buildLangMap("gemstone", k, v)},\n`;
}
out += `};\n\n`;

// ── Deities ─────────────────────────────────────────────────────────────
out += `// ── Deities (transliterated across langs — sacred names kept phonetic) ──────
export const DEITY: Record<string, LangMap> = {
`;
for (const [k, v] of Object.entries(SRC.deity)) {
  if (k.startsWith("_")) continue;
  out += `  ${k.padEnd(10)}: ${buildLangMap("deity", k, v)},\n`;
}
out += `};\n\n`;

// ── Helpers ─────────────────────────────────────────────────────────────
out += `// ── Convenience helpers ──────────────────────────────────────────────────────
export function rashiName(key: RashiKey, lang: UILang): string {
  return pick(lang, RASHI[key]);
}
export function planetName(key: PlanetKey, lang: UILang): string {
  return pick(lang, PLANET[key]);
}
export function dayName(key: DayKey, lang: UILang): string {
  return pick(lang, DAY[key]);
}

// Map weekday number (0=Sun..6=Sat) → DayKey
export const WEEKDAY_KEYS: DayKey[] = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

// ── Nakshatra (27 lunar mansions, transliterated across langs) ──────────────
export const NAKSHATRA: LangMap[] = [
`;
const nakKeys = Object.keys(SRC.nakshatra).filter(k => !k.startsWith("_"));
for (const k of nakKeys) {
  out += `  ${buildLangMap("nakshatra", k, SRC.nakshatra[k])},\n`;
}
out += `];

export function nakshatraName(idx: number, lang: UILang | "en" | "hn" | "hi"): string {
  const n = NAKSHATRA[idx];
  if (!n) return "";
  return pick(lang, n);
}

// ── Rashi index helper (0=Mesh..11=Meen) ────────────────────────────────────
export const RASHI_KEYS: RashiKey[] = [
  "mesh","vrishabh","mithun","kark","simha","kanya",
  "tula","vrishchik","dhanu","makar","kumbh","meen",
];
export function rashiAt(idx: number, lang: UILang | "en" | "hn" | "hi"): string {
  const k = RASHI_KEYS[((idx % 12) + 12) % 12];
  return pick(lang, RASHI[k]);
}
`;

fs.writeFileSync(TARGET_TS, out);
console.log(`Wrote ${TARGET_TS} — ${out.split("\n").length} lines`);
