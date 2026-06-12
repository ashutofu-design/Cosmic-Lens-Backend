/**

 * Detect whether cached Love Reality Pro text matches requested report language.

 * No imports from loveRealityProReport — avoids Metro circular-import undefined exports.

 */

import { coerceProPdfLang, type ProPdfLangCode } from "@/lib/proPdfLang";
import { LOVE_REALITY_POLISH_ASSEMBLY_VER } from "@/lib/loveRealityReportRevision";



const DEVANAGARI = /[\u0900-\u097F]/;

const HINGLISH_STRONG =

  /\b(aap|aapka|aapke|aapki|aapko|rishta|rishte|pyar|kya|hai|hain|nahi|nahin|hoga|hogi|zyada|kam|saath|beech|asli|poori|jyotish|dasha|upay|tumhari|tumhe|dono|bach|karo|karein|yeh|ye|aur|mein|main|ke liye|saath|lagta|rishte)\b/i;



/** Minimal shape for language detection — matches LoveProReportResponse fields we read. */

export type LoveReportLangPayload = {

  lang?: string;

  section4_hi_body?: string | null;

  section8_hi_body?: string | null;

  hi_cache_ver?: string | null;

  polish_assembly?: string | null;

  pro_premium?: {
    remedies_action_narrative?: string;
    action_steps?: string[];
  };

  section8_debug?: {

    gate_ver?: string;

    breakup_words?: number;

    breakup_deva?: number;

    root_words?: number;

    root_deva?: number;

    effective_words?: number;

    effective_deva?: number;

  };

  pdf_context?: { page6_root_cause?: string };

  page1?: {

    relationship_summary?: string;

    insights_narrative?: string;

    verdict?: string;

    key_insights?: string[];

    recommendation_paragraphs?: string[];

    recommendations?: string[];

  };

  app_sections?: Array<{

    id?: string;

    body?: string | null;

    bullets?: string[] | null;

  }>;

  content_script?: string;

};



/** Narrative prose — scorecard KPI labels checked separately via scorecardHiLoadGate. */

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



/** Selected lang does not match cached/API prose — need fresh LLM. */

export function needsLoveReportLlmRefresh(

  report: LoveReportLangPayload | null | undefined,

  lang: ProPdfLangCode,

  metaContentLang?: string | null,

): boolean {

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

  if (lang === "hi") return script === "hi";

  if (lang === "hn") return script === "hn";

  return true;

}



/** True when Update can stop retrying — full Hindi/Hinglish, not mixed English. */

export function reportHindiFullyReady(

  report: LoveReportLangPayload,

  lang: ProPdfLangCode,

): boolean {

  if (lang === "en") return reportSummaryMatchesLang(report, lang);

  const script = (report.content_script || "").trim().toLowerCase();

  if (lang === "hi") return script === "hi";

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

  if (lang === "hi" && !section4HiLoadReady(report, lang)) return true;

  return !reportHindiFullyReady(report, lang);

}



/** Primary check — narrative prose (not English score labels). */

function textLooksEnglishProse(text: string): boolean {

  const t = text.trim();

  if (!t || t.length < 20) return false;

  if (DEVANAGARI.test(t)) return false;

  if (textLooksHinglish(t)) return false;

  return true;

}



export function reportSummaryMatchesLang(

  report: LoveReportLangPayload,

  lang: ProPdfLangCode,

): boolean {

  if (reportScriptMatchesLang(report, lang)) return true;

  const text = narrativeText(report);

  if (!text.trim()) return false;

  if (lang === "en") return textLooksEnglishProse(text);

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



function section8RootCauseText(report: LoveReportLangPayload): string {

  const sec = (report.app_sections || []).find(

    s => String(s.id || "").toLowerCase() === "root_cause",

  );

  const fromSec = String(sec?.body || "").trim();

  if (fromSec) return fromSec;

  return String(report.pdf_context?.page6_root_cause || "").trim();

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



function devaCount(text: string): number {

  return (text.match(DEVANAGARI) || []).length;

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

      const avg = lines.reduce((n, l) => n + wordCount(l), 0) / lines.length;

      if (avg < 22) return true;

    }

  }

  return false;

}



