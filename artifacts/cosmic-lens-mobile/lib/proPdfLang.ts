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

/** My Reports title / success alert — English, Hinglish, or हिन्दी. */
export function proPdfLangDisplayName(code: ProPdfLangCode): string {
  const opt = PRO_PDF_LANG_OPTIONS.find(o => o.code === code);
  return opt?.native ?? "English";
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

/** Language picker modal — title, subtitle, buttons follow selected highlight lang. */
export function proPdfLangPickerUi(uiLang: ProPdfLangCode) {
  if (uiLang === "hi") {
    return {
      title: "रिपोर्ट की भाषा चुनें",
      subtitle: "English, Hinglish या Hindi",
      deliveryHead: "डिलीवरी",
      deliveryLine: "My Reports में सेव · More से खोलें",
      priorityRefund:
        "१२-घंटे प्राथमिकता गारंटी — १२ घंटे की डिलीवरी छूटने पर केवल प्राथमिकता शुल्क १००% वापस।",
      cancel: "रद्द करें",
      continue: "ऑर्डर करें",
    };
  }
  if (uiLang === "hn") {
    return {
      title: "Report Language Chunein",
      subtitle: "English, Hinglish ya Hindi",
      deliveryHead: "Delivery",
      deliveryLine: "My Reports · 4–6 business days",
      priorityRefund: "12-hour Priority Guarantee — 12 ghante miss hue to Priority fee 100% refund.",
      cancel: "Cancel",
      continue: "Order karo",
    };
  }
  return {
    title: "Report Language",
    subtitle: "English, Hinglish, or Hindi",
    deliveryHead: "Delivery",
      deliveryLine: "My Reports · 4–6 business days",
      priorityRefund: "12-hour Priority Guarantee — If we miss the 12-hour delivery window, your Priority fee is 100% refunded.",
    cancel: "Cancel",
    continue: "Place order",
  };
}

/** Short explain line under each language option (in picker UI language). */
export function proPdfLangOptionExplain(
  optionCode: ProPdfLangCode,
  uiLang: ProPdfLangCode,
): string {
  const table: Record<ProPdfLangCode, Record<ProPdfLangCode, string>> = {
    en: {
      en: "Full report in English",
      hn: "Full report in Roman Hinglish",
      hi: "Full report in Devanagari Hindi",
    },
    hn: {
      en: "Poori report English mein",
      hn: "Poori report Roman Hinglish mein",
      hi: "Poori report Devanagari Hindi mein",
    },
    hi: {
      en: "पूरी रिपोर्ट अंग्रेज़ी में",
      hn: "पूरी रिपोर्ट रोमन हिंग्लिश में",
      hi: "पूरी रिपोर्ट देवनागरी हिंदी में",
    },
  };
  return table[uiLang][optionCode];
}
