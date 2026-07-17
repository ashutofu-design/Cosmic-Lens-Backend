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
  { id: "en", label: "English", sublabel: "Reply in English" },
  { id: "hn", label: "Hinglish", sublabel: "Roman Hindi reply" },
  { id: "hi", label: "हिंदी", sublabel: "देवनागरी में jawab" },
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

/**
 * Detect reply language from the question text.
 * Same rule as server `_resolve_response_lang`:
 *   Devanagari → hi | Roman Hindi/Hinglish → hn | English → en
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

  const hinglish = new Set([
    "mera", "meri", "mere", "mujhe", "mujhko", "main", "mai", "mein", "me",
    "kya", "kab", "kaise", "kaisa", "kaisi", "kyun", "kyu", "kitna", "kitne",
    "hai", "hain", "hoga", "hogi", "honge", "ho", "hua", "hui",
    "shaadi", "shadi", "naukri", "job", "paisa", "paise", "ghar",
    "kabhi", "abhi", "bahut", "thoda", "acha", "accha", "theek",
    "aap", "aapki", "aapka", "tumhara", "tumhari", "uska", "uski",
    "wala", "wali", "ke", "ki", "ka", "se", "par", "pe", "ko",
    "aur", "ya", "nahi", "nhi", "mat", "bas", "sirf",
  ]);
  const hits = tokens.filter((t) => hinglish.has(t)).length;
  if (hits >= 2) return "hn";
  if (hits >= 1 && hits / tokens.length >= 0.1) return "hn";
  return "en";
}
