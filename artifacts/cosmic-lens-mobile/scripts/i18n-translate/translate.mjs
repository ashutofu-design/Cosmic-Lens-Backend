// Translate the EN dict to all 21 non-EN/HN/HI languages via OpenAI.
// Resumable: per-language JSON files in ./out/<lang>.json are merged on each run.
// Usage:
//   OPENAI_API_KEY=... node artifacts/cosmic-lens-mobile/scripts/i18n-translate/translate.mjs [lang1 lang2 ...]
// If no lang args given, translates all 21.

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const EN_PATH = path.join(ROOT, "en.json");
const OUT_DIR = path.join(ROOT, "out");
fs.mkdirSync(OUT_DIR, { recursive: true });

const en = JSON.parse(fs.readFileSync(EN_PATH, "utf8"));
const ALL_KEYS = Object.keys(en);
console.log(`EN keys: ${ALL_KEYS.length}`);

const LANG_INFO = {
  bn: { name: "Bengali",     script: "Bengali script (বাংলা)" },
  mr: { name: "Marathi",     script: "Devanagari (मराठी)" },
  ta: { name: "Tamil",       script: "Tamil script (தமிழ்)" },
  te: { name: "Telugu",      script: "Telugu script (తెలుగు)" },
  gu: { name: "Gujarati",    script: "Gujarati script (ગુજરાતી)" },
  kn: { name: "Kannada",     script: "Kannada script (ಕನ್ನಡ)" },
  ml: { name: "Malayalam",   script: "Malayalam script (മലയാളം)" },
  pa: { name: "Punjabi",     script: "Gurmukhi script (ਪੰਜਾਬੀ)" },
  or: { name: "Odia",        script: "Odia script (ଓଡ଼ିଆ)" },
  as: { name: "Assamese",    script: "Assamese script (অসমীয়া)" },
  zh: { name: "Simplified Chinese", script: "Simplified Chinese (简体中文)" },
  es: { name: "Spanish",     script: "Spanish (Español)" },
  ar: { name: "Arabic",      script: "Modern Standard Arabic (العربية)" },
  fr: { name: "French",      script: "French (Français)" },
  pt: { name: "Portuguese",  script: "Portuguese (Português, Brazilian)" },
  de: { name: "German",      script: "German (Deutsch)" },
  ru: { name: "Russian",     script: "Russian (Русский)" },
  ja: { name: "Japanese",    script: "Japanese (日本語)" },
  id: { name: "Indonesian",  script: "Bahasa Indonesia" },
  ko: { name: "Korean",      script: "Korean (한국어)" },
  tr: { name: "Turkish",     script: "Türkçe" },
};

const TARGET_LANGS = Object.keys(LANG_INFO);
const argLangs = process.argv.slice(2).filter(a => TARGET_LANGS.includes(a));
const langs = argLangs.length ? argLangs : TARGET_LANGS;
console.log("Translating to:", langs.join(", "));

const API_KEY  = process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
const BASE_URL = (process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
if (!API_KEY) { console.error("OPENAI API KEY missing"); process.exit(1); }

const MODEL = process.env.MODEL || "gpt-5-mini";
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 60);
const CONCURRENCY = Number(process.env.CONCURRENCY || 6);
const MAX_RETRIES = 5;

