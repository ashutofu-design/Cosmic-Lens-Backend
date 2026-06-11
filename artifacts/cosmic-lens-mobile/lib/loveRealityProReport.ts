/**
 * Love Reality Pro — in-app full report (JSON from server, PDF-parity layout).
 */
import { API_BASE } from "@/lib/apiConfig";
import { pdfAuthHeaders } from "@/lib/coupleReportCheckoutFlow";
import { packLovePerson } from "@/lib/loveRealityPack";
import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";
import type { BirthData } from "@/types";

export type LoveProDeepAnalysis = {
  key?: string;
  title?: string;
  score?: number;
  explanation?: string;
};

export type LoveProChapter = {
  key?: string;
  title?: string;
  chapter_body?: string;
  full_read?: string;
  grounding?: string;
};

export type LoveProPremium = {
  verdict?: string;
  hidden_truth?: string;
  blueprint_reality?: string;
  harmony?: string;
  moon_sync_narrative?: string;
  red_flags_narrative?: string;
  dasha_narrative?: string;
  roadmap_narrative?: string;
  deep_analysis?: LoveProDeepAnalysis[];
  chapters?: LoveProChapter[];
  special?: string[];
  damage?: string[];
  practical?: string[];
  remedies_action_narrative?: string;
  action_steps?: string[];
  _meta?: {
    pdf_generation?: {
      estimated_cost_inr?: number;
    };
    sections?: Record<string, {
      pdf_generation?: { estimated_cost_inr?: number };
    }>;
  };
};

export type LovePdfContext = {
  page1_dashboard?: {
    summary_index?: string;
    love_score?: number;
    scores?: { label?: string; value?: string; band?: string }[];
  };
  page2_3_blueprint?: { part1?: string; part2?: string };
  page4_dimensions?: { label?: string; score?: number; key?: string }[];
  page5_moon?: {
    p1_moon?: string;
    p2_moon?: string;
    body?: string;
    notes?: string[];
    shashtashtak?: boolean;
  };
  page6_root_cause?: string;
  page7_loyalty?: {
    body?: string;
    summary?: string;
    behavior?: string;
    rows?: { label?: string; value?: string; band?: string }[];
  };
  page8_red_flags?: { body?: string; bullets?: string[] };
  page9_harmony?: string;
  page10_dasha?: { body?: string; lines?: string[] };
  page11_roadmap?: {
    body?: string;
    rows?: { period?: string; trend?: string; note?: string }[];
  };
  page12_remedies?: { body?: string; bullets?: string[] };
  page13_checklist?: { body?: string; bullets?: string[] };
  page14_closing?: string;
};

export type LovePage1Dashboard = {
  report_id?: string;
  cosmic_score?: number;
  relationship_summary?: string;
  insights_narrative?: string;
  key_insights?: string[];
  metrics?: { label?: string; value?: number; interpretation?: string }[];
  analysis?: { title?: string; score?: number; explanation?: string }[];
  strengths?: { label?: string; value?: number }[];
  challenges?: { label?: string; value?: number }[];
  verdict?: string;
  recommendations?: string[];
  recommendation_paragraphs?: string[];
};

export type LoveProReportResponse = {
  ok: boolean;
  lang: string;
  p1_name: string;
  p2_name: string;
  polish_source?: string;
  scores: {
    love: number;
    breakup: number;
    loyalty: number;
    return: number;
    future: number;
  };
  pro_premium: LoveProPremium;
  pdf_context?: LovePdfContext;
  page1?: LovePage1Dashboard;
  /** Server-built scroll sections (Update Report) — render these, not a local rebuild. */
  app_sections?: Array<{
    id: string;
    body?: string | null;
    bullets?: string[] | null;
  }>;
  /** hi | hn | en | en_mismatch — server check after localize. */
  content_script?: string;
  /** Rounded OpenAI cost in INR (operator) — English UI only. */
  llm_cost_inr?: number;
  /** Canonical Hindi deep_connection (विस्तार) body from server. */
  section3_hi_body?: string | null;
  /** Canonical Hindi recommendations (उपाय और आगे क्या करें) body from server. */
  section4_hi_body?: string | null;
  section5_hi_body?: string | null;
  section7_hi_body?: string | null;
  section7_debug?: {
    moon_narr_words?: number;
    moon_narr_deva?: number;
    moon_body_words?: number;
    moon_body_deva?: number;
  };
  /** Canonical Hindi Section 8 body — server gate passed. */
  section8_hi_body?: string | null;
  hi_cache_ver?: string | null;
  /** Server LLM assembly version — bump invalidates en/hn device cache. */
  polish_assembly?: string | null;
  section8_debug?: {
    gate_ver?: string;
    breakup_words?: number;
    breakup_deva?: number;
    root_words?: number;
    root_deva?: number;
    effective_words?: number;
    effective_deva?: number;
  };
};

export type LoveReportSection = {
  id: string;
  title: string;
  subtitle?: string;
  body?: string;
  bullets?: string[];
  tableRows?: string[][];
  /** PDF section number when this card maps to a numbered PDF chapter (e.g. root_cause = 8). */
  pdfSectionNo?: number;
};

/** In-app badge numbers aligned with Love Reality PDF chapters (not scroll index). */
const PDF_SECTION_NO: Record<string, number> = {
  blueprint_vs: 5,
  moon: 7,
  root_cause: 8,
};

export function loveReportPdfSectionNo(sectionId: string): number | undefined {
  return PDF_SECTION_NO[String(sectionId || "").toLowerCase()];
}

function annotatePdfSectionNo(sections: LoveReportSection[]): LoveReportSection[] {
  return sections.map(sec => {
    const pdfNo = loveReportPdfSectionNo(sec.id);
    return pdfNo != null ? { ...sec, pdfSectionNo: pdfNo } : sec;
  });
}

function breakupChapterBody(report: LoveProReportResponse): string {
  const ch = (report.pro_premium?.chapters || []).find(
    c => String(c.key || "").trim().toLowerCase() === "breakup",
  );
  return String(ch?.chapter_body || ch?.full_read || "").trim();
}

function devaCount(text: string): number {
  return (text.match(/[\u0900-\u097F]/g) || []).length;
}

