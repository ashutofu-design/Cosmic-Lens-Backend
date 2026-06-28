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

/** API body `lang` — flask accepts english | hinglish | hindi (or en/hn/hi). */
export function askLangToApi(lang: AskReplyLang): string {
  if (lang === "en") return "english";
  if (lang === "hi") return "hindi";
  return "hinglish";
}

export function loadAskReplyLang(raw: string | null | undefined): AskReplyLang {
  return coerceUILang(raw || "hn");
}
