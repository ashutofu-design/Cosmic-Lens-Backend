/**
 * Detect whether cached Love Reality Pro text matches requested report language.
 */
import type { LoveProReportResponse } from "@/lib/loveRealityProReport";
import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";

const DEVANAGARI = /[\u0900-\u097F]/;
const HINGLISH_STRONG =
  /\b(aap|aapka|aapke|aapki|aapko|rishta|rishte|pyar|kya|hai|hain|nahi|nahin|hoga|hogi|zyada|kam|saath|beech|asli|poori|jyotish|dasha|upay|tumhari|tumhe|dono|bach|karo|karein|yeh|ye|aur|mein|main|ke liye|saath|lagta|rishte)\b/i;

function execSummaryText(report: LoveProReportResponse): string {
  const p1 = report.page1;
  return [
    p1?.relationship_summary,
    p1?.insights_narrative,
    ...(p1?.key_insights || []).slice(0, 3),
  ].filter(Boolean).join("\n");
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
  return (t.match(DEVANAGARI) || []).length >= 6;
}

function textLooksEnglishOnly(text: string): boolean {
  const t = text.trim();
  if (!t) return true;
  if (DEVANAGARI.test(t)) return false;
  if (HINGLISH_STRONG.test(t)) return false;
  return /^[\x00-\x7F\s.,!?;:'"()\-–—/0-9]+$/.test(t.slice(0, 280));
}

/** Primary check — exec summary block user sees first. */
export function reportSummaryMatchesLang(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return true;
  const text = execSummaryText(report);
  if (!text.trim()) return false;
  if (lang === "hi") return textLooksHindi(text);
  if (lang === "hn") return textLooksHinglish(text) && !textLooksEnglishOnly(text);
  return coerceProPdfLang(report.lang) === lang;
}

/** True when saved JSON body matches the language user selected. */
export function reportContentMatchesLang(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
): boolean {
  if (lang === "en") return true;
  if (coerceProPdfLang(report.lang) !== lang) return false;
  return reportSummaryMatchesLang(report, lang);
}

/** hn/hi selected but cache/API payload is still English — need fresh LLM. */
export function needsLoveReportLlmRefresh(
  report: LoveProReportResponse | null | undefined,
  lang: ProPdfLangCode,
  metaContentLang?: string | null,
): boolean {
  if (lang === "en") return false;
  if (!report) return true;
  if (metaContentLang && coerceProPdfLang(metaContentLang) !== lang) return true;
  return !reportSummaryMatchesLang(report, lang);
}