function wordCountText(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

function proseFullyHindi(text: string): boolean {
  const t = String(text || "").trim();
  if (!t || t.length < 40) return false;
  const deva = devaCount(t);
  if (deva < 12) return false;
  const letters = (t.match(/[A-Za-z\u0900-\u097F]/g) || []).length;
  if (letters < 20) return deva >= 8;
  return deva / letters >= 0.32;
}

function proseLaneOk(text: string, lang: ProPdfLangCode): boolean {
  const t = String(text || "").trim();
  if (!t) return false;
  const deva = devaCount(t);
  if (lang === "en") return deva < 3;
  if (lang === "hi") return deva >= 12;
  if (lang === "hn") return deva < 6;
  return true;
}

function normalizeProseParagraphs(text: string, minParagraphs = 3): string {
  const raw = String(text || "").trim();
  if (!raw) return raw;
  if (proseParagraphFormOk(raw, minParagraphs, 18)) return raw;
  const flat = raw.replace(/\s*\n\s*/g, " ");
  const sentences = flat.split(/(?<=[।.!?])\s+/).map(s => s.trim()).filter(Boolean);
  if (sentences.length < minParagraphs) return raw;
  const perPara = Math.max(2, Math.ceil(sentences.length / minParagraphs));
  const paras: string[] = [];
  for (let i = 0; i < sentences.length; i += perPara) {
    const chunk = sentences.slice(i, i + perPara);
    if (chunk.length) paras.push(chunk.join(" "));
  }
  const out = paras.join("\n\n");
  return proseParagraphFormOk(out, minParagraphs, 18) ? out : raw;
}

function section8LoadReady(text: string): boolean {
  const t = normalizeProseParagraphs(String(text || "").trim());
  return wordCountText(t) >= 80 && devaCount(t) >= 24 && proseFullyHindi(t);
}

/** Best Hindi Section 8 text — server canonical body, breakup chapter, or root_cause. */
export function effectiveSection8HiText(report: LoveProReportResponse): string {
  const canon = normalizeProseParagraphs(String(report.section8_hi_body || "").trim());
  if (canon && section8LoadReady(canon)) return canon;

  const breakup = breakupChapterBody(report);
  const fromCtx = String(report.pdf_context?.page6_root_cause || "").trim();
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "root_cause");
  const root = String(fromSec?.body || "").trim() || fromCtx;

  let best = "";
  let bestDeva = -1;
  for (const raw of [breakup, root]) {
    const text = normalizeProseParagraphs(String(raw || "").trim());
    if (!text) continue;
    const deva = devaCount(text);
    const wc = wordCountText(text);
    if (wc >= 80 && deva > bestDeva) {
      best = text;
      bestDeva = deva;
    }
  }
  return best || normalizeProseParagraphs(breakup || root || canon);
}

const MOON_ENGINE_FALLBACK_HI =
  /चंद्र संकेत सहज भावनात्मक लय|षष्ठाष्टक.*६-८ राशि चंद्र/;

const BLUEPRINT_JARGON_RE =
  /(?:7th|8th|12th)\s+house|upapada|house\s+lord|lagna|venus\s*:|jupiter\s*:|mercury\s*\(|occupants|nakshatra|उपापदा|अरुधा|लग्न|घर\s*स्वामी|७वीं?\s*भाव|शुक्र\s*:|गुरु\s*:/i;

function blueprintHasJargon(text: string): boolean {
  return BLUEPRINT_JARGON_RE.test(text || "");
}

const BULLET_LINE_RE = /^\s*(?:[•\-*►▪]|(?:\d+[.)]))\s+/m;

function textLooksLikePointList(text: string): boolean {
  const raw = String(text || "").trim();
  if (!raw) return true;
  if (BULLET_LINE_RE.test(raw)) return true;
  if (/chart signals|engine facts|•\s/i.test(raw)) return true;
  if (!raw.includes("\n\n")) {
    const lines = raw.split("\n").map(l => l.trim()).filter(Boolean);
    if (lines.length >= 3) {
      const avg = lines.reduce((n, l) => n + wordCountText(l), 0) / lines.length;
      if (avg < 22) return true;
    }
  }
  return false;
}

function proseParagraphFormOk(
  text: string,
  minParagraphs = 3,
  minParaWords = 18,
): boolean {
  const raw = String(text || "").trim();
  if (!raw || textLooksLikePointList(raw)) return false;
  const paras = raw.split(/\n\s*\n+/).map(p => p.trim()).filter(Boolean);
  if (paras.length < minParagraphs) return false;
  const good = paras.filter(p => wordCountText(p) >= minParaWords).length;
  return good >= minParagraphs;
}

function blueprintBodyReady(text: string, lang: ProPdfLangCode): boolean {
  const norm = normalizeProseParagraphs(String(text || "").trim());
  const scriptOk = lang === "hi" ? devaCount(norm) >= 24 : proseLaneOk(norm, lang);
  return (
    wordCountText(norm) >= 80
    && !blueprintHasJargon(norm)
    && scriptOk
    && proseParagraphFormOk(norm, 3, 18)
  );
}

function narrativeBodyReady(
  text: string,
  minWords: number,
  lang: ProPdfLangCode,
  minParaWords = 15,
): boolean {
  const norm = normalizeProseParagraphs(String(text || "").trim());
  const scriptOk = lang === "hi" ? devaCount(norm) >= 24 : proseLaneOk(norm, lang);
  return (
    wordCountText(norm) >= minWords
    && scriptOk
    && !textLooksLikePointList(norm)
    && proseParagraphFormOk(norm, 3, minParaWords)
  );
}

function narrativeBodyFallback(text: string, minWords: number, lang: ProPdfLangCode): string {
  const norm = normalizeProseParagraphs(String(text || "").trim());
  const scriptOk = lang === "hi" ? devaCount(norm) >= 24 : proseLaneOk(norm, lang);
  if (wordCountText(norm) >= minWords && scriptOk && !textLooksLikePointList(norm)) {
    return norm;
  }
  return "";
}

const DEEP_ANALYSIS_TITLES_HI: Record<string, string> = {
  emotional: "भावनात्मक अनुकूलता",
  communication: "संवाद",
  trust: "विश्वास और निष्ठा",
  long_term: "दीर्घकालिक संभावना",
};

const DEEP_ANALYSIS_TITLES_EN: Record<string, string> = {
  emotional: "Emotional Compatibility",
  communication: "Communication",
  trust: "Trust & Loyalty",
  long_term: "Long-Term Potential",
};

function deepAnalysisTitle(key: string, lang: ProPdfLangCode): string {
  if (lang === "hi") return DEEP_ANALYSIS_TITLES_HI[key] || key;
  return DEEP_ANALYSIS_TITLES_EN[key] || key;
}

function deepConnectionBodyReady(text: string, lang: ProPdfLangCode): boolean {
  const norm = normalizeProseParagraphs(String(text || "").trim());
  if (wordCountText(norm) < 200 || textLooksLikePointList(norm)) return false;
  if (lang === "hi") return devaCount(norm) >= 48;
  return proseLaneOk(norm, lang);
}

function recommendationsBodyReady(text: string, lang: ProPdfLangCode): boolean {
  const norm = normalizeProseParagraphs(String(text || "").trim());
  const scriptOk = lang === "hi" ? devaCount(norm) >= 24 : proseLaneOk(norm, lang);
  return wordCountText(norm) >= 80 && scriptOk && !textLooksLikePointList(norm);
}