function proseParagraphFormOk(text: string, minParagraphs = 3, minParaWords = 18): boolean {

  const raw = String(text || "").trim();

  if (!raw || textLooksLikePointList(raw)) return false;

  const paras = raw.split(/\n\s*\n+/).map(p => p.trim()).filter(Boolean);

  if (paras.length < minParagraphs) return false;

  const good = paras.filter(p => wordCount(p) >= minParaWords).length;

  return good >= minParagraphs;

}



function normalizeProseParagraphs(text: string, minParagraphs = 3): string {

  const raw = String(text || "").trim();

  if (!raw) return raw;

  if (proseParagraphFormOk(raw, minParagraphs, 18)) return raw;

  const flat = raw.replace(/\s*\n\s*/g, " ");

  const sentences = flat

    .split(/(?<=[।.!?])\s+/)

    .map(s => s.trim())

    .filter(Boolean);

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

  return (

    wordCount(t) >= SECTION8_MIN_WORDS

    && devaCount(t) >= 24

    && proseFullyHindi(t)

  );

}



function proseFullyHindi(text: string): boolean {

  const t = text.trim();

  if (!t || t.length < 40) return false;

  const deva = devaCount(t);

  if (deva < 12) return false;

  const letters = (t.match(/[A-Za-z\u0900-\u097F]/g) || []).length;

  if (letters < 20) return deva >= 8;

  return deva / letters >= 0.32;

}



function effectiveSection8Text(report: LoveReportLangPayload): string {

  const canon = normalizeProseParagraphs(String(report.section8_hi_body || "").trim());

  if (canon && section8LoadReady(canon)) return canon;



  const breakup = section8BreakupChapterText(report);

  const root = section8RootCauseText(report);



  let best = "";

  let bestDeva = -1;

  for (const raw of [breakup, root]) {

    const text = normalizeProseParagraphs(String(raw || "").trim());

    if (!text) continue;

    const deva = devaCount(text);

    const wc = wordCount(text);

    if (wc >= SECTION8_MIN_WORDS && deva > bestDeva) {

      best = text;

      bestDeva = deva;

    }

  }

  if (best) return best;



  if (serverSection8Ready(report)) {

    const fallback = normalizeProseParagraphs(breakup || root || canon);

    if (fallback) return fallback;

  }

  return "";

}



function serverSection8Ready(report: LoveReportLangPayload): boolean {

  const dbg = report.section8_debug;

  if (!dbg?.gate_ver) return false;

  const rootD = dbg.root_deva ?? 0;

  const buD = dbg.breakup_deva ?? 0;

  const effD = dbg.effective_deva ?? 0;

  const rootW = dbg.root_words ?? 0;

  const buW = dbg.breakup_words ?? 0;

  const effW = dbg.effective_words ?? 0;

  const deva = Math.max(rootD, buD, effD);

  const words = Math.max(rootW, buW, effW);

  return deva >= 24 && words >= SECTION8_MIN_WORDS;

}



const SECTION4_MIN_WORDS = 70;

const GENERIC_REC_HI_MARKERS = [
  "हर झगड़े के २४ घंटे",
  "साप्ताहिक २० मिनट",
  "कमज़ोर दशा में अल्टीमेटम",
];



function section4RemediesNarrative(report: LoveReportLangPayload): string {
  return normalizeProseParagraphs(
    String(report.pro_premium?.remedies_action_narrative || "").trim(),
  );
}

/** Align with server remedies_action_hi_ready — no English paragraph fallback. */
function section4NarrativeHiReady(text: string): boolean {
  const t = normalizeProseParagraphs(String(text || "").trim());
  if (wordCount(t) < SECTION4_MIN_WORDS) return false;
  if (devaCount(t) < 24) return false;
  if (!proseFullyHindi(t)) return false;
  if (textLooksLikePointList(t)) return false;
  return true;
}

