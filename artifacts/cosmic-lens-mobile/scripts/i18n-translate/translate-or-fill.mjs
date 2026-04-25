// One-shot script: fill the 236 missing Odia keys in out/or.json
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "artifacts/cosmic-lens-mobile/scripts/i18n-translate");
const en = JSON.parse(fs.readFileSync(path.join(ROOT, "en.json"), "utf8"));
const orPath = path.join(ROOT, "out/or.json");
const or = JSON.parse(fs.readFileSync(orPath, "utf8"));

const missing = Object.keys(en).filter(k => !(k in or));
console.log(`Translating ${missing.length} keys to Odia...`);

const SYSTEM = `You are translating UI strings for a Vedic astrology mobile app called "Cosmic Lens".
Target language: Odia — write in Odia script (ଓଡ଼ିଆ).

Rules:
1. Translate ENGLISH VALUES into Odia. Keys MUST remain unchanged (English identifiers).
2. Preserve EXACTLY: emojis, line breaks (\\n), placeholders like %s %d {0} {name}, numbers, %, time formats (06:30 AM), markdown (**bold**), bullet markers (•, ·, -, →).
3. Brand / product terms stay in English script: "Cosmic Lens", "PRO", "PREMIUM", "FREE", "AstroVastu", "BASIC", "BEST VALUE".
4. Vedic / Sanskrit terms transliterate to Odia script: Kundli, Rashi, Nakshatra, Tithi, Yoga, Karana, Dasha, Mahadasha, Antardasha, Pratyantardasha, Vrat, Pooja, Vastu, Muhurat, Manglik, Nadi, Bhakut, Gana, Yoni, Tara, Vasya, Varna, Atmakaraka, Navatara, Jaimini, Ashtakavarga, Pitra, Rahukaal, Lagna, Panchang.
5. Keep tone concise. Match approximate length.
6. Do NOT add explanations, notes, or extra punctuation. No prefixes/suffixes.
7. If a value is purely an emoji, number, or brand name, return it unchanged.

Output STRICTLY a JSON object: {"key1":"translation1",...}
Same keys as input. No prose. No markdown fences. Pure JSON only.`;

const API_KEY = process.env.AI_INTEGRATIONS_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
const BASE_URL = (process.env.AI_INTEGRATIONS_OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
if (!API_KEY) { console.error("OPENAI key missing"); process.exit(1); }

const MODEL = process.env.MODEL || "gpt-4o-mini";
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 40);
const CONCURRENCY = Number(process.env.CONCURRENCY || 5);

async function callOpenAI(batchObj) {
  const userJson = JSON.stringify(batchObj);
  let lastErr = null;
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      const resp = await fetch(`${BASE_URL}/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}` },
        body: JSON.stringify({
          model: MODEL,
          messages: [
            { role: "system", content: SYSTEM },
            { role: "user", content: userJson },
          ],
          response_format: { type: "json_object" },
          temperature: 0.2,
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${(await resp.text()).slice(0,200)}`);
      const data = await resp.json();
      const content = data.choices?.[0]?.message?.content;
      if (!content) throw new Error("empty content");
      return JSON.parse(content);
    } catch (e) {
      lastErr = e;
      console.warn(`  attempt ${attempt} failed: ${e.message}`);
      await new Promise(r => setTimeout(r, 800 * attempt));
    }
  }
  throw lastErr;
}

const batches = [];
for (let i = 0; i < missing.length; i += BATCH_SIZE) {
  const slice = missing.slice(i, i + BATCH_SIZE);
  const obj = {};
  for (const k of slice) obj[k] = en[k];
  batches.push({ idx: batches.length, keys: slice, obj });
}
console.log(`${batches.length} batches × ${BATCH_SIZE}, concurrency ${CONCURRENCY}, model ${MODEL}`);

let done = 0;
async function worker(jobs) {
  for (const job of jobs) {
    const result = await callOpenAI(job.obj);
    let added = 0;
    for (const k of job.keys) {
      if (result[k] != null && !(k in or)) { or[k] = result[k]; added++; }
    }
    done++;
    console.log(`  batch ${job.idx + 1}/${batches.length}: +${added} (total or now ${Object.keys(or).length})`);
  }
}

// Round-robin shard
const shards = Array.from({ length: CONCURRENCY }, () => []);
batches.forEach((b, i) => shards[i % CONCURRENCY].push(b));

await Promise.all(shards.map(worker));

fs.writeFileSync(orPath, JSON.stringify(or, null, 2));
console.log(`DONE. Final or: ${Object.keys(or).length} / ${Object.keys(en).length}`);