/** Full LLM remedies + action plan — उपाय और आगे क्या करें (recommendations section). */
export function resolveRecommendationsBody(
  report: LoveProReportResponse,
  lang: ProPdfLangCode = "en",
): string {
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "recommendations");
  const candidates = [
    lang === "hi" ? String(report.section4_hi_body || "").trim() : "",
    String(report.pro_premium?.remedies_action_narrative || "").trim(),
    (report.page1?.recommendation_paragraphs || [])
      .map(p => String(p || "").trim())
      .filter(Boolean)
      .join("\n\n"),
    String(fromSec?.body || "").trim(),
  ]
    .filter(Boolean)
    .map(t => normalizeProseParagraphs(t));

  for (const text of candidates) {
    if (recommendationsBodyReady(text, lang)) return text;
  }
  for (const text of candidates) {
    const scriptOk = lang === "hi" ? devaCount(text) >= 24 : proseLaneOk(text, lang);
    if (wordCountText(text) >= 55 && scriptOk && !textLooksLikePointList(text)) {
      return text;
    }
  }
  return candidates.find(t => t.length > 0 && proseLaneOk(t, lang)) || "";
}

export function resolveRecommendationsBullets(report: LoveProReportResponse): string[] {
  const steps = (report.pro_premium?.action_steps || [])
    .map(s => String(s || "").trim())
    .filter(Boolean);
  if (steps.length) return steps.slice(0, 7);

  const fromP1 = (report.page1?.recommendations || [])
    .map(s => String(s || "").trim())
    .filter(Boolean);
  if (fromP1.length) return fromP1.slice(0, 7);

  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "recommendations");
  return (fromSec?.bullets || [])
    .map(s => String(s || "").trim())
    .filter(Boolean)
    .slice(0, 7);
}

/** Full LLM deep connection — 4 dimensions (विस्तार / Deep Connection section). */
export function resolveDeepConnectionBody(
  report: LoveProReportResponse,
  lang: ProPdfLangCode = "en",
): string {
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "deep_connection");
  const secBody = String(fromSec?.body || "").trim();
  const candidates: string[] = [];
  if (lang === "hi") {
    const canon = String(report.section3_hi_body || "").trim();
    if (canon) candidates.push(canon);
  }
  if (secBody) candidates.push(secBody);

  for (const text of candidates.map(t => normalizeProseParagraphs(t))) {
    if (deepConnectionBodyReady(text, lang)) return text;
  }

  const lines: string[] = [];
  for (const row of report.pro_premium?.deep_analysis || []) {
    if (!row || typeof row !== "object") continue;
    const key = String(row.key || "").toLowerCase();
    const expl = String(row.explanation || "").trim();
    if (wordCountText(expl) < 55 || !proseLaneOk(expl, lang)) continue;
    const title = deepAnalysisTitle(key, lang);
    lines.push(`${title}\n${expl}`);
  }
  if (lines.length >= 2) return lines.join("\n\n");

  const p1Lines: string[] = [];
  for (const item of report.page1?.analysis || []) {
    if (!item || typeof item !== "object") continue;
    const expl = String(item.explanation || "").trim();
    if (wordCountText(expl) < 40 || !proseLaneOk(expl, lang)) continue;
    const title = String(item.title || "Analysis").trim();
    p1Lines.push(`${title}\n${expl}`);
  }
  if (p1Lines.length >= 2) return p1Lines.join("\n\n");

  return candidates.find(t => proseLaneOk(t, lang)) || "";
}

/** Plain blueprint narrative — no planet/house engine dump (Section 5). */
export function resolveBlueprintVsBody(
  report: LoveProReportResponse,
  lang: ProPdfLangCode = "en",
): string {
  const narr = String(report.pro_premium?.blueprint_reality || "").trim();
  const fromCtx = String(report.pdf_context?.page2_3_blueprint?.part2 || "").trim();
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "blueprint_vs");
  const body = String(fromSec?.body || "").trim() || fromCtx;
  const canon = lang === "hi" ? String(report.section5_hi_body || "").trim() : "";

  for (const text of [canon, narr, body].filter(Boolean)) {
    if (blueprintBodyReady(text, lang)) return text;
  }
  for (const text of [canon, narr, body].filter(Boolean)) {
    const fallback = narrativeBodyFallback(text, 80, lang);
    if (fallback && !blueprintHasJargon(fallback)) return fallback;
  }
  return "";
}

/** Prefer LLM moon_sync_narrative over engine one-liner for Section 7. */
export function resolveMoonSyncBody(
  report: LoveProReportResponse,
  lang: ProPdfLangCode = "en",
): string {
  const narr = String(report.pro_premium?.moon_sync_narrative || "").trim();
  const fromCtx = String(report.pdf_context?.page5_moon?.body || "").trim();
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "moon");
  const moon = String(fromSec?.body || "").trim() || fromCtx;
  const canon = lang === "hi" ? String(report.section7_hi_body || "").trim() : "";

  const candidates = [canon, narr, moon].filter(
    t => t && (lang === "hi" ? !MOON_ENGINE_FALLBACK_HI.test(t) : proseLaneOk(t, lang)),
  );
  for (const text of candidates) {
    if (narrativeBodyReady(text, 55, lang)) return text;
  }
  for (const text of candidates) {
    const fallback = narrativeBodyFallback(text, 55, lang);
    if (fallback) return fallback;
  }
  return "";
}

function section8NarrativeReady(text: string, lang: ProPdfLangCode): boolean {
  const t = normalizeProseParagraphs(String(text || "").trim());
  if (!narrativeBodyReady(t, 80, lang, 18)) return false;
  if (textLooksLikePointList(t)) return false;
  if (lang === "hi") return proseFullyHindi(t);
  return proseLaneOk(t, lang);
}

/** Prefer LLM breakup chapter for Section 8 when app_sections root_cause is stale/thin. */
export function resolveSection8RootCauseBody(
  report: LoveProReportResponse,
  lang: ProPdfLangCode = "en",
): string {
  if (lang === "hi") {
    const effective = effectiveSection8HiText(report);
    if (effective) return effective;
  }
  const breakup = breakupChapterBody(report);
  if (section8NarrativeReady(breakup, lang)) {
    return normalizeProseParagraphs(breakup);
  }
  const fromCtx = String(report.pdf_context?.page6_root_cause || "").trim();
  const fromSec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "root_cause");
  const root = String(fromSec?.body || "").trim() || fromCtx;
  if (section8NarrativeReady(root, lang)) {
    return normalizeProseParagraphs(root);
  }
  return breakup || root;
}

function pushSection(sections: LoveReportSection[], sec: LoveReportSection | null | undefined) {
  if (!sec) return;
  const hasBody = (sec.body || "").trim().length > 0;
  const hasBullets = (sec.bullets || []).some(b => b.trim().length > 0);
  const hasTable = (sec.tableRows || []).length > 0;
  if (hasBody || hasBullets || hasTable) sections.push(sec);
}

/** In-app scroll — never show PDF teaser / download promo cards. */
const IN_APP_HIDDEN_SECTION_IDS = new Set(["pdf_teaser"]);

export function filterInAppReportSections(sections: LoveReportSection[]): LoveReportSection[] {
  return sections.filter(s => !IN_APP_HIDDEN_SECTION_IDS.has(s.id.toLowerCase()));
}

function pickLabel(lang: ProPdfLangCode, en: string, hn: string, hi: string): string {
  if (lang === "hi") return hi;
  if (lang === "hn") return hn;
  return en;
}

