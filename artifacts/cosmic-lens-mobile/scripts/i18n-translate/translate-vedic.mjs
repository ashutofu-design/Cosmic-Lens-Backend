// Translate Vedic vocabulary (rashi/planet/day/direction/color/metal/element/gemstone/deity/nakshatra)
// from EN source to all 22 non-EN/HN/HI languages.
// Each category has a _mode (translate|transliterate) and _hint to guide the model.
// Resumable: per-language JSON files in ./out-vedic/<lang>.json are merged on each run.

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const SRC_PATH = path.join(ROOT, "vedic-source.json");
const OUT_DIR = path.join(ROOT, "out-vedic");
fs.mkdirSync(OUT_DIR, { recursive: true });

const SRC = JSON.parse(fs.readFileSync(SRC_PATH, "utf8"));

// Flatten into { "category.key": { en, mode, hint } }
const ENTRIES = [];
for (const [cat, group] of Object.entries(SRC)) {
  const mode = group._mode || "translate";
  const hint = group._hint || "";
  for (const [k, v] of Object.entries(group)) {
    if (k.startsWith("_")) continue;
    ENTRIES.push({ id: `${cat}.${k}`, en: v, mode, hint, cat });
  }
}
console.log(`Total Vedic entries: ${ENTRIES.length}`);

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

const API_KEY  = process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
const BASE_URL = (process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
if (!API_KEY) { console.error("OPENAI API KEY missing"); process.exit(1); }

const MODEL = process.env.MODEL || "gpt-5-mini";
const CONCURRENCY = Number(process.env.CONCURRENCY || 6);
const MAX_RETRIES = 5;

function buildPrompt(lang, entries) {
  const info = LANG_INFO[lang];
  // Group by category for clarity
  const byCat = {};
  for (const e of entries) (byCat[e.cat] ??= []).push(e);
  const sections = Object.entries(byCat).map(([cat, items]) => {
    const mode = items[0].mode;
    const hint = items[0].hint;
    const lines = items.map(e => `  "${e.id}": "${e.en}"`).join(",\n");
    return `### Category: ${cat} (mode: ${mode})
${hint}
{
${lines}
}`;
  }).join("\n\n");

  return `You are localizing Vedic astrology vocabulary for "Cosmic Lens" app.
Target language: ${info.name} — write ALL output in ${info.script}.

Two modes:
- "translate": Use the natural/standard term in target language (e.g. astronomy, calendar, color words).
- "transliterate": PHONETICALLY transcribe the Sanskrit-origin proper noun into target script. Do NOT translate meaning. Keep the sound recognizable.

Rules:
1. Output a single JSON object whose keys are the FULL ids (e.g. "rashi.mesh", "nakshatra.n0").
2. Every value MUST be in ${info.script}. Do NOT use Latin letters unless the target language natively uses them (e.g. Spanish, French, German, Indonesian, Turkish use Latin; Chinese/Japanese/Korean/Arabic/Russian/Hindi-family DO NOT).
3. Keep terms short (1-3 words). No explanations, no parentheses.
4. For "Rahu" and "Ketu" planet names: TRANSLITERATE (no native equivalent exists).

Categories below:

${sections}

Return ONLY the JSON object with all ${entries.length} keys.`;
}

async function callOpenAI(messages, attempt = 1) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 90000);
  try {
    const r = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}` },
      body: JSON.stringify({
        model: MODEL,
        messages,
        response_format: { type: "json_object" },
        reasoning_effort: "minimal",
      }),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!r.ok) {
      const txt = await r.text();
      throw new Error(`HTTP ${r.status}: ${txt.slice(0, 200)}`);
    }
    const j = await r.json();
    return JSON.parse(j.choices[0].message.content);
  } catch (e) {
    clearTimeout(timer);
    if (attempt < MAX_RETRIES) {
      const wait = Math.min(1000 * 2 ** attempt, 15000);
      console.log(`  retry ${attempt} in ${wait}ms (${e.message.slice(0, 80)})`);
      await new Promise(r => setTimeout(r, wait));
      return callOpenAI(messages, attempt + 1);
    }
    throw e;
  }
}

async function translateLang(lang) {
  const outPath = path.join(OUT_DIR, `${lang}.json`);
  let done = {};
  if (fs.existsSync(outPath)) done = JSON.parse(fs.readFileSync(outPath, "utf8"));

  const todo = ENTRIES.filter(e => !(e.id in done));
  if (todo.length === 0) {
    console.log(`[${lang}] DONE — ${Object.keys(done).length} entries (cached)`);
    return;
  }
  console.log(`[${lang}] translating ${todo.length} of ${ENTRIES.length} entries`);

  const messages = [
    { role: "system", content: "You are an expert localizer for Vedic astrology terminology. Output strict JSON only." },
    { role: "user", content: buildPrompt(lang, todo) },
  ];

  const result = await callOpenAI(messages);
  let added = 0;
  for (const e of todo) {
    if (typeof result[e.id] === "string") {
      done[e.id] = result[e.id].trim();
      added++;
    }
  }
  fs.writeFileSync(outPath, JSON.stringify(done, null, 2));
  console.log(`[${lang}] +${added} (total ${Object.keys(done).length}/${ENTRIES.length})`);

  // Retry pass for any missing
  const stillMissing = ENTRIES.filter(e => !(e.id in done));
  if (stillMissing.length > 0 && stillMissing.length < todo.length) {
    console.log(`[${lang}] retry pass for ${stillMissing.length} missing`);
    const r2 = await callOpenAI([
      { role: "system", content: "Output strict JSON only." },
      { role: "user", content: buildPrompt(lang, stillMissing) },
    ]);
    for (const e of stillMissing) {
      if (typeof r2[e.id] === "string") done[e.id] = r2[e.id].trim();
    }
    fs.writeFileSync(outPath, JSON.stringify(done, null, 2));
  }
}

async function main() {
  const queue = [...langs];
  const workers = Array.from({ length: CONCURRENCY }, async () => {
    while (queue.length) {
      const lang = queue.shift();
      try { await translateLang(lang); }
      catch (e) { console.error(`[${lang}] FAILED: ${e.message}`); }
    }
  });
  await Promise.all(workers);
  console.log("ALL DONE");
}

main().catch(e => { console.error(e); process.exit(1); });
