/**
 * On-screen AstroVastu report language (English / Hinglish / Hindi).
 * Floor plan → Photo Engine; fixes, remedies, scores → kundli + Vastu report engine.
 * Branding: never expose "AI" in user-facing copy.
 */
import { coerceProPdfLang, PRO_PDF_LANG_OPTIONS, type ProPdfLangCode } from "@/lib/proPdfLang";

export type ReportLangCode = ProPdfLangCode;
export { PRO_PDF_LANG_OPTIONS as REPORT_LANG_OPTIONS, coerceProPdfLang };

export function defaultReportLang(appLang: string | undefined): ReportLangCode {
  const l = (appLang || "en").toLowerCase();
  if (l === "hi") return "hi";
  if (l === "hn" || l === "hinglish") return "hn";
  return "en";
}

/** Strip accidental AI branding from engine/API strings (brand rule). */
export function stripAiBranding(text: string): string {
  if (!text) return text;
  return text
    .replace(/Photo Engine AI/gi, "Photo Engine")
    .replace(/\(AI\s*scan\)/gi, "(report engine)")
    .replace(/\(AI\s*स्कैन\)/g, "(रिपोर्ट इंजन)")
    .replace(/\bAI\s+server\b/gi, "server")
    .replace(/\bAI\s+service\b/gi, "analysis service")
    .replace(/\bAI\b/g, "")
    .replace(/\s{2,}/g, " ")
    .replace(/\(\s*\)/g, "")
    .trim();
}

/**
 * en → English
 * hn → Roman Hinglish (summary_hn / hinglish)
 * hi → Devanagari (summary_hi / hindi) — no English fallback on hi chip
 */
export function pickReportLine(
  lang: ReportLangCode,
  en?: string,
  hi?: string,
  hn?: string,
): string {
  const e = stripAiBranding((en || "").trim());
  const h = stripAiBranding((hi || "").trim());
  const r = stripAiBranding((hn || "").trim());
  if (lang === "en") return e;
  if (lang === "hi") return h || e;
  return r || h || e;
}

/** On-screen PRO result chrome — follows report language chips, not app UI language. */
export type ReportUiStrings = {
  headerTitle: string;
  langLabel: string;
  engineNote: string;
  scoreHint: string;
  grade: string;
  detectedTitle: string;
  confidence: string;
  fixTitle: string;
  remedyTitle: string;
  now: string;
  ideal: string;
  remedyLabel: string;
  scanAgain: string;
  emptyTitle: string;
  btnOpenPro: string;
};

const REPORT_UI: Record<ReportLangCode, ReportUiStrings> = {
  en: {
    headerTitle: "Your AstroVastu Report",
    langLabel: "Report language",
    engineNote:
      "Photo Engine reads rooms and directions from your floor plan only. " +
      "All fixes, remedies, and scores below come from your kundli + Vastu report engine — not generic advice.",
    scoreHint: "Your home Vastu score (1–100)",
    grade: "Grade",
    detectedTitle: "From your plan (report engine)",
    confidence: "Scan confidence",
    fixTitle: "Priority fixes (engine)",
    remedyTitle: "Remedies per room (engine)",
    now: "Current",
    ideal: "Ideal",
    remedyLabel: "Remedies",
    scanAgain: "Scan another floor plan",
    emptyTitle: "No report loaded",
    btnOpenPro: "Open AstroVastu PRO",
  },
  hn: {
    headerTitle: "Aapki AstroVastu Report",
    langLabel: "Report language",
    engineNote:
      "Photo Engine sirf aapke floor plan image se rooms aur directions padhta hai. " +
      "Neeche sab fix, remedy aur score aapki kundli + Vastu report engine se hai — generic nahi.",
    scoreHint: "Ghar ka Vastu score (1–100)",
    grade: "Grade",
    detectedTitle: "Aapke plan se (report engine)",
    confidence: "Scan confidence",
    fixTitle: "Kya fix karna hai (engine)",
    remedyTitle: "Remedy har room ke liye (engine)",
    now: "Abhi",
    ideal: "Ideal",
    remedyLabel: "Upaay",
    scanAgain: "Dusra plan scan karein",
    emptyTitle: "Koi report load nahi",
    btnOpenPro: "AstroVastu PRO kholo",
  },
  hi: {
    headerTitle: "आपकी AstroVastu रिपोर्ट",
    langLabel: "रिपोर्ट भाषा",
    engineNote:
      "Photo Engine केवल आपके फ़्लोर प्लान से कमरे और दिशाएँ पढ़ता है। " +
      "नीचे सभी सुधार, उपाय और स्कोर आपकी कुंडली + Vastu रिपोर्ट इंजन से हैं — सामान्य नहीं।",
    scoreHint: "घर का Vastu स्कोर (1–100)",
    grade: "ग्रेड",
    detectedTitle: "आपके प्लान से (रिपोर्ट इंजन)",
    confidence: "स्कैन विश्वास",
    fixTitle: "क्या ठीक करना है (इंजन)",
    remedyTitle: "हर कमरे के उपाय (इंजन)",
    now: "अभी",
    ideal: "आदर्श",
    remedyLabel: "उपाय",
    scanAgain: "दूसरा प्लान स्कैन करें",
    emptyTitle: "कोई रिपोर्ट लोड नहीं",
    btnOpenPro: "AstroVastu PRO खोलें",
  },
};