function L(lang: ProPdfLangCode) {
  return {
    execSummary: pickLabel(
      lang,
      "Executive Summary & Cosmic Alignment",
      "Rishte ka Summary aur Cosmic Score",
      "रिश्ते का सारांश और कॉस्मिक स्कोर",
    ),
    relSummary: pickLabel(
      lang,
      "Relationship Summary",
      "Stars kya keh rahe hain",
      "तारे क्या कह रहे हैं",
    ),
    coreMetrics: pickLabel(lang, "Core Metrics", "Core Scores", "मुख्य स्कोर"),
    scorecard: pickLabel(lang, "Your Connection Scorecard", "Aapka Connection Scorecard", "आपका कनेक्शन स्कोरकार्ड"),
    cosmicScore: (n: number) => pickLabel(
      lang,
      `Cosmic Alignment Score: ${n}/100`,
      `Cosmic Score: ${n}/100`,
      `कॉस्मिक संरेखण स्कोर: ${n}/100`,
    ),
    insights: pickLabel(lang, "Relationship Insights", "Rishte ki Insights", "रिश्ते की अंतर्दृष्टि"),
    strengths: pickLabel(lang, "Strengths in this Connection", "Is Rishte ki Strengths", "इस कनेक्शन की ताकत"),
    challenges: pickLabel(lang, "Challenges in this Connection", "Is Rishte ki Challenges", "इस कनेक्शन की चुनौतियाँ"),
    verdict: pickLabel(lang, "Final Cosmic Verdict", "Final Cosmic Verdict", "अंतिम ज्योतिषीय निष्कर्ष"),
    verdictSub: pickLabel(lang, "Astrologer's Note", "Jyotishi ka Note", "ज्योतिषी का नोट"),
    recommendations: pickLabel(lang, "Remedies & Next Steps", "Upay aur Aage Kya Karein", "उपाय और आगे क्या करें"),
    recommendationsSub: pickLabel(
      lang,
      "Practical remedies · daily habits · next 3–12 months",
      "Practical upay · daily habits · agle 3–12 mahine",
      "व्यावहारिक उपाय · दैनिक आदत · अगले ३–१२ महीने",
    ),
    deepAnalysis: pickLabel(lang, "Deep Connection Analysis", "Gehra Connection Analysis", "गहन कनेक्शन विश्लेषण"),
    deepCombined: pickLabel(lang, "Deep Connection Analysis", "Gehra Connection Analysis", "गहन कनेक्शन विश्लेषण"),
    deepSub: pickLabel(
      lang,
      "Emotional · Communication · Trust · Long-term",
      "Emotional · Communication · Trust · Long-term",
      "भावनात्मक · संवाद · विश्वास · दीर्घकाल",
    ),
    blueprintYou: pickLabel(
      lang,
      "Destiny Partner Blueprint (You)",
      "Aapka Destiny Partner Blueprint",
      "आपका भाग्य साथी ब्लूप्रिंट",
    ),
    blueprintVs: pickLabel(
      lang,
      "Partner Blueprint vs Reality",
      "Ideal Partner vs Asli Reality",
      "आदर्श साथी बनाम वास्तविकता",
    ),
    blueprintVsSub: pickLabel(
      lang,
      "How your ideal partner pattern compares to reality",
      "Aapke ideal partner pattern vs asli partner",
      "आदर्श पैटर्न बनाम वास्तविक साथी",
    ),
    dimensions: pickLabel(
      lang,
      "The 5 Love Dimensions Deep-Dive",
      "5 Love Dimensions — Detail",
      "५ प्रेम आयाम — विस्तार",
    ),
    moon: pickLabel(
      lang,
      "Moon Synastry & Emotional Rhythm",
      "Moon Match aur Emotional Rhythm",
      "चंद्र समन्वय और भावनात्मक लय",
    ),
    moonSub: pickLabel(
      lang,
      "Emotional rhythm between you two",
      "Aap dono ke beech emotional rhythm",
      "आप दोनों के बीच भावनात्मक लय",
    ),
    moonYour: pickLabel(lang, "Your Moon", "Aapka Moon", "आपका चंद्र"),
    moonPartner: pickLabel(lang, "Partner Moon", "Partner ka Moon", "साथी का चंद्र"),
    rootCause: pickLabel(lang, "The Core Root Cause", "Asli Root Cause", "मूल वजह"),
    rootCauseSub: pickLabel(
      lang,
      "What is silently breaking you apart",
      "Kya chupke aapko alag kar raha hai",
      "क्या चुपचाप आपको अलग कर रहा है",
    ),
    loyalty: pickLabel(
      lang,
      "Loyalty, Trust & Psychological Traits",
      "Loyalty, Trust aur Traits",
      "निष्ठा, विश्वास और लक्षण",
    ),
    redFlags: pickLabel(lang, "Red Flags Matrix", "Red Flags", "चेतावनी संकेत"),
    harmony: pickLabel(lang, "The Harmony Formula", "Harmony Formula", "सामंजस्य सूत्र"),
    dasha: pickLabel(lang, "Vimshottari Dasha Synchronization", "Dasha Sync", "विंशोत्तरी दशा"),
    roadmap: pickLabel(lang, "The 1–3 Year Chronological Roadmap", "1–3 Saal ka Roadmap", "१–३ वर्ष का रोडमैप"),
    upay: pickLabel(lang, "Planetary Counter Measures (Upay)", "Upay aur Remedies", "उपाय और सुझाव"),
    checklist: pickLabel(lang, "Relationship Checklist", "Relationship Checklist", "रिश्ते की चेकलिस्ट"),
    closing: pickLabel(lang, "Closing Guidance & Disclaimer", "Closing Note", "अंतिम मार्गदर्शन"),
    pdfNote: pickLabel(lang, "Full chart detail in PDF", "Poori detail PDF mein", "पूरी जानकारी PDF में"),
    pdfTeaserSub: pickLabel(
      lang,
      "Dasha · Roadmap · Remedies · Full blueprint",
      "Dasha · Roadmap · Upay · Poora blueprint",
      "दशा · रोडमैप · उपाय · पूरा ब्लूप्रिंट",
    ),
    pdfTeaserBody: pickLabel(
      lang,
      "Tap Download PDF below for the complete 18-page report with timelines, remedies, and full chart detail.",
      "Neeche Download PDF dabao — poori 18-page report timelines, upay aur chart detail ke saath.",
      "नीचे PDF डाउनलोड करें — पूरी १८-पृष्ठ रिपोर्ट।",
    ),
    scoreLove: pickLabel(lang, "Love", "Love", "प्रेम"),
    scoreBreakup: pickLabel(lang, "Breakup", "Breakup", "ब्रेकअप"),
    scoreLoyalty: pickLabel(lang, "Loyalty", "Loyalty", "निष्ठा"),
    scoreReturn: pickLabel(lang, "Return", "Return", "वापसी"),
    scoreFuture: pickLabel(lang, "Future", "Future", "भविष्य"),
    proBadge: pickLabel(lang, "PRO REPORT", "PRO REPORT", "PRO रिपोर्ट"),
    heroTitle: pickLabel(lang, "Love Reality Pro", "Love Reality Pro", "Love Reality Pro"),
    downloadPdf: pickLabel(lang, "Download PDF", "PDF Download karo", "PDF डाउनलोड"),
    downloadingPdf: pickLabel(lang, "Downloading PDF…", "PDF download ho rahi hai…", "PDF डाउनलोड…"),
    downloadHint: pickLabel(
      lang,
      "Full report from this page — saved to My Reports",
      "Is page se poori report — My Reports mein save hogi",
      "इस पेज से पूरी रिपोर्ट — My Reports में",
    ),
    cosmicAlignment: pickLabel(lang, "Cosmic Alignment", "Cosmic Alignment", "कॉस्मिक संरेखण"),
    moonDetailSub: pickLabel(
      lang,
      "Shashtashtak / 6-8 sign emotional alignment check",
      "Shashtashtak / 6-8 sign emotional check",
      "षष्ठाष्टक / ६-८ राशि भावनात्मक जाँच",
    ),
    chipOverview: pickLabel(lang, "Overview", "Poora Overview", "सारांश"),
    chipScores: pickLabel(lang, "Scores", "Scores", "स्कोर"),
    chipFullPdf: pickLabel(lang, "Full PDF", "Poori PDF", "पूरी PDF"),
    chipDeepDive: pickLabel(lang, "Deep Dive", "Deep Dive", "विस्तार"),
    chipStrengths: pickLabel(lang, "Strengths", "Strengths", "ताकत"),
    chipChallenges: pickLabel(lang, "Challenges", "Challenges", "चुनौतियाँ"),
    chipVerdict: pickLabel(lang, "Verdict", "Verdict", "निष्कर्ष"),
    chipActionPlan: pickLabel(lang, "Action Plan", "Action Plan", "अगला कदम"),
    chipBlueprint: pickLabel(lang, "Blueprint", "Blueprint", "ब्लूप्रिंट"),
    chipFiveDimensions: pickLabel(lang, "5 Dimensions", "5 Dimensions", "५ आयाम"),
    chipMoonSync: pickLabel(lang, "Moon Sync", "Moon Sync", "चंद्र"),
    chipRootCause: pickLabel(lang, "Root Cause", "Root Cause", "मूल वजह"),
    chipInsight: pickLabel(lang, "Insight", "Insight", "अंतर्दृष्टि"),
    alertRefreshTitle: pickLabel(lang, "Report refresh needed", "Report refresh chahiye", "रिपोर्ट रिफ्रेश"),
    alertRefreshBody: pickLabel(
      lang,
      "This saved report is incomplete. Tap Retry to reload, then Download PDF.",
      "Saved report incomplete hai. Retry dabao, phir PDF Download karo.",
      "सहेजी रिपोर्ट अधूरी है। Retry करें, फिर PDF डाउनलोड।",
    ),
    alertPdfSaved: pickLabel(lang, "PDF saved", "PDF save ho gayi", "PDF सहेजी"),
    alertPdfSavedBody: pickLabel(
      lang,
      "Saved to My Reports — English report",
      "My Reports mein save ho gayi — Hinglish report",
      "My Reports में सहेजी गई — Hindi रिपोर्ट",
    ),
    alertPdfSaveFailed: pickLabel(
      lang,
      "PDF downloaded but could not save to My Reports. Try again.",
      "PDF download ho gayi par My Reports mein save nahi hui. Phir try karo.",
      "PDF डाउनलोड हुई पर My Reports में सहेज नहीं सकी। फिर कोशिश करें।",
    ),
    openMyReports: pickLabel(lang, "Open My Reports", "My Reports kholo", "My Reports खोलें"),
    alertPdfFailed: pickLabel(lang, "PDF download failed", "PDF download fail", "PDF विफल"),
    retry: pickLabel(lang, "Retry", "Retry", "पुनः"),
    ok: pickLabel(lang, "OK", "OK", "ठीक"),
    updateReport: pickLabel(lang, "Update Report", "Report Update karo", "रिपोर्ट अपडेट करें"),
    updatingReport: pickLabel(lang, "Updating…", "Update ho raha hai…", "अपडेट हो रहा है…"),
    updateHint: pickLabel(
      lang,
      "Refresh full report — Overview and all sections",
      "Poora report refresh — Overview aur saari sections Hinglish mein",
      "पूरी रिपोर्ट रिफ्रेश — सारांश और सभी अनुभाग हिंदी में",
    ),
    updateDone: pickLabel(lang, "Report updated", "Report update ho gaya", "रिपोर्ट अपडेट हो गई"),
  };
}

