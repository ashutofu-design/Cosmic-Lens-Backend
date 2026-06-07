export interface MetricBlock {
  label: string;
  value: number;
  interpretation: string;
  invert?: boolean;
}

export interface AnalysisBlock {
  title: string;
  score: number;
  explanation: string;
}

export interface InsightItem {
  text: string;
}

export interface ComparisonItem {
  label: string;
  value: number;
}

export interface LoveRealityReportData {
  reportId: string;
  generatedAt: string;
  p1Name: string;
  p2Name: string;
  cosmicAlignmentScore: number;
  relationshipSummary: string;
  metrics: {
    loveCompatibility: MetricBlock;
    breakupRisk: MetricBlock;
    loyalty: MetricBlock;
    reunionChance: MetricBlock;
  };
  snapshot: string;
  keyInsights: InsightItem[];
  aiExplanation: string;
  analysis: {
    emotional: AnalysisBlock;
    communication: AnalysisBlock;
    trust: AnalysisBlock;
    longTerm: AnalysisBlock;
  };
  strengths: ComparisonItem[];
  challenges: ComparisonItem[];
  verdict: string;
  recommendations: string[];
  qrUrl?: string;
}

/** Map API `page1_dashboard` + bundle fields into dashboard props. */
export function mapFromPdfContext(
  ctx: {
    page1_dashboard?: {
      love_score?: number;
      summary_index?: string;
      scores?: { label: string; value: string; band?: string }[];
    };
    page4_dimensions?: { label: string; score: number; key: string }[];
    page14_closing?: string;
  },
  p1: { name?: string },
  p2: { name?: string },
  extras?: Partial<LoveRealityReportData>,
): LoveRealityReportData {
  const dash = ctx.page1_dashboard ?? {};
  const scores = dash.scores ?? [];
  const pick = (label: string) =>
    scores.find((s) => s.label.toLowerCase().includes(label.toLowerCase()));
  const num = (row?: { value: string }) => {
    const n = parseInt(String(row?.value ?? "0"), 10);
    return Number.isFinite(n) ? n : 0;
  };
  const dims = ctx.page4_dimensions ?? [];
  const dim = (key: string) => dims.find((d) => d.key === key)?.score ?? 0;

  const love = num(pick("Love"));
  const breakup = num(pick("Breakup"));
  const loyalty = num(pick("Loyalty"));
  const reunion = num(pick("Return"));

  return {
    reportId: extras?.reportId ?? `LR-${Date.now().toString(36).toUpperCase()}`,
    generatedAt: extras?.generatedAt ?? new Date().toISOString(),
    p1Name: p1.name ?? "Partner A",
    p2Name: p2.name ?? "Partner B",
    cosmicAlignmentScore: dash.love_score ?? love,
    relationshipSummary:
      extras?.relationshipSummary ??
      dash.summary_index ??
      "Your charts show a complex bond with strong pull and recurring friction windows.",
    metrics: {
      loveCompatibility: {
        label: "Love Compatibility",
        value: love,
        interpretation: pick("Love")?.band || "Emotional resonance across charts",
      },
      breakupRisk: {
        label: "Breakup Risk",
        value: breakup,
        interpretation: pick("Breakup")?.band || "Stress-trigger separation probability",
        invert: true,
      },
      loyalty: {
        label: "Loyalty & Trust",
        value: loyalty,
        interpretation: pick("Loyalty")?.band || "Commitment under pressure",
      },
      reunionChance: {
        label: "Reunion Chance",
        value: reunion,
        interpretation: pick("Return")?.band || "Return window if separated",
      },
    },
    snapshot:
      extras?.snapshot ??
      dash.summary_index ??
      "This connection carries magnetic attraction with uneven emotional pacing.",
    keyInsights: extras?.keyInsights ?? [
      { text: "Moon rhythm mismatch amplifies silent periods" },
      { text: "Mercury styles differ — repair within 24h after conflict" },
      { text: "Dasha window favors stability in next 90 days" },
    ],
    aiExplanation:
      extras?.aiExplanation ??
      dash.summary_index ??
      "AI synthesis: attraction is real, but loyalty drops when silence exceeds 48 hours.",
    analysis: extras?.analysis ?? {
      emotional: {
        title: "Emotional Compatibility",
        score: dim("emotional") || Math.round(love * 0.9),
        explanation:
          "Feelings run deep but peak at different speeds — one partner needs reassurance while the other needs space.",
      },
      communication: {
        title: "Communication",
        score: dim("communication") || Math.max(20, 100 - breakup),
        explanation:
          "Direct vs indirect styles clash under stress. Scheduled check-ins reduce misread signals.",
      },
      trust: {
        title: "Trust & Loyalty",
        score: loyalty,
        explanation:
          "Trust holds when transparency is proactive. Hidden resentment erodes scores faster than open conflict.",
      },
      longTerm: {
        title: "Long-Term Potential",
        score: dim("stability") || Math.round((love + loyalty) / 2),
        explanation:
          "Long horizon is workable with shared rituals. Without repair habits, cycles repeat every 6–8 months.",
      },
    },
    strengths: extras?.strengths ?? [
      { label: "Emotional magnetism", value: Math.min(100, love + 8) },
      { label: "Shared growth intent", value: Math.min(100, loyalty) },
      { label: "Karmic pull", value: dim("karmic") || 62 },
    ],
    challenges: extras?.challenges ?? [
      { label: "Communication gaps", value: Math.min(100, breakup) },
      { label: "Trust under stress", value: Math.min(100, 100 - loyalty) },
      { label: "Timing misalignment", value: Math.min(100, reunion > 50 ? 40 : 68) },
    ],
    verdict: extras?.verdict ?? ctx.page14_closing ?? "Proceed with eyes open — timing and repair habits decide the outcome.",
    recommendations: extras?.recommendations ?? [
      "24-hour repair rule after any argument",
      "Weekly 20-min phone-free check-in",
      "Track dasha dates — avoid ultimatums in down windows",
    ],
    qrUrl: extras?.qrUrl ?? "https://cosmiclens.app",
  };
}
