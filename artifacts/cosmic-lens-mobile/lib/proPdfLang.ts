/** Pro report PDF languages (matches backend PRO_PDF_LANG_CODES / Milan). */
export const PRO_PDF_LANG_CODES = ["en", "hn", "hi"] as const;
export type ProPdfLangCode = (typeof PRO_PDF_LANG_CODES)[number];

export const PRO_PDF_LANG_OPTIONS = [
  { code: "en" as const, native: "English", english: "English" },
  { code: "hn" as const, native: "Hinglish", english: "Roman Hindi" },
  { code: "hi" as const, native: "हिन्दी", english: "Hindi (Devanagari)" },
] as const;

export function coerceProPdfLang(code: string | undefined): ProPdfLangCode {
  const c = (code || "en").toLowerCase();
  return (PRO_PDF_LANG_CODES as readonly string[]).includes(c) ? (c as ProPdfLangCode) : "en";
}

/** Numerology Pro PDF API expects english | hindi | hinglish. */
export function numerologyPdfLangParam(
  code: ProPdfLangCode,
): "english" | "hindi" | "hinglish" {
  if (code === "en") return "english";
  if (code === "hi") return "hindi";
  return "hinglish";
}

/** Face Reading PDF API expects en | hinglish | hi. */
export type FaceReadingPdfLang = "en" | "hinglish" | "hi";

export function faceReadingPdfLangParam(code: ProPdfLangCode): FaceReadingPdfLang {
  if (code === "en") return "en";
  if (code === "hi") return "hi";
  return "hinglish";
}

/** AstroVastu PRO PDF GET ?lang= (matches pdf_renderer aliases). */
export function astrovastuPdfLangParam(code: ProPdfLangCode): FaceReadingPdfLang {
  return faceReadingPdfLangParam(code);
}