/** UI + section labels for Love Reality Pro (en / hn / hi). */
export function loveRealityReportLabels(lang: ProPdfLangCode) {
  return L(lang);
}

function sumSectionLlmCostInr(
  meta: { pdf_generation?: { estimated_cost_inr?: number }; sections?: Record<string, { pdf_generation?: { estimated_cost_inr?: number } }> } | undefined,
): number {
  if (!meta) return 0;
  let total = 0;
  const sections = meta.sections;
  if (sections && typeof sections === "object") {
    for (const row of Object.values(sections)) {
      const inr = Number(row?.pdf_generation?.estimated_cost_inr ?? 0);
      if (inr > 0) total += inr;
    }
  }
  if (total > 0) return total;
  return Number(meta.pdf_generation?.estimated_cost_inr ?? 0);
}

/** Rounded LLM cost in ₹ — integer only, no tokens (operator). */
export function loveReportLlmCostInr(
  report: LoveProReportResponse | null | undefined,
): number | null {
  if (!report) return null;
  const top = report.llm_cost_inr;
  if (typeof top === "number" && top > 0) return Math.round(top);
  const meta = report.pro_premium?._meta as Parameters<typeof sumSectionLlmCostInr>[0];
  const inr = sumSectionLlmCostInr(meta);
  if (!inr || inr <= 0) return null;
  return Math.round(inr);
}

function isRiskMetric(label: string): boolean {
  return /breakup|risk|challenge|conflict|gap|stress|escalation|misalign/i.test(label);
}

const METRIC_LABEL_HI: Record<string, string> = {
  "Love Compatibility": "प्रेम अनुकूलता",
  "Breakup Risk": "ब्रेकअप जोखिम",
  "Loyalty & Trust": "निष्ठा और विश्वास",
  "Reunion Chance": "पुनर्मिलन की संभावना",
  Love: "प्रेम",
  Breakup: "ब्रेकअप",
  Loyalty: "निष्ठा",
  Return: "वापसी",
  "Emotional magnetism": "भावनात्मक आकर्षण",
  "Shared growth intent": "साझा विकास की इच्छा",
  "Karmic pull": "कर्मिक खिंचाव",
  "Attraction axis": "आकर्षण अक्ष",
  "Communication gaps": "संवाद में अंतर",
  "Trust under stress": "तनाव में विश्वास",
  "Timing misalignment": "समय की बेतालमेल",
  "Conflict escalation": "संघर्ष बढ़ना",
};