function buildPrompt(lang) {
  const info = LANG_INFO[lang];
  return `You are translating UI strings for a Vedic astrology mobile app called "Cosmic Lens".
Target language: ${info.name} — write in ${info.script}.

Rules:
1. Translate ENGLISH VALUES into ${info.name}. Keys MUST remain unchanged (English identifiers).
2. Preserve EXACTLY: emojis, line breaks (\\n), placeholders like %s %d {0} {name}, numbers, %, time formats (06:30 AM), markdown (**bold**), bullet markers (•, ·, -, →).
3. Brand / product terms stay in English script: "Cosmic Lens", "PRO", "PREMIUM", "FREE", "AstroVastu", "BASIC", "BEST VALUE".
4. Vedic / Sanskrit terms must stay as transliteration (for Indian-script languages, transliterate to that script; for global languages, keep the standard romanized form):
   Kundli, Rashi, Nakshatra, Tithi, Yoga, Karana, Dasha, Mahadasha, Antardasha, Pratyantardasha,
   Vrat, Pooja, Vastu, Muhurat, Manglik, Nadi, Bhakut, Gana, Yoni, Tara, Vasya, Varna,
   Atmakaraka, Navatara, Jaimini, Ashtakavarga, Pitra, Rahukaal, Lagna, Panchang, Pradosh,
   Ekadashi, Amavasya, Purnima, Paksha, Shukla, Krishna, Sade Sati, Janeu, Mundan, Mantra,
   Karma, Dharma, Yantra, Rudraksha, Tarot, Hawan, Yagya, Sankalp, Bhakti, Moksha.
5. Keep tone concise — these are mobile UI labels. Match approximate length.
6. Do NOT add explanations, notes, or extra punctuation. No prefixes/suffixes.
7. If a value is purely an emoji, number, or brand name, return it unchanged.

Output STRICTLY a JSON object: {"key1":"translation1","key2":"translation2",...}
Same keys as input. No prose. No markdown fences. Pure JSON only.`;
}

async function callOpenAI(systemPrompt, userJson) {
  const body = {
    model: MODEL,
    max_completion_tokens: 16384,
    reasoning_effort: "minimal",
    response_format: { type: "json_object" },
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: "Translate the values in this JSON object:\n" + JSON.stringify(userJson) },
    ],
  };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 90_000); // 90s per request
  let resp;
  try {
    resp = await fetch(BASE_URL + "/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
  } finally {
    clearTimeout(timer);
  }
  if (!resp.ok) {
    const text = await resp.text();
    const err = new Error(`HTTP ${resp.status}: ${text.slice(0, 400)}`);
    err.status = resp.status;
    throw err;
  }
  const data = await resp.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error("Empty content from OpenAI");
  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch (e) {
    throw new Error("Invalid JSON from OpenAI: " + content.slice(0, 200));
  }
  return parsed;
}

async function withRetry(fn, label) {
  let lastErr;
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      const wait = Math.min(30000, 1000 * Math.pow(2, i)) + Math.random() * 500;
      console.warn(`[${label}] try ${i + 1} failed: ${e.message?.slice(0, 120)} — wait ${Math.round(wait)}ms`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw lastErr;
}

function chunk(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

async function translateLang(lang) {
  const outPath = path.join(OUT_DIR, `${lang}.json`);
  let done = {};
  if (fs.existsSync(outPath)) {
    try { done = JSON.parse(fs.readFileSync(outPath, "utf8")); } catch {}
  }
  const remaining = ALL_KEYS.filter(k => !(k in done) || typeof done[k] !== "string" || done[k].length === 0);
  if (!remaining.length) {
    console.log(`[${lang}] already complete (${Object.keys(done).length} keys)`);
    return;
  }
  console.log(`[${lang}] need ${remaining.length} keys (already ${Object.keys(done).length})`);
  const batches = chunk(remaining, BATCH_SIZE);
  const sys = buildPrompt(lang);
  let i = 0;
  for (const batch of batches) {
    i++;
    const input = {};
    batch.forEach(k => { input[k] = en[k]; });
    const result = await withRetry(() => callOpenAI(sys, input), `${lang} b${i}/${batches.length}`);
    let added = 0;
    for (const k of batch) {
      if (typeof result[k] === "string") { done[k] = result[k]; added++; }
    }
    fs.writeFileSync(outPath, JSON.stringify(done, null, 2), "utf8");
    console.log(`[${lang}] batch ${i}/${batches.length} +${added} (total ${Object.keys(done).length}/${ALL_KEYS.length})`);
  }
  console.log(`[${lang}] DONE — ${Object.keys(done).length} keys`);
}

async function runWithConcurrency(items, n, fn) {
  const queue = [...items];
  const workers = Array.from({ length: n }, async () => {
    while (queue.length) {
      const item = queue.shift();
      try { await fn(item); }
      catch (e) { console.error(`FAIL ${item}: ${e.message}`); }
    }
  });
  await Promise.all(workers);
}

await runWithConcurrency(langs, CONCURRENCY, translateLang);
console.log("ALL DONE");
