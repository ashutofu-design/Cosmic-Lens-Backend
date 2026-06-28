/** Mirror of api-server/ask_language_gate.detect_supported_ask_lang for admin display. */

export type AskQuestionLang = "en" | "hi" | "hn";

const HINGLISH_TOKENS = new Set([
  "kab", "kya", "kyon", "kyun", "kaise", "kaun", "kahan", "kitna", "kitne",
  "hai", "hain", "ho", "hoga", "hogi", "hua", "hui", "tha", "thi", "the",
  "mai", "main", "mei", "mein", "me",
  "mera", "meri", "mere", "mujhe", "mujhko", "humara", "humari", "hamara",
  "aap", "aapka", "aapki", "aapke", "tum", "tera", "teri", "tumhara",
  "shaadi", "shadi", "vivah", "biwi", "pati", "patni", "rishta",
  "naukri", "kaam", "paisa", "paise", "dhan", "santaan", "bachcha",
  "swasthya", "bimari", "batao", "bataiye", "karna", "karu", "karoon",
  "nahi", "nahin", "haan", "han", "kundli", "rashi", "nakshatra", "dasha",
  "abhi", "phir", "pehle", "baad", "se", "tak", "ya", "aur",
  "prem", "sambandh", "yog", "banega", "jeevan", "baar",
]);

const UNSUPPORTED_SCRIPT_RANGES: [number, number][] = [
  [0x0980, 0x09ff],
  [0x0a00, 0x0a7f],
  [0x0a80, 0x0aff],
  [0x0b00, 0x0b7f],
  [0x0b80, 0x0bff],
  [0x0c00, 0x0c7f],
  [0x0c80, 0x0cff],
  [0x0d00, 0x0d7f],
  [0x0600, 0x06ff],
  [0x0750, 0x077f],
  [0x0400, 0x04ff],
  [0x0e00, 0x0e7f],
  [0x3040, 0x30ff],
  [0x4e00, 0x9fff],
  [0xac00, 0xd7af],
];

function unsupportedScriptHit(question: string): boolean {
  for (const ch of question) {
    const o = ch.codePointAt(0) ?? 0;
    if (o < 128 || /\s/.test(ch)) continue;
    if (o >= 0x0900 && o <= 0x097f) continue;
    for (const [lo, hi] of UNSUPPORTED_SCRIPT_RANGES) {
      if (o >= lo && o <= hi) return true;
    }
  }
  return false;
}

export function detectQuestionLang(question: string): AskQuestionLang | null {
  const q = (question || "").trim();
  if (!q) return "en";
  if (unsupportedScriptHit(q)) return null;

  for (const ch of q) {
    if (ch >= "\u0900" && ch <= "\u097F") return "hi";
  }

  const tokens = q.toLowerCase().match(/[a-zA-Z]+/g) ?? [];
  if (!tokens.length) return "en";

  const hinglishHits = tokens.filter((t) => HINGLISH_TOKENS.has(t)).length;
  if (hinglishHits >= 2) return "hn";
  if (hinglishHits >= 1 && hinglishHits / tokens.length >= 0.1) return "hn";
  return "en";
}

export function questionLangLabel(lang: AskQuestionLang | null): string {
  if (lang === "hi") return "Hindi (Devanagari)";
  if (lang === "hn") return "Hinglish (Roman Hindi)";
  if (lang === "en") return "English";
  return "Unsupported script";
}

export function questionLangShort(lang: AskQuestionLang | null): string {
  if (lang === "hi") return "Hindi";
  if (lang === "hn") return "Hinglish";
  if (lang === "en") return "English";
  return "Other";
}