function localizeMetricLabel(label: string, lang: ProPdfLangCode): string {
  if (lang !== "hi") return label;
  return METRIC_LABEL_HI[label] || label;
}

/** Human-readable band — replaces misleading server labels like "very high" on score 13. */
export function humanScoreBand(score: number, label: string, lang: ProPdfLangCode = "en"): string {
  const v = Math.max(0, Math.min(100, Math.round(score)));
  if (isRiskMetric(label)) {
    if (lang === "hn") {
      if (v >= 70) return "Risk zyada";
      if (v >= 45) return "Risk moderate";
      return "Risk kam";
    }
    if (lang === "hi") {
      if (v >= 70) return "जोखिम अधिक";
      if (v >= 45) return "मध्यम जोखिम";
      return "कम जोखिम";
    }
    if (v >= 70) return "High risk";
    if (v >= 45) return "Moderate risk";
    return "Lower risk";
  }
  if (lang === "hn") {
    if (v >= 70) return "Strong";
    if (v >= 45) return "Mixed";
    if (v >= 25) return "Low";
    return "Bahut kam";
  }
  if (lang === "hi") {
    if (v >= 70) return "मजबूत";
    if (v >= 45) return "मिश्रित";
    if (v >= 25) return "कम";
    return "बहुत कम";
  }
  if (v >= 70) return "Strong";
  if (v >= 45) return "Mixed";
  if (v >= 25) return "Low";
  return "Very low";
}

function insightBulletsWithoutScores(items: string[] | undefined, max = 4): string[] {
  return (items || [])
    .filter(i => {
      const t = String(i || "").trim();
      return t && !/\d+\s*\/\s*100/.test(t);
    })
    .slice(0, max);
}

function pickSummary(primary?: string, secondary?: string): string {
  const a = (primary || "").trim();
  const b = (secondary || "").trim();
  if (!a) return b;
  if (!b) return a;
  const aStart = a.slice(0, 72).toLowerCase();
  const bStart = b.slice(0, 72).toLowerCase();
  if (aStart === bStart || a.includes(b.slice(0, 48)) || b.includes(a.slice(0, 48))) {
    return a.length >= b.length ? a : b;
  }
  return a;
}

function formatMetricLine(
  label: string,
  value: number | undefined,
  interpretation: string | undefined,
  lang: ProPdfLangCode,
): string {
  const locLabel = localizeMetricLabel(label, lang);
  const v = value ?? 0;
  const band = humanScoreBand(v, locLabel, lang);
  if (interpretation && interpretation.toLowerCase() !== band.toLowerCase()) {
    return `${locLabel}: ${v}/100 — ${band}`;
  }
  return `${locLabel}: ${v}/100 — ${band}`;
}

export {
  detectLoveReportChange,
  loveReportNeedsPdfResync,
  type LoveReportChangeKind,
  type LoveReportCacheMeta,
} from "@/lib/loveRealityReportRevision";

export type LoveReportBuildMode = "full" | "page";

/** Full sections — used for Connect to PDF (complete report). */
export function buildLoveReportSectionsFull(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
): LoveReportSection[] {
  const labels = L(lang);
  const sections: LoveReportSection[] = [];
  const ctx = report.pdf_context;
  const p1 = report.page1;

  if (p1) {
    const summaryParts = [
      p1.relationship_summary,
      p1.insights_narrative,
    ].filter(Boolean);
    pushSection(sections, {
      id: "exec_summary",
      title: labels.execSummary,
      subtitle: labels.relSummary,
      body: summaryParts.join("\n\n"),
      bullets: p1.key_insights,
    });

    const metricLines = (p1.metrics || []).map(
      m => `${m.label || "Metric"}: ${m.value ?? "—"}/100${m.interpretation ? ` — ${m.interpretation}` : ""}`,
    );
    pushSection(sections, {
      id: "core_metrics",
      title: labels.coreMetrics,
      subtitle: p1.cosmic_score != null ? `Cosmic Alignment Score: ${p1.cosmic_score}/100` : undefined,
      bullets: metricLines.length ? metricLines : undefined,
    });

    const strengthLines = (p1.strengths || []).map(s => `${s.label}: ${s.value}/100`);
    const challengeLines = (p1.challenges || []).map(c => `${c.label}: ${c.value}/100`);
    pushSection(sections, {
      id: "strengths",
      title: labels.strengths,
      bullets: strengthLines,
    });
    pushSection(sections, {
      id: "challenges",
      title: labels.challenges,
      bullets: challengeLines,
    });

    pushSection(sections, {
      id: "verdict",
      title: labels.verdict,
      subtitle: labels.verdictSub,
      body: p1.verdict,
    });

    const recBody = (p1.recommendation_paragraphs || []).join("\n\n");
    pushSection(sections, {
      id: "recommendations",
      title: labels.recommendations,
      body: recBody || undefined,
      bullets: p1.recommendations,
    });

    for (const item of p1.analysis || []) {
      const expl = (item.explanation || "").trim();
      if (!expl) continue;
      sections.push({
        id: `deep_${sections.length}`,
        title: item.title || "Deep Analysis",
        subtitle: labels.deepAnalysis,
        body: expl,
      });
    }
  }

  if (ctx) {
    const bp = ctx.page2_3_blueprint || {};
    pushSection(sections, {
      id: "blueprint_you",
      title: labels.blueprintYou,
      subtitle: "7th house · Upapada · Venus/Jupiter ideal signature",
      body: bp.part1,
    });
    pushSection(sections, {
      id: "blueprint_vs",
      title: labels.blueprintVs,
      subtitle: "Chart ideal vs actual partner nature",
      body: bp.part2,
    });

    const dimRows = (ctx.page4_dimensions || []).map(d => [
      d.label || d.key || "—",
      `${d.score ?? 0}/100`,
      "Love dimension matrix",
    ]);
    pushSection(sections, {
      id: "dimensions",
      title: labels.dimensions,
      subtitle: "Emotional · Attraction · Communication · Karmic · Stability",
      body: "Granular matrices from combined chart synastry — same bars as Basic mode.",
      tableRows: dimRows.length ? dimRows : undefined,
    });

    const moon = ctx.page5_moon || {};
    const moonBody = (moon.body || "").trim() || undefined;
    pushSection(sections, {
      id: "moon",
      title: labels.moon,
      subtitle: labels.moonDetailSub,
      body: moonBody,
    });

    pushSection(sections, {
      id: "root_cause",
      title: labels.rootCause,
      subtitle: labels.rootCauseSub,
      body: ctx.page6_root_cause,
    });

    const loyalty = ctx.page7_loyalty || {};
    const loyRows = (loyalty.rows || []).map(r => [
      r.label || "—",
      `${r.value ?? "—"}`,
      r.band || "",
    ]);
    pushSection(sections, {
      id: "loyalty",
      title: labels.loyalty,
      subtitle: loyalty.behavior || "Commitment under pressure",
      body: loyalty.body || loyalty.summary,
      tableRows: loyRows.length ? loyRows : undefined,
    });

    const rf = ctx.page8_red_flags || {};
    pushSection(sections, {
      id: "red_flags",
      title: labels.redFlags,
      subtitle: "Chart-derived warning signals",
      body: rf.body || "Chart-derived warning signals for this couple:",
      bullets: rf.bullets,
    });

    pushSection(sections, {
      id: "harmony",
      title: labels.harmony,
      subtitle: "Core behavioral shifts required",
      body: ctx.page9_harmony,
    });

    const dasha = ctx.page10_dasha || {};
    pushSection(sections, {
      id: "dasha",
      title: labels.dasha,
      subtitle: "Parallel time cycles for both partners",
      body: dasha.body || "Current and upcoming dasha alignment:",
      bullets: dasha.lines,
    });

    const roadmap = ctx.page11_roadmap || {};
    const rmRows = (roadmap.rows || []).map(r => [
      r.period || "—",
      r.trend || "—",
      (r.note || "").slice(0, 120),
    ]);
    pushSection(sections, {
      id: "roadmap",
      title: labels.roadmap,
      subtitle: "3 months · 12 months · 36 months",
      body: roadmap.body || "Month-by-month arc from Future + Return engines:",
      tableRows: rmRows.length ? rmRows : undefined,
    });

    const remedies = ctx.page12_remedies || {};
    pushSection(sections, {
      id: "upay",
      title: labels.upay,
      subtitle: "Customized structural remedies",
      body: remedies.body || "Personalized upay blocks — chart-balanced actions:",
      bullets: remedies.bullets,
    });

    const checklist = ctx.page13_checklist || {};
    pushSection(sections, {
      id: "checklist",
      title: labels.checklist,
      subtitle: "Human action plan",
      body: checklist.body || "Physical communication guidelines for this bond:",
      bullets: checklist.bullets,
    });

    pushSection(sections, {
      id: "closing",
      title: labels.closing,
      subtitle: "Positive closure · next check-in · disclaimer",
      body: ctx.page14_closing,
    });
  }

  if (sections.length > 0) return sections;

  // Fallback when server has not deployed pdf_context yet
  const pro = report.pro_premium;
  const verdict = (pro.verdict || "").trim();
  if (verdict) {
    sections.push({
      id: "verdict",
      title: labels.verdict,
      body: verdict,
    });
  }
  for (const ch of pro.chapters || []) {
    const body = (ch.chapter_body || ch.full_read || "").trim();
    if (!body) continue;
    sections.push({
      id: `ch_${ch.key || sections.length}`,
      title: ch.title || ch.key || "Chapter",
      body,
    });
  }
  return sections;
}

