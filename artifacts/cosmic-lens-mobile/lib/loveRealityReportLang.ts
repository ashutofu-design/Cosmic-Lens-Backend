/**
 * Detect whether cached Love Reality Pro text matches requested report language.
 * No imports from loveRealityProReport — avoids Metro circular-import undefined exports.
 */
import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";

const DEVANAGARI = /[\u0900-\u097F]/;
const HINGLISH_STRONG =
  /\b(aap|aapka|aapke|aapki|aapko|rishta|rishte|pyar|kya|hai|hain|nahi|nahin|hoga|hogi|zyada|kam|saath|beech|asli|poori|jyotish|dasha|upay|tumhari|tumhe|dono|bach|karo|karein|yeh|ye|aur|mein|main|ke liye|saath|lagta|rishte)\b/i;

/** Minimal shape for language detection — matches LoveProReportResponse fields we read. */
export type LoveReportLangPayload = {
  lang?: string;
  page1?: {
    relationship_summary?: string;
    insights_narrative?: string;
    verdict?: string;
    key_insights?: string[];
  };
  app_sections?: Array<{
    id?: string;
    body?: string | null;
    bullets?: string[] | null;
  }>;
  content_script?: string;
};

/** Narrative prose only — scorecard lines stay English ("Love: 75/100"). */
const NARRATIVE_SECTION_IDS = new Set([
  "exec_summary",
  "verdict",
  "recommendations",
  "deep_connection",
  "blueprint_vs",
  "root_cause",
  "moon",
]);

function narrativeText(report: LoveReportLangPayload): string {
  const p1 = report.page1;
  const fromPage1 = [
    p1?.relationship_summary,
    p1?.insights_narrative,
    p1?.verdict,
  ].filter(Boolean).join("\n");
  const fromSections = (report.app_sections || [])
    .filter(s => NARRATIVE_SECTION_IDS.has(String(s.id || "").toLowerCase()))
    .map(s => String(s.body || "").trim())
    .filter(Boolean)
    .join("\n");
  const recParas = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "recommendations")
    ?.bullets?.slice(0, 4)
    .join("\n");
  return [fromPage1, fromSections, recParas].filter(Boolean).join("\n");
}

function textLooksHinglish(text: string): boolean {
  const t = text.trim();
  if (!t || t.length < 20) return false;
  if (DEVANAGARI.test(t)) return false;
  return HINGLISH_STRONG.test(t);
}

function textLooksHindi(text: string): boolean {
  const t = text.trim();
  if (!t || t.length < 20) return false;
  const deva = (t.match(DEVANAGARI) || []).length;
  if (deva < 12) return false;
  const letters = (t.match(/[A-Za-z\u0900-\u097F]/g) || []).length;
  return letters < 24 || deva / letters >= 0.28;
}

