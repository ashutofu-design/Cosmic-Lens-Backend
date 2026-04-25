// Translate content-en.json into all 23 non-EN languages (hn=Hinglish, hi=Devanagari, +21 others).
// Resumable per-lang JSON in ./out/<lang>.json.

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-content");
const EN_PATH = path.join(ROOT, "content-en.json");
const OUT_DIR = path.join(ROOT, "out");
fs.mkdirSync(OUT_DIR, { recursive: true });

const en = JSON.parse(fs.readFileSync(EN_PATH, "utf8"));
const ALL_KEYS = Object.keys(en);
console.log(`Content EN keys: ${ALL_KEYS.length}`);

const LANG_INFO = {
  hn: { name: "Hinglish",    script: "Roman script — Hindi words spelled with English letters (e.g. 'Naya saal mubarak ho')" },
  hi: { name: "Hindi",       script: "Devanagari script (हिन्दी)" },
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
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 50);
const CONCURRENCY = Number(process.env.CONCURRENCY || 8);
const MAX_RETRIES = 5;

function buildPrompt(lang) {
  const info = LANG_INFO[lang];
  return `You are translating CONTENT strings (calendar months, demo chart labels, numerology themes, Navatara names/descriptions, Jaimini Karaka names/descriptions, Vastu room guidance) for a Vedic astrology mobile app called "Cosmic Lens".
Target language: ${info.name} — write in ${info.script}.

Rules:
1. Translate ENGLISH VALUES into ${info.name}. Keys MUST remain unchanged (English identifiers).
2. Calendar month names (keys starting with month_full_ or month_short_) MUST be the natural calendar month names of the target language. Use the language's standard names (e.g. for Marathi use जानेवारी फेब्रुवारी मार्च; for Tamil ஜனவரி பிப்ரவரி; for Spanish enero febrero; etc.). NEVER leave them as English.
3. Vedic / Sanskrit terms (Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Paramamitra, Atmakaraka, Amatyakaraka, Bhratrukaraka, Matrakaraka, Putrakaraka, Gnatikaraka, Darakaraka, Vastu, Ishan, Agni, Brahmasthan, Saraswati, Ganpati, Swastik, Om, Gayatri, Mandarin, Rangoli) — for Indian-script languages transliterate into that script; for global languages keep the standard romanized form.
4. Direction abbreviations like NE, NW, SE, SW may stay as English letters; cardinal direction words (North, East, South, West) should be translated naturally.
5. Brand / product terms stay in English script: "Cosmic Lens", "PRO", "PREMIUM", "FREE", "AstroVastu".
6. Preserve EXACTLY: emojis, line breaks (\\n), placeholders like %s %d {0} {name}, numbers, %, time formats (10PM, 1AM), parentheses, quotes around mantras (e.g. 'Om Namah Shivaya' stays as 'Om Namah Shivaya' but transliterated for Indian-script langs).
7. Keep tone concise and informative. Match approximate length.
8. Do NOT add explanations, notes, or extra punctuation. No prefixes/suffixes.
9. If a value is purely an emoji, number, or brand name (e.g. "10PM", "1AM"), translate the WORD parts only — for "10PM"/"1AM"/etc, keep the digit but translate AM/PM if there is a natural local form, OR keep the English form if standard.
10. For "Now" — translate to the natural local word for "now/current time".

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
  const timer = setTimeout(() => ctrl.abort(), 90_000);
  let resp;
  try {
    resp = await fetch(BASE_URL + "/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${API_KEY}` },
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
  try {
    return JSON.parse(content);
  } catch (e) {
    throw new Error("Invalid JSON from OpenAI: " + content.slice(0, 200));
  }
}

async function withRetry(fn, label) {
  let lastErr;
  for (let i = 0; i < MAX_RETRIES; i++) {
    try { return await fn(); }
    catch (e) {
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