/**
 * Clean ~8-section scroll view — no duplicates, no dev boilerplate, fixed score labels.
 * PDF download uses the same `"page"` sections (WYSIWYG mirror).
 */
export function buildLoveReportSectionsForPage(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
): LoveReportSection[] {
  const labels = L(lang);
  const sections: LoveReportSection[] = [];
  const ctx = report.pdf_context;
  const p1 = report.page1;

  if (p1) {
    const summary = pickSummary(p1.relationship_summary, p1.insights_narrative);
    pushSection(sections, {
      id: "exec_summary",
      title: labels.execSummary,
      subtitle: labels.relSummary,
      body: summary || undefined,
      bullets: insightBulletsWithoutScores(p1.key_insights, 4),
    });

    const serverScorecard = (report.app_sections || []).find(
      s => String(s.id || "").toLowerCase() === "scorecard",
    );
    const serverBullets = (serverScorecard?.bullets || [])
      .map(b => String(b || "").trim())
      .filter(Boolean);
    const scorecardLines = serverBullets.length && lang === "hi"
      ? serverBullets
      : [
        ...(p1.metrics || []).map(m =>
          formatMetricLine(m.label || "Metric", m.value, m.interpretation, lang),
        ),
        ...(p1.strengths || []).map(s => {
          const lbl = localizeMetricLabel(s.label || "", lang);
          return `${lbl}: ${s.value}/100 — ${humanScoreBand(s.value ?? 0, lbl, lang)}`;
        }),
        ...(p1.challenges || []).map(c => {
          const lbl = localizeMetricLabel(c.label || "challenge", lang);
          return `${lbl}: ${c.value}/100 — ${humanScoreBand(c.value ?? 0, lbl, lang)}`;
        }),
      ];
    pushSection(sections, {
      id: "scorecard",
      title: labels.scorecard,
      subtitle: p1.cosmic_score != null ? labels.cosmicScore(p1.cosmic_score) : undefined,
      bullets: scorecardLines.length ? scorecardLines : undefined,
    });

    pushSection(sections, {
      id: "verdict",
      title: labels.verdict,
      subtitle: labels.verdictSub,
      body: p1.verdict,
    });

    const recBody = resolveRecommendationsBody(report, lang);
    const recBullets = resolveRecommendationsBullets(report);
    pushSection(sections, {
      id: "recommendations",
      title: labels.recommendations,
      subtitle: labels.recommendationsSub,
      body: recBody || undefined,
      bullets: recBullets.length ? recBullets : undefined,
    });

    pushSection(sections, {
      id: "deep_connection",
      title: labels.deepCombined,
      subtitle: labels.deepSub,
      body: resolveDeepConnectionBody(report, lang) || undefined,
    });
  }

  if (ctx) {
    pushSection(sections, {
      id: "blueprint_vs",
      title: labels.blueprintVs,
      subtitle: labels.blueprintVsSub,
      body: resolveBlueprintVsBody(report, lang) || undefined,
    });

    const moonBody = resolveMoonSyncBody(report, lang) || undefined;
    pushSection(sections, {
      id: "moon",
      title: labels.moon,
      subtitle: labels.moonSub,
      body: moonBody,
    });

    pushSection(sections, {
      id: "root_cause",
      title: labels.rootCause,
      subtitle: labels.rootCauseSub,
      body: resolveSection8RootCauseBody(report, lang) || ctx.page6_root_cause,
    });
  }

  if (sections.length > 0) return annotatePdfSectionNo(filterInAppReportSections(sections));

  return filterInAppReportSections(buildLoveReportSectionsFull(report, lang));
}

/**
 * Prefer server `app_sections` from pro-report (post Update / LLM).
 * Falls back to local build when older API omits the field.
 */