function textLooksEnglishOnly(text: string): boolean {
  const t = text.trim();
  if (!t) return true;
  if (DEVANAGARI.test(t)) return false;
  if (HINGLISH_STRONG.test(t)) return false;
  return /^[\x00-\x7F\s.,!?;:'"()\-–—/0-9]+$/.test(t.slice(0, 280));
}

/** hn/hi selected but cache/API payload is still English — need fresh LLM. */
export function needsLoveReportLlmRefresh(
  report: LoveReportLangPayload | null | undefined,
  lang: ProPdfLangCode,
  metaContentLang?: string | null,
): boolean {
  if (lang === "en") return false;
  if (!report) return true;
  if (metaContentLang && coerceProPdfLang(metaContentLang) !== lang) return true;
  return !reportSummaryMatchesLang(report, lang);
}

/** Server confirmed Hindi/Hinglish script after localize. */
export function reportScriptMatchesLang(
  report: LoveReportLangPayload,
  lang: ProPdfLangCode,
): boolean {
  const script = (report.content_script || "").trim().toLowerCase();
  if (lang === "hi") return script === "hi" || script === "hi_partial";
  if (lang === "hn") return script === "hn";
  return true;
}

/** True when Update can stop retrying — full Hindi/Hinglish, not mixed English. */
export function reportHindiFullyReady(
  report: LoveReportLangPayload,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return true;
  const script = (report.content_script || "").trim().toLowerCase();
  if (lang === "hi") {
    if (script === "hi") return true;
    if (script && script !== "hi") return false;
    return textLooksHindi(narrativeText(report));
  }
  if (lang === "hn") {
    if (script === "hn") return true;
    if (script && script !== "hn") return false;
    return textLooksHinglish(narrativeText(report));
  }
  return reportSummaryMatchesLang(report, lang);
}

/** Mixed/partial script — keep fetching on Update until fully localized. */
export function reportNeedsHindiRetry(
  report: LoveReportLangPayload,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return false;
  const script = (report.content_script || "").trim().toLowerCase();
  if (script === "en_mismatch" || script === "hi_partial") return true;
  return !reportHindiFullyReady(report, lang);
}

/** Primary check — narrative prose (not English score labels). */
export function reportSummaryMatchesLang(
  report: LoveReportLangPayload,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return true;
  if (reportScriptMatchesLang(report, lang)) return true;
  const text = narrativeText(report);
  if (!text.trim()) return false;
  if (lang === "hi") return textLooksHindi(text);
  if (lang === "hn") return textLooksHinglish(text) && !textLooksEnglishOnly(text);
  return coerceProPdfLang(report.lang) === lang;
}

/** Enough payload to show after Update — do not block the whole screen. */
export function reportHasDisplayableContent(report: LoveReportLangPayload | null | undefined): boolean {
  if (!report?.page1) return false;
  if (Array.isArray(report.app_sections) && report.app_sections.length > 0) return true;
  return Boolean(
    report.page1.relationship_summary
    || report.page1.verdict
    || report.page1.insights_narrative,
  );
}

const SECTION8_MIN_WORDS = 80;
const SECTION8_ENGINE_MARKERS = [
  "mercury mismatch",
  "communication style clash",
  "hidden desire axis",
  "12th house):",
];

function section8RootCauseText(report: LoveReportLangPayload): string {
  const sec = (report.app_sections || []).find(
    s => String(s.id || "").toLowerCase() === "root_cause",
  );
  return String(sec?.body || "").trim();
}

function section8BreakupChapterText(report: LoveReportLangPayload): string {
  const pro = (report as { pro_premium?: { chapters?: Array<{ key?: string; chapter_body?: string; full_read?: string }> } }).pro_premium;
  const ch = (pro?.chapters || []).find(
    c => String(c.key || "").trim().toLowerCase() === "breakup",
  );
  return String(ch?.chapter_body || ch?.full_read || "").trim();
}

function wordCount(text: string): number {
  return (text || "").split(/\s+/).filter(Boolean).length;
}

function proseFullyHindi(text: string): boolean {
  const t = text.trim();
  if (!t || t.length < 40) return false;
  const deva = (t.match(DEVANAGARI) || []).length;
  if (deva < 24) return false;
  const letters = (t.match(/[A-Za-z\u0900-\u097F]/g) || []).length;
  if (letters < 30) return false;
  return deva / letters >= 0.35;
}

/** Section 8 (root_cause) must be full LLM Hindi before Hindi report loads. */
export function section8HiLoadGate(
  report: LoveReportLangPayload | null | undefined,
): { ok: boolean; reason: string } {
  if (!report) {
    return {
      ok: false,
      reason:
        "Report load nahi hua — Section 8 (मूल कारण) data missing hai. Update Report dubara dabayein.",
    };
  }

  const breakup = section8BreakupChapterText(report);
  let root = section8RootCauseText(report);
  if (wordCount(root) < SECTION8_MIN_WORDS && wordCount(breakup) >= SECTION8_MIN_WORDS) {
    root = breakup;
  }

  if (!breakup) {
    if (!root) {
      return {
        ok: false,
        reason:
          "Report load nahi hua — Section 8 (मूल कारण) bilkul khali hai. "
          + "LLM ne breakup chapter generate nahi kiya. Niche «Update Report» dabayein.",
      };
    }
    return {
      ok: false,
      reason:
        "Report load nahi hua — LLM breakup chapter save nahi hua "
        + "(sirf engine text mila). Niche «Update Report» dabayein.",
    };
  }

  const breakupWc = wordCount(breakup);
  if (breakupWc < SECTION8_MIN_WORDS) {
    return {
      ok: false,
      reason:
        `Report load nahi hua — Section 8 LLM explanation bahut chhota hai `
        + `(${breakupWc} words, kam se kam ${SECTION8_MIN_WORDS} chahiye). `
        + "OpenAI poora paragraph nahi likh paya — Update dubara try karein.",
    };
  }

  const rootWc = wordCount(root);
  if (rootWc < SECTION8_MIN_WORDS) {
    return {
      ok: false,
      reason:
        `Report load nahi hua — Section 8 screen text incomplete hai `
        + `(${rootWc} words). LLM chapter poora map nahi hua — Update dubara dabayein.`,
    };
  }

  const rootLower = root.toLowerCase();
  for (const marker of SECTION8_ENGINE_MARKERS) {
    if (rootLower.includes(marker) && breakupWc < SECTION8_MIN_WORDS) {
      return {
        ok: false,
        reason:
          "Report load nahi hua — Section 8 par purana English engine text aa raha hai, "
          + "LLM Hindi explanation nahi. Update Report se fresh LLM chalao.",
      };
    }
  }

  if (!proseFullyHindi(breakup)) {
    const deva = (breakup.match(DEVANAGARI) || []).length;
    return {
      ok: false,
      reason:
        "Report load nahi hua — Section 8 LLM text abhi poori देवनागरी Hindi nahi hai "
        + `(Devanagari chars: ${deva}). Mixed/English lines hain — Update dubara dabayein.`,
    };
  }
  if (!proseFullyHindi(root)) {
    return {
      ok: false,
      reason:
        "Report load nahi hua — Section 8 display text Hindi me convert nahi hua. "
        + "Update Report dubara dabayein.",
    };
  }

  return { ok: true, reason: "" };
}

export function section8HiLoadReady(
  report: LoveReportLangPayload | null | undefined,
  lang: ProPdfLangCode,
): boolean {
  if (lang !== "hi") return true;
  return section8HiLoadGate(report).ok;
}

/** True when saved JSON body matches the language user selected. */
export function reportContentMatchesLang(
  report: LoveReportLangPayload,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return true;
  if (coerceProPdfLang(report.lang) !== lang) return false;
  return reportSummaryMatchesLang(report, lang);
}