const SINGLE_ROOM_UI: Record<ReportLangCode, Partial<ReportUiStrings>> = {
  en: {
    engineNote:
      "You confirmed this room from your photo and compass direction. " +
      "Scores and remedies come from your kundli + Vastu report engine for that placement — not generic room tips.",
    detectedTitle: "Your confirmed room (photo + direction)",
    scanAgain: "Scan another room",
  },
  hn: {
    engineNote:
      "Aapne photo aur compass se room + direction confirm kiya. " +
      "Score aur remedy aapki kundli + Vastu report engine se hai — generic kitchen tips nahi.",
    detectedTitle: "Aapka confirmed room (photo + direction)",
    scanAgain: "Dusra room scan karein",
  },
  hi: {
    engineNote:
      "आपने फ़ोटो और कम्पास से कमरा + दिशा पुष्टि की। " +
      "स्कोर और उपाय आपकी कुंडली + Vastu रिपोर्ट इंजन से हैं — सामान्य सुझाव नहीं।",
    detectedTitle: "आपका पुष्टि किया कमरा (फ़ोटो + दिशा)",
    scanAgain: "दूसरा कमरा स्कैन करें",
  },
};

export function getReportUi(
  lang: ReportLangCode,
  scanSource?: string,
): ReportUiStrings {
  const base = REPORT_UI[lang] ?? REPORT_UI.en;
  if (scanSource !== "single_room_photo") return base;
  return { ...base, ...(SINGLE_ROOM_UI[lang] ?? SINGLE_ROOM_UI.en) };
}

export function pickRemedy(
  lang: ReportLangCode,
  r: { english?: string; hindi?: string; hinglish?: string; action?: string },
): string {
  const roman = stripAiBranding((r.hinglish || r.hindi || r.action || "").trim());
  const dev = stripAiBranding((r.hindi || "").trim());
  if (lang === "en") return stripAiBranding((r.english || r.action || "").trim());
  if (lang === "hi") return dev || roman;
  return roman || stripAiBranding((r.english || r.action || "").trim());
}

const VERDICT_HN: Record<string, string> = {
  Ideal: "Ideal (Uttam)",
  Acceptable: "Acceptable (Theek)",
  "Adjustment Needed": "Adjustment Needed (Sudhar)",
  Avoid: "Avoid (Bachiye)",
};

const VERDICT_HI: Record<string, string> = {
  Ideal: "उत्तम",
  Acceptable: "स्वीकार्य",
  "Adjustment Needed": "सुधार ज़रूरी",
  Avoid: "टालें",
};

export function localizeVerdict(lang: ReportLangCode, verdict: string): string {
  if (lang === "hi") return VERDICT_HI[verdict] || verdict;
  if (lang === "hn") return VERDICT_HN[verdict] || verdict;
  return verdict;
}

export function apiLangForVision(reportLang: ReportLangCode): string {
  if (reportLang === "hi") return "hi";
  if (reportLang === "hn") return "hn";
  return "en";
}