export function buildReportSectionsFromPayload(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
): LoveReportSection[] {
  const local = buildLoveReportSections(report, lang, { mode: "page" });
  const server = report.app_sections;
  if (!Array.isArray(server) || server.length === 0) {
    return filterInAppReportSections(local);
  }
  const labels = L(lang);
  const meta: Record<string, { title: string; subtitle?: string }> = {
    exec_summary: { title: labels.execSummary, subtitle: labels.relSummary },
    scorecard: { title: labels.scorecard },
    verdict: { title: labels.verdict, subtitle: labels.verdictSub },
    recommendations: { title: labels.recommendations, subtitle: labels.recommendationsSub },
    deep_connection: { title: labels.deepCombined, subtitle: labels.deepSub },
    blueprint_vs: { title: labels.blueprintVs, subtitle: labels.blueprintVsSub },
    root_cause: { title: labels.rootCause, subtitle: labels.rootCauseSub },
    moon: { title: labels.moon, subtitle: labels.moonSub },
  };
  const localById = new Map(local.map(s => [s.id.toLowerCase(), s]));
  const narrativeNoBullets = new Set([
    "deep_connection",
    "blueprint_vs",
    "moon",
    "root_cause",
    "verdict",
  ]);
  const sections: LoveReportSection[] = [];
  const seen = new Set<string>();
  for (const row of server) {
    if (!row || typeof row !== "object") continue;
    const id = String(row.id || "").trim();
    if (!id) continue;
    seen.add(id.toLowerCase());
    const fallback = localById.get(id.toLowerCase());
    let body = String(row.body || "").trim() || fallback?.body;
    if (id.toLowerCase() === "root_cause") {
      const resolved = resolveSection8RootCauseBody(report, lang);
      if (resolved) body = resolved;
    }
    if (id.toLowerCase() === "recommendations") {
      const resolved = resolveRecommendationsBody(report, lang);
      if (resolved) body = resolved;
    }
    if (id.toLowerCase() === "deep_connection") {
      const resolved = resolveDeepConnectionBody(report, lang);
      if (resolved) body = resolved;
    }
    if (id.toLowerCase() === "blueprint_vs") {
      const resolved = resolveBlueprintVsBody(report, lang);
      if (resolved) body = resolved;
    }
    if (id.toLowerCase() === "moon") {
      const resolved = resolveMoonSyncBody(report, lang);
      if (resolved) body = resolved;
    }
    let rawBullets = Array.isArray(row.bullets) && row.bullets.length
      ? row.bullets.map(b => String(b).trim()).filter(Boolean)
      : fallback?.bullets;
    if (id.toLowerCase() === "recommendations") {
      const resolvedBullets = resolveRecommendationsBullets(report);
      if (resolvedBullets.length) rawBullets = resolvedBullets;
    }
    if (body && !proseLaneOk(body, lang)) {
      const safeFallback = fallback?.body && proseLaneOk(fallback.body, lang) ? fallback.body : "";
      body = safeFallback || undefined;
    }
    const bullets = narrativeNoBullets.has(id.toLowerCase()) ? undefined : rawBullets;
    const m = meta[id];
    pushSection(sections, {
      id,
      title: m?.title || fallback?.title || id,
      subtitle: m?.subtitle || fallback?.subtitle,
      body: body || undefined,
      bullets: bullets?.length ? bullets : undefined,
    });
  }
  for (const loc of local) {
    if (seen.has(loc.id.toLowerCase())) continue;
    pushSection(sections, loc);
  }
  if (sections.length > 0) return annotatePdfSectionNo(filterInAppReportSections(sections));
  return annotatePdfSectionNo(filterInAppReportSections(local));
}

/** @param mode `"page"` = clean in-app scroll · `"full"` = complete PDF mirror (default) */
export function buildLoveReportSections(
  report: LoveProReportResponse,
  lang: ProPdfLangCode,
  opts?: { mode?: LoveReportBuildMode },
): LoveReportSection[] {
  if (opts?.mode === "page") {
    return filterInAppReportSections(buildLoveReportSectionsForPage(report, lang));
  }
  return buildLoveReportSectionsFull(report, lang);
}

export type LoveProReportFetchResult = {
  data: LoveProReportResponse;
  /** Server returned a saved JSON report — no LLM / no bundle rebuild. */
  serverCacheHit: boolean;
};

export async function fetchLoveRealityProReport(opts: {
  user: { id: number; api_key?: string | null };
  p1: BirthData;
  p2: BirthData;
  p1Name: string;
  p2Name: string;
  lang: string;
  signal?: AbortSignal;
  /**
   * Rebuild pdf_context + page1 from saved polish — skips JSON cache, no LLM.
   * Use when PDF layout ver changed on server.
   */
  layoutRefresh?: boolean;
  /** Fresh OpenAI polish — skips polish snapshot; only when true. */
  forceLlm?: boolean;
  /** User tapped Update Report — full LLM regen, never layout-only cache. */
  fullUpdate?: boolean;
  /** Re-run Hindi translate on saved JSON — no LLM (fast retry after Update). */
  relocalizeOnly?: boolean;
  /** Bust CDN/proxy caches on force refresh. */
  cacheBust?: number;
  /** After reinstall — restore saved report from server account cache (no LLM). */
  preferServerCache?: boolean;
}): Promise<LoveProReportFetchResult> {
  const lang = coerceProPdfLang(opts.lang);
  const tz1 = opts.p1.tz ?? Math.round((opts.p1.lon! / 15) * 2) / 2;
  const tz2 = opts.p2.tz ?? Math.round((opts.p2.lon! / 15) * 2) / 2;
  const fullUpdate = Boolean(opts.fullUpdate);
  const layoutRefresh = Boolean(opts.layoutRefresh) && !fullUpdate;
  const relocalizeOnly = Boolean(opts.relocalizeOnly) && !fullUpdate;
  const forceLlm = Boolean(opts.forceLlm) && !relocalizeOnly;
  const cacheBust = opts.cacheBust ?? (fullUpdate ? Date.now() : 0);
  const bustQs = cacheBust ? `?_=${cacheBust}` : "";

  const resp = await fetch(`${API_BASE}/api/love-reality/pro-report${bustQs}`, {
    method: "POST",
    headers: {
      ...pdfAuthHeaders(opts.user),
      Accept: "application/json",
      ...(layoutRefresh ? { "X-PDF-Layout-Refresh": "1" } : {}),
      ...(fullUpdate ? { "X-Force-Regenerate": "1" } : {}),
      ...(forceLlm ? { "X-Force-LLM": "1" } : {}),
      ...(fullUpdate ? { "X-Love-Report-Full-Update": "1" } : {}),
      ...(relocalizeOnly ? { "X-Relocalize-Sections": "1" } : {}),
      ...(opts.preferServerCache ? { "X-Prefer-Server-Cache": "1" } : {}),
    },
    body: JSON.stringify({
      p1: { ...packLovePerson(opts.p1, opts.p1Name), tz: tz1 },
      p2: { ...packLovePerson(opts.p2, opts.p2Name), tz: tz2 },
      lang,
      ...(fullUpdate ? { force_regenerate: true } : {}),
      ...(forceLlm ? { force_llm: true } : {}),
      ...(fullUpdate ? { force_update: true } : {}),
      ...(relocalizeOnly ? { relocalize_sections: true } : {}),
      ...(cacheBust ? { cache_bust: cacheBust } : {}),
    }),
    signal: opts.signal,
  });

  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = (data as { detail?: string }).detail;
    throw new Error(
      detail
      || (data as { message?: string }).message
      || (data as { error?: string }).error
      || `Report failed (${resp.status})`,
    );
  }
  const serverCacheHit = (resp.headers.get("X-Report-Cache") || "").toLowerCase() === "hit";
  return { data: data as LoveProReportResponse, serverCacheHit };
}
