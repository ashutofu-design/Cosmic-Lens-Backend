/**
 * Love Reality Pro — in-app full report (JSON from server, PDF-parity layout).
 */
import { API_BASE } from "@/lib/apiConfig";
import { pdfAuthHeaders } from "@/lib/coupleReportCheckoutFlow";
import { packLovePerson } from "@/lib/loveRealityProPdfDownload";
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
  red_flags_narrative?: string;
  dasha_narrative?: string;
  roadmap_narrative?: string;
  deep_analysis?: LoveProDeepAnalysis[];
  chapters?: LoveProChapter[];
  special?: string[];
  damage?: string[];
  practical?: string[];
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
};

export type LoveReportSection = {
  id: string;
  title: string;
  subtitle?: string;
  body?: string;
  bullets?: string[];
  tableRows?: string[][];
};

function pushSection(sections: LoveReportSection[], sec: LoveReportSection | null | undefined) {
  if (!sec) return;
  const hasBody = (sec.body || "").trim().length > 0;
  const hasBullets = (sec.bullets || []).some(b => b.trim().length > 0);
  const hasTable = (sec.tableRows || []).length > 0;
  if (hasBody || hasBullets || hasTable) sections.push(sec);
}

function L(lang: ProPdfLangCode) {
  const hi = lang === "hi";
  const hn = lang === "hn";
  return {
    execSummary: hi ? "Executive Summary & Cosmic Alignment" : "Executive Summary & Cosmic Alignment",
    relSummary: hi ? "Relationship Summary" : "Relationship Summary",
    coreMetrics: hi ? "Core Metrics" : "Core Metrics",
    insights: hi ? "Relationship Insights" : "Relationship Insights",
    strengths: hi ? "Strengths in this Connection" : "Strengths in this Connection",
    challenges: hi ? "Challenges in this Connection" : "Challenges in this Connection",
    verdict: hi ? "ज्योतिषी का नोट" : hn ? "Final Cosmic Verdict" : "Final Cosmic Verdict",
    verdictSub: hi ? "Final Verdict & Recommendations" : "Astrologer's Note",
    recommendations: hi ? "Recommendations" : hn ? "Aage Kya Karein" : "Recommendations",
    deepAnalysis: hi ? "Deep Connection Analysis" : "Deep Connection Analysis",
    blueprintYou: hi ? "Destiny Partner Blueprint (You)" : "Destiny Partner Blueprint (You)",
    blueprintVs: hi ? "Partner Blueprint vs Reality" : "Partner Blueprint vs Reality",
    dimensions: hi ? "The 5 Love Dimensions Deep-Dive" : "The 5 Love Dimensions Deep-Dive",
    moon: hi ? "Moon Synastry & Emotional Rhythm" : "Moon Synastry & Emotional Rhythm",
    rootCause: hi ? "The Core Root Cause" : "The Core Root Cause",
    loyalty: hi ? "Loyalty, Trust & Psychological Traits" : "Loyalty, Trust & Psychological Traits",
    redFlags: hi ? "Red Flags Matrix" : "Red Flags Matrix",
    harmony: hi ? "The Harmony Formula" : "The Harmony Formula",
    dasha: hi ? "Vimshottari Dasha Synchronization" : "Vimshottari Dasha Synchronization",
    roadmap: hi ? "The 1–3 Year Chronological Roadmap" : "The 1–3 Year Chronological Roadmap",
    upay: hi ? "Planetary Counter Measures (Upay)" : "Planetary Counter Measures (Upay)",
    checklist: hi ? "Relationship Checklist" : "Relationship Checklist",
    closing: hi ? "Closing Guidance & Disclaimer" : "Closing Guidance & Disclaimer",
  };
}

/** PDF-parity scroll sections — same engine + LLM mix as ReportLab PDF. */
export function buildLoveReportSections(
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
      const score = item.score != null ? ` · ${item.score}/100` : "";
      sections.push({
        id: `deep_${sections.length}`,
        title: `${item.title || "Deep Analysis"}${score}`,
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
    const moonBody = [
      moon.p1_moon && moon.p2_moon
        ? `Your Moon: ${moon.p1_moon} · Partner Moon: ${moon.p2_moon}`
        : "",
      moon.body || "",
    ].filter(Boolean).join("\n\n");
    pushSection(sections, {
      id: "moon",
      title: labels.moon,
      subtitle: "Shashtashtak / 6-8 sign emotional alignment check",
      body: moonBody,
      bullets: (moon.notes || []).map(String),
    });

    pushSection(sections, {
      id: "root_cause",
      title: labels.rootCause,
      subtitle: "What is silently breaking you apart",
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
}): Promise<LoveProReportFetchResult> {
  const lang = coerceProPdfLang(opts.lang);
  const tz1 = opts.p1.tz ?? Math.round((opts.p1.lon! / 15) * 2) / 2;
  const tz2 = opts.p2.tz ?? Math.round((opts.p2.lon! / 15) * 2) / 2;

  const resp = await fetch(`${API_BASE}/api/love-reality/pro-report`, {
    method: "POST",
    headers: {
      ...pdfAuthHeaders(opts.user),
      Accept: "application/json",
    },
    body: JSON.stringify({
      p1: { ...packLovePerson(opts.p1, opts.p1Name), tz: tz1 },
      p2: { ...packLovePerson(opts.p2, opts.p2Name), tz: tz2 },
      lang,
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
