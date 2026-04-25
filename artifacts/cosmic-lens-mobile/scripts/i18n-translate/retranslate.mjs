// Re-translate flagged keys (those identical to EN that should have been translated).
// Reads audit.json (produced by audit.mjs) and updates out/<lang>.json in place.
//
// Usage:
//   node artifacts/cosmic-lens-mobile/scripts/i18n-translate/retranslate.mjs [lang...]

import fs from "node:fs";
import path from "node:path";

const ROOT      = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const EN_PATH   = path.join(ROOT, "en.json");
const OUT_DIR   = path.join(ROOT, "out");
const AUDIT     = path.join(ROOT, "audit.json");

const en    = JSON.parse(fs.readFileSync(EN_PATH, "utf8"));
const audit = JSON.parse(fs.readFileSync(AUDIT, "utf8"));

const LANG_INFO = {
  bn: "Bengali (write in Bengali script বাংলা)",
  mr: "Marathi (write in Devanagari मराठी)",
  ta: "Tamil (write in Tamil script தமிழ்)",
  te: "Telugu (write in Telugu script తెలుగు)",
  gu: "Gujarati (write in Gujarati script ગુજરાતી)",
  kn: "Kannada (write in Kannada script ಕನ್ನಡ)",
  ml: "Malayalam (write in Malayalam script മലയാളം)",
  pa: "Punjabi (write in Gurmukhi script ਪੰਜਾਬੀ)",
  or: "Odia (write in Odia script ଓଡ଼ିଆ)",
  as: "Assamese (write in Assamese script অসমীয়া)",
  zh: "Simplified Chinese (write in 简体中文)",
  es: "Spanish (Español)",
  ar: "Modern Standard Arabic (write in العربية)",
  fr: "French (Français)",
  pt: "Brazilian Portuguese (Português)",
  de: "German (Deutsch)",
  ru: "Russian (write in Cyrillic Русский)",
  ja: "Japanese (write in 日本語)",
  id: "Bahasa Indonesia",
  ko: "Korean (write in 한국어)",
  tr: "Turkish (Türkçe)",
};

const TARGET_LANGS = Object.keys(LANG_INFO);
const argLangs = process.argv.slice(2).filter(a => TARGET_LANGS.includes(a));
const langs = argLangs.length ? argLangs : TARGET_LANGS;

const API_KEY  = process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
const BASE_URL = (process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
if (!API_KEY) { console.error("API key missing"); process.exit(1); }

const MODEL = process.env.MODEL || "gpt-5-mini"; // mini is more careful than nano
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 25);
const CONCURRENCY = Number(process.env.CONCURRENCY || 4);
const MAX_RETRIES = 5;

function prompt(lang) {
  const langDesc = LANG_INFO[lang];
  return `You are a professional translator for "Cosmic Lens", a Vedic astrology mobile app.

CRITICAL TASK: The following English UI strings were NOT translated on a previous pass. You MUST translate them now into ${langDesc}.

ABSOLUTE RULES:
1. EVERY value in the input MUST be translated into the target language script.
2. DO NOT return the input string unchanged. DO NOT keep it in English. The reason these keys are being re-translated is because they were left in English on the previous pass.
3. Preserve emojis (🔮, 💑, etc.) and number/percent formats EXACTLY in their original positions.
4. Preserve placeholders like %s, %d, {0}, {name}, \\n exactly.
5. Brand names stay as-is (English Latin script): "Cosmic Lens", "PRO", "PREMIUM", "FREE", "AstroVastu", "BASIC", "BEST VALUE".
6. Vedic / Sanskrit terms must be transliterated into the target script — do NOT leave them in Latin script for non-Latin target languages:
   Kundli, Rashi, Nakshatra, Tithi, Yoga, Karana, Dasha, Mahadasha, Antardasha, Pratyantardasha,
   Vrat, Pooja, Vastu, Muhurat, Manglik, Nadi, Bhakut, Gana, Yoni, Tara, Vasya, Varna,
   Atmakaraka, Navatara, Jaimini, Ashtakavarga, Pitra, Rahukaal, Lagna, Panchang, Pradosh,
   Ekadashi, Amavasya, Purnima, Paksha, Shukla, Krishna, Sade Sati, Janeu, Mundan, Mantra,
   Karma, Dharma, Yantra, Rudraksha, Tarot, Hawan, Yagya, Sankalp, Bhakti, Moksha.
7. Tone: concise mobile UI labels. Match approximate length when possible.
8. Output STRICTLY a JSON object with the SAME keys, values translated into ${langDesc}.
   No prose. No markdown. Pure JSON.

Translate every value. If you accidentally leave any value unchanged you have failed the task.`;
}

async function callOpenAI(systemPrompt, userJson) {
  const body = {
    model: MODEL,
    max_completion_tokens: 16384,
    reasoning_effort: "minimal",
    response_format: { type: "json_object" },
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: "Translate every value. Return JSON only.\n" + JSON.stringify(userJson) },
    ],
  };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 90_000);
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
  } finally { clearTimeout(timer); }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${(await resp.text()).slice(0,200)}`);
  const data = await resp.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error("Empty content");
  return JSON.parse(content);
}

async function withRetry(fn, label) {
  let lastErr;
  for (let i = 0; i < MAX_RETRIES; i++) {
    try { return await fn(); }
    catch (e) {
      lastErr = e;
      const wait = Math.min(20000, 800 * Math.pow(2, i)) + Math.random() * 400;
      console.warn(`[${label}] try ${i+1} failed: ${e.message?.slice(0,100)} — wait ${Math.round(wait)}ms`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw lastErr;
}

function chunk(a, n) { const o=[]; for (let i=0;i<a.length;i+=n) o.push(a.slice(i,i+n)); return o; }

async function retranslateLang(lang) {
  const flag = audit.flagged[lang] || [];
  if (!flag.length) { console.log(`[${lang}] nothing to retranslate`); return; }
  const outPath = path.join(OUT_DIR, `${lang}.json`);
  const dict = JSON.parse(fs.readFileSync(outPath, "utf8"));

  // Re-check current state (the dict may already have been improved on prior re-runs)
  const remaining = flag.filter(k => dict[k] === en[k]);
  if (!remaining.length) { console.log(`[${lang}] flagged keys already retranslated`); return; }
  console.log(`[${lang}] retranslating ${remaining.length} flagged keys`);

  const sys = prompt(lang);
  const batches = chunk(remaining, BATCH_SIZE);
  let i = 0;
  for (const batch of batches) {
    i++;
    const input = {};
    batch.forEach(k => { input[k] = en[k]; });
    const result = await withRetry(() => callOpenAI(sys, input), `${lang} r${i}/${batches.length}`);
    let changed = 0;
    for (const k of batch) {
      const v = result[k];
      if (typeof v === "string" && v.length && v !== en[k]) { dict[k] = v; changed++; }
    }
    fs.writeFileSync(outPath, JSON.stringify(dict, null, 2), "utf8");
    console.log(`[${lang}] retry batch ${i}/${batches.length} changed ${changed}/${batch.length}`);
  }
}

async function runConcurrently(items, n, fn) {
  const q = [...items];
  await Promise.all(Array.from({length:n}, async () => {
    while (q.length) {
      const it = q.shift();
      try { await fn(it); }
      catch(e) { console.error(`FAIL ${it}: ${e.message}`); }
    }
  }));
}

await runConcurrently(langs, CONCURRENCY, retranslateLang);
console.log("RETRANSLATE DONE");