function serverSection4Ready(report: LoveReportLangPayload): boolean {
  const dbg = (report as { section4_debug?: { ready?: boolean; deva?: number; words?: number } }).section4_debug;
  if (!dbg?.ready) return false;
  return (dbg.deva ?? 0) >= 24 && (dbg.words ?? 0) >= SECTION4_MIN_WORDS;
}

function effectiveSection4Text(report: LoveReportLangPayload): string {
  const narr = section4RemediesNarrative(report);
  const canon = normalizeProseParagraphs(String(report.section4_hi_body || "").trim());
  if (section4NarrativeHiReady(narr)) return narr;
  if (section4NarrativeHiReady(canon)) return canon;
  if (canon && devaCount(canon) >= 24) return canon;
  if (narr) return narr;
  const sec = (report.app_sections || [])
    .find(s => String(s.id || "").toLowerCase() === "recommendations");
  const fromSec = normalizeProseParagraphs(String(sec?.body || "").trim());
  if (fromSec && devaCount(fromSec) >= 24) return fromSec;
  const paras = (report.page1?.recommendation_paragraphs || [])
    .map(p => String(p || "").trim())
    .filter(Boolean)
    .join("\n\n");
  if (paras && devaCount(paras) >= 24) return normalizeProseParagraphs(paras);
  return fromSec || normalizeProseParagraphs(paras);
}

function section4RecommendationsText(report: LoveReportLangPayload): string {
  return effectiveSection4Text(report);
}



function section4LooksGenericFallback(report: LoveReportLangPayload): boolean {

  const body = section4RecommendationsText(report);

  if (wordCount(body) >= SECTION4_MIN_WORDS && devaCount(body) >= 24) return false;

  const sec = (report.app_sections || [])

    .find(s => String(s.id || "").toLowerCase() === "recommendations");

  const bullets = (sec?.bullets || report.page1?.recommendations || [])

    .map(b => String(b || "").trim())

    .filter(Boolean);

  if (!bullets.length) return true;

  if (bullets.length > 4) return false;

  const hits = bullets.filter(b =>

    GENERIC_REC_HI_MARKERS.some(m => b.includes(m)),

  ).length;

  return hits >= Math.min(2, bullets.length);

}



function section4LoadReady(text: string): boolean {

  const t = normalizeProseParagraphs(String(text || "").trim());

  return (

    wordCount(t) >= SECTION4_MIN_WORDS

    && devaCount(t) >= 24

    && proseFullyHindi(t)

    && !textLooksLikePointList(t)

  );

}



/** Section 4 (उपाय और आगे क्या करें) — full LLM Hindi prose required. */

export function section4HiLoadReady(

  report: LoveReportLangPayload | null | undefined,

  lang: ProPdfLangCode,

): boolean {

  if (lang !== "hi") return true;

  return section4HiLoadGate(report).ok;

}



