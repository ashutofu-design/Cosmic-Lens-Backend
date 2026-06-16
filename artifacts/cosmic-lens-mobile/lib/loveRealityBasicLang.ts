import { coerceUILang, type UILang } from "@/lib/i18n";

export type LoveBasicLang = UILang;

export function coerceLoveBasicLang(lang?: string | null): LoveBasicLang {
  return coerceUILang(lang || "en");
}

export function pickLoveBasicCopy(
  lang: LoveBasicLang,
  en: string,
  hn: string,
  hi: string,
): string {
  if (lang === "hi") return hi;
  if (lang === "hn") return hn;
  return en;
}
