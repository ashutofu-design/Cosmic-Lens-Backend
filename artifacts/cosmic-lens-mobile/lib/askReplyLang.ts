/** Ask chat reply language — independent of app UI language. */

import type { UILang } from "@/lib/i18n";
import { coerceUILang } from "@/lib/i18n";

export type AskReplyLang = UILang;

export const ASK_REPLY_LANG_STORAGE_KEY = "ask_reply_lang_v1";

export const ASK_REPLY_LANG_OPTIONS: {
  id: AskReplyLang;
  label: string;
  sublabel: string;
}[] = [
  { id: "hi", label: "हिंदी", sublabel: "देवनागरी में jawab" },
  { id: "en", label: "English", sublabel: "Reply in English" },
  { id: "hn", label: "Hinglish", sublabel: "Roman Hindi reply" },
];

/** Single display label for the currently selected reply language. */
export function askReplyLangLabel(lang: AskReplyLang | string | null | undefined): string {
  const id = coerceUILang(lang || "hn");
  const hit = ASK_REPLY_LANG_OPTIONS.find((o) => o.id === id);
  if (hit) return hit.label;
  if (id === "en") return "English";
  if (id === "hi") return "हिंदी";
  return "Hinglish";
}

/** API body `lang` — flask accepts english | hinglish | hindi (or en/hn/hi). */
export function askLangToApi(lang: AskReplyLang): string {
  if (lang === "en") return "english";
  if (lang === "hi") return "hindi";
  return "hinglish";
}

export function loadAskReplyLang(raw: string | null | undefined): AskReplyLang {
  return coerceUILang(raw || "hn");
}

const STRONG_HINGLISH = new Set([
  "kab", "kya", "kyon", "kyun", "kaise", "kaun", "kahan", "kitna", "kitne",
  "hai", "hain", "hoga", "hogi", "mera", "meri", "mere", "mujhe", "mujhko",
  "aap", "aapka", "aapki", "aapke", "mai", "main", "mein", "shaadi", "shadi",
  "naukri", "batao", "nahi", "nahin", "kundli", "dasha", "milega", "milegi",
  "karu", "chahiye", "abhi", "kabhi", "lekin", "kyunki", "toh", "bhi",
  "kaisa", "kaisi", "patni", "pati", "vivah", "rishta", "upay",
]);

const ENGLISH_FUNC = new Set([
  "the", "a", "an", "and", "or", "but", "if", "then", "so", "because",
  "as", "of", "to", "in", "on", "for", "with", "at", "by", "from", "into",
  "through", "during", "before", "after", "between", "under", "when", "where",
  "why", "how", "all", "each", "few", "more", "most", "other", "some", "such",
  "no", "nor", "not", "only", "own", "same", "than", "too", "very", "can",
  "will", "just", "should", "would", "could", "may", "might", "shall", "must",
  "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
  "do", "does", "did", "this", "that", "these", "those", "i", "my", "mine",
  "we", "our", "you", "your", "he", "him", "his", "she", "her", "they", "them",
  "their", "what", "which", "who", "whom", "it", "its", "me", "us", "about",
  "also", "really", "even", "still", "already", "please", "tell", "analyze",
  "situation", "currently",
]);

/**
 * Detect reply language from the question text.
 * Same rule as server `_detect_question_lang`:
 *   Devanagari → hi | clear Roman Hindi → hn | English prose → en
 */
export function detectAskLangFromQuestion(question: string): AskReplyLang | null {
  const q = (question || "").trim();
  if (!q) return null;

  for (const ch of q) {
    const code = ch.charCodeAt(0);
    if (code >= 0x0900 && code <= 0x097f) return "hi";
  }

  const tokens = q.toLowerCase().match(/[a-z]+/g) || [];
  if (!tokens.length) return null;

  const unique = new Set(tokens);
  const strong = [...unique].filter((t) => STRONG_HINGLISH.has(t));
  const enFunc = tokens.filter((t) => ENGLISH_FUNC.has(t)).length;
  const n = tokens.length;

  // Long English prose must not flip to Hinglish
  if (n >= 18 && enFunc / n >= 0.2) {
    if (strong.length < 2) return "en";
  }

  if (strong.length >= 2) return "hn";
  if (strong.length >= 1 && strong.length / Math.max(1, unique.size) >= 0.12) {
    return "hn";
  }
  return "en";
}