export function section4HiLoadGate(

  report: LoveReportLangPayload | null | undefined,

): { ok: boolean; reason: string } {

  if (!report) {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 4 (उपाय) data missing. «रिपोर्ट अपडेट करें» dabao.",

    };

  }

  const pro = (report as { pro_premium?: { _meta?: { section4_remedies?: { source?: string } } } }).pro_premium;

  const llmMeta = pro?._meta?.section4_remedies;

  if (llmMeta?.source === "failed") {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 4 LLM Hindi fail hua. «रिपोर्ट अपडेट करें» dubara dabao — 2–3 min wait.",

    };

  }

  if (serverSection4Ready(report)) {
    return { ok: true, reason: "" };
  }

  const narr = section4RemediesNarrative(report);
  const canon = normalizeProseParagraphs(String(report.section4_hi_body || "").trim());

  if (section4NarrativeHiReady(narr) || section4NarrativeHiReady(canon)) {
    return { ok: true, reason: "" };
  }

  if (section4LooksGenericFallback(report)) {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 4 mein sirf chhoti generic lines hain, LLM explanation nahi bana. «रिपोर्ट अपडेट करें» dabao.",

    };

  }

  const text = effectiveSection4Text(report);

  if (!text) {
    return {
      ok: false,
      reason:
        "Report load nahi hua — Section 4 (उपाय और आगे क्या करें) khali hai. Update Report dabao.",
    };
  }

  if (!section4NarrativeHiReady(text)) {
    const wc = wordCount(text);
    const deva = devaCount(text);
    const canonDeva = devaCount(canon);
    const dbg = (report as { section4_debug?: { ready?: boolean; deva?: number } }).section4_debug;
    const hint = dbg?.deva && dbg.deva >= 24
      ? ` (server section4_hi_body deva=${dbg.deva} — app reload karo)`
      : canonDeva >= 24
        ? ` (canon deva=${canonDeva} — gate mismatch, app update chahiye)`
        : "";
    return {
      ok: false,
      reason:
        `Report load nahi hua — Section 4 poori देवनागरी Hindi nahi bani (${wc} words, Devanagari=${deva}). «रिपोर्ट अपडेट करें» dabao — 2–3 min wait.${hint}`,
    };
  }

  return { ok: true, reason: "" };

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



  const s8Meta = (

    report as { pro_premium?: { _meta?: { section8_breakup?: { source?: string; attempt?: string | number } } } }

  ).pro_premium?._meta?.section8_breakup;

  if (s8Meta?.attempt === "translate_fallback" || s8Meta?.source === "translate") {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 8 sirf translate se bana (LLM chapter nahi). "

        + "«रिपोर्ट अपडेट करें» dabao.",

    };

  }

  if (s8Meta?.source === "failed") {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 8 LLM Hindi chapter fail hua. "

        + "«रिपोर्ट अपडेट करें» dubara dabao.",

    };

  }



  if (serverSection8Ready(report)) {

    return { ok: true, reason: "" };

  }



  const text = effectiveSection8Text(report);



  if (!text) {

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 8 (मूल वजह) bilkul khali hai. "

        + "LLM ne breakup chapter generate nahi kiya. Niche «Update Report» dabayein.",

    };

  }



  const wc = wordCount(text);

  if (wc < SECTION8_MIN_WORDS) {

    return {

      ok: false,

      reason:

        `Report load nahi hua — Section 8 LLM explanation bahut chhota hai `

        + `(${wc} words, kam se kam ${SECTION8_MIN_WORDS} chahiye). `

        + "OpenAI poora paragraph nahi likh paya — Update dubara try karein.",

    };

  }



  if (!proseFullyHindi(text)) {

    const deva = devaCount(text);

    const dbg = report.section8_debug;

    const srv = Math.max(dbg?.root_deva ?? 0, dbg?.breakup_deva ?? 0, dbg?.effective_deva ?? 0);

    return {

      ok: false,

      reason:

        "Report load nahi hua — Section 8 abhi English/mixed hai, poori देवनागरी Hindi nahi "

        + `(Devanagari chars: ${deva}${srv ? `, server=${srv}` : ""}). `

        + "«रिपोर्ट अपडेट करें» dubao.",

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



function scorecardLinesFromReport(report: LoveReportLangPayload): string[] {

  const sec = (report.app_sections || []).find(

    s => String(s.id || "").toLowerCase() === "scorecard",

  );

  const fromServer = (sec?.bullets || [])

    .map(b => String(b || "").trim())

    .filter(Boolean);

  if (fromServer.length) return fromServer;

  const p1 = report.page1;

  if (!p1) return [];

  return [

    ...(p1.metrics || []).map(m => `${String(m.label || "").trim()}: ${m.value ?? 0}/100`),

    ...(p1.strengths || []).map(s => `${String(s.label || "").trim()}: ${s.value ?? 0}/100`),

    ...(p1.challenges || []).map(c => `${String(c.label || "").trim()}: ${c.value ?? 0}/100`),

  ].filter(l => l.includes(":"));

}



function scorecardLabelHiOk(line: string): boolean {

  const label = line.split(":")[0]?.trim() || "";

  return Boolean(label && DEVANAGARI.test(label));

}



/** KPI / scorecard labels must be देवनागरी before Hindi page opens. */

export function scorecardHiLoadGate(

  report: LoveReportLangPayload | null | undefined,

): { ok: boolean; reason: string } {

  const lines = scorecardLinesFromReport(report || {});

  if (!lines.length) {

    return {

      ok: false,

      reason:

        "Report load nahi hua — KPI scorecard missing hai. «रिपोर्ट अपडेट करें» dabao.",

    };

  }

  for (const line of lines) {

    if (!scorecardLabelHiOk(line)) {

      const label = line.split(":")[0]?.trim().slice(0, 28) || "KPI";

      return {

        ok: false,

        reason:

          `Report load nahi hua — KPI "${label}" abhi English hai. Poori Hindi banne tak wait karo ya «रिपोर्ट अपडेट करें» dabao.`,

      };

    }

  }

  return { ok: true, reason: "" };

}



/** Hindi page opens only when narrative + KPI + sections are fully देवनागरी. */

export function hindiReportPageLoadReady(

  report: LoveReportLangPayload | null | undefined,

  lang: ProPdfLangCode,

): { ok: boolean; reason: string } {

  if (lang !== "hi") return { ok: true, reason: "" };

  const s4 = section4HiLoadGate(report);

  if (!s4.ok) return s4;

  const s8 = section8HiLoadGate(report);

  if (!s8.ok) return s8;

  const sc = scorecardHiLoadGate(report);

  if (!sc.ok) return sc;

  const script = (report?.content_script || "").trim().toLowerCase();

  if (script === "hi_partial" || script === "en_mismatch") {

    return {

      ok: false,

      reason:

        "Report abhi poori देवनागरी Hindi nahi — kuch lines English mein hain. 1–2 min wait karke «रिपोर्ट अपडेट करें» dabao.",

    };

  }

  if (script === "unknown") {
    const narr = narrativeText(report || {});
    if (textLooksHindi(narr) && scorecardHiLoadGate(report).ok) {
      return { ok: true, reason: "" };
    }
    return {
      ok: false,
      reason:
        "Report script unknown — server par app_sections build fail ho sakta hai. VPS: git pull + pm2 restart, phir cache clear.",
    };
  }

  if (script !== "hi") {
    return {
      ok: false,
      reason:
        script
          ? `Report script "${script}" — poori Hindi tayyar nahi. «रिपोर्ट अपडेट करें» dabao.`
          : "Report abhi localize ho rahi hai — poori Hindi banne ke baad page khulega. «रिपोर्ट अपडेट करें» try karo.",
    };
  }

  return { ok: true, reason: "" };

}



export function hindiReportPageLoadOk(

  report: LoveReportLangPayload | null | undefined,

  lang: ProPdfLangCode,

): boolean {

  return hindiReportPageLoadReady(report, lang).ok;

}



/** en/hn — saved report complete enough to open from device cache (no LLM). */

export function enHnReportCacheReady(

  report: LoveReportLangPayload | null | undefined,

  lang: ProPdfLangCode,

): boolean {

  if (lang !== "en" && lang !== "hn") return false;

  if (!report || !reportHasDisplayableContent(report)) return false;

  const asm = String(report.polish_assembly || "").trim();
  if (asm && asm !== LOVE_REALITY_POLISH_ASSEMBLY_VER) return false;

  return reportContentMatchesLang(report, lang);

}



/** True when saved JSON body matches the language user selected. */

export function reportContentMatchesLang(

  report: LoveReportLangPayload,

  lang: ProPdfLangCode,

): boolean {

  if (coerceProPdfLang(report.lang) !== lang) return false;

  return reportSummaryMatchesLang(report, lang);

}


