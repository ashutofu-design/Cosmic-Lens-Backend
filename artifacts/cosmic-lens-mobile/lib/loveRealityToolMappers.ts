/** Maps Love Reality API payloads → minimal single-screen UI model */

import {
  coerceLoveBasicLang,
  pickLoveBasicCopy,
  type LoveBasicLang,
} from "@/lib/loveRealityBasicLang";
import { parseChartProof, type ChartProof } from "@/lib/loveRealityChartProof";

export type LoveRealityToolKey =
  | "love-compat"
  | "breakup"
  | "loyalty"
  | "will-return"
  | "future-outcome";

export type LoveVisualKind = "circular" | "risk-gauge" | "status-card";

/** Per-person loyalty scores from API (p1 = you, p2 = partner). */
export type LoyaltyCompareData = {
  youScore: number;
  partnerScore: number;
  youLevel: string;
  partnerLevel: string;
  higherSide: "you" | "partner" | "tie";
  youDutyBound?: boolean;
  partnerDutyBound?: boolean;
  /** True when built from love-compat afflictions (older server without per_person). */
  estimated?: boolean;
};

export type LoveDimensionBar = {
  key: string;
  label: string;
  score: number;
};

export type LoveCompatDetail = {
  emotionalSummary?: string;
  riskLevel?: string;
  factors?: Record<string, string>;
  dimensions: LoveDimensionBar[];
  reasons: string[];
};

export type FutureOutcomeDetail = {
  verdictLine: string;
  reasonLine?: string;
};

export interface LoveRealityBasicDisplay {
  visual: LoveVisualKind;
  percent?: number;
  riskScore?: number;
  riskLevel?: string;
  statusLabel?: string;
  statusAccent?: string;
  hookLine: string;
  warningLine?: string;
  chartProof?: ChartProof | null;
  loyaltyCompare?: LoyaltyCompareData;
  loveDetail?: LoveCompatDetail;
  futureDetail?: FutureOutcomeDetail;
}

function withProof(json: Record<string, unknown>, base: LoveRealityBasicDisplay): LoveRealityBasicDisplay {
  return { ...base, chartProof: parseChartProof(json) };
}

/** Raw API reasons — hide planet/house jargon from Basic UI. */
export function isTechnicalChartLine(text: string): boolean {
  const t = text.trim();
  if (!t) return true;
  if (/\b(moon|venus|mars|saturn|rahu|ketu|jupiter|mercury|sun|nodes?)\b/i.test(t)) return true;
  if (/\b7th[- ]?lord\b/i.test(t)) return true;
  if (/\b(7th|5th|12th|1st|2nd|3rd|4th|6th|8th|9th|10th|11th)\s*(lord|house|axis)\b/i.test(t)) return true;
  if (/\bon 7th\b/i.test(t)) return true;
  if (/\b(dusthana|debil|neech|navamsa|d9|d1|afflict|synastry|transit|dasha|yoga)\b/i.test(t)) return true;
  if (/\b(venus|moon)\s*\/\s*(moon|venus)\b/i.test(t)) return true;
  if (/\bthird[- ]?person\b/i.test(t)) return true;
  if (/\b(ketu|rahu|mars|saturn)\s+on\b/i.test(t)) return true;
  if (/\bboth charts?\b/i.test(t)) return true;
  if (/\bsignatures?\b/i.test(t) && /\b(breakup|chart|bond|separation|break)\b/i.test(t)) return true;
  if (/'s\s+\w+/i.test(t) && /\b(moon|venus|mars|saturn|rahu|ketu|chart)\b/i.test(t)) return true;
  if (/\bunder\s+(saturn|rahu|ketu|mars|nodes?)\b/i.test(t)) return true;
  if (/saturn[\u2013-]moon/i.test(t)) return true;
  return false;
}

export function humanizeDisplayText(text: string): string {
  if (!text?.trim()) return "";
  return text
    .replace(/_/g, " ")
    .replace(/[-–—]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function sanitizeBasicHookLine(line?: string): string | undefined {
  if (!line?.trim()) return undefined;
  const clean = userFacingLine(line);
  return clean ? humanizeDisplayText(clean) : undefined;
}

function userFacingLine(text: unknown): string {
  if (typeof text !== "string") return "";
  const t = text.trim();
  if (!t || isTechnicalChartLine(t)) return "";
  return t.length > 160 ? `${t.slice(0, 157)}…` : t;
}

function fallbackHook(tool: LoveRealityToolKey): string {
  switch (tool) {
    case "love-compat":
      return "Your charts show a real pull — but one hidden factor is shaping how love actually feels day to day.";
    case "breakup":
      return "Stress signatures are active — the next few months decide whether friction fades or deepens.";
    case "loyalty":
      return "Loyalty runs deeper than words here — yet a planetary shadow can blur intentions without warning.";
    case "will-return":
      return "Reconnection energy exists in the timeline — timing and karma decide if it surfaces.";
    case "future-outcome":
      return "This bond is moving through a decisive phase — the next shift changes the long-term arc.";
  }
}

const LOVE_DIMENSION_DEFS: { key: string; label: string }[] = [
  { key: "emotional", label: "Emotional Bond" },
  { key: "attraction", label: "Attraction" },
  { key: "communication", label: "Communication" },
  { key: "karmic", label: "Karmic Link" },
  { key: "stability", label: "Stability" },
];

function parseLoveCompatDetail(json: Record<string, unknown>): LoveCompatDetail | undefined {
  const bd = json.breakdown as Record<string, unknown> | undefined;
  if (!bd) return undefined;

  const dimensions: LoveDimensionBar[] = [];
  for (const def of LOVE_DIMENSION_DEFS) {
    const v = Number(bd[def.key]);
    if (Number.isFinite(v)) {
      dimensions.push({
        key: def.key,
        label: def.label,
        score: Math.round(Math.max(0, Math.min(100, v))),
      });
    }
  }
  if (!dimensions.length) return undefined;

  const factorsRaw = json.factors as Record<string, unknown> | undefined;
  const factors: Record<string, string> = {};
  if (factorsRaw) {
    for (const [k, v] of Object.entries(factorsRaw)) {
      if (typeof v === "string" && v.trim()) factors[k] = v.trim();
    }
  }

  return {
    riskLevel: typeof json.risk_level === "string" ? json.risk_level : undefined,
    factors: Object.keys(factors).length ? factors : undefined,
    dimensions,
    reasons: [],
  };
}

export function buildLoveCompatDetailFromJson(json: Record<string, unknown>): LoveCompatDetail | undefined {
  return parseLoveCompatDetail(json);
}

export function mapLoveCompatibility(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const score = Number(json.score) || 0;
  return withProof(json, {
    visual: "circular",
    percent: Math.round(Math.max(0, Math.min(100, score))),
    hookLine: "",
    loveDetail: parseLoveCompatDetail(json),
  });
}

export function mapBreakupChances(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const score = Number(json.breakup_score) || 0;
  const risk = humanizeDisplayText(String(json.risk_level || "medium"));
  return withProof(json, {
    visual: "risk-gauge",
    riskScore: Math.round(Math.max(0, Math.min(100, score))),
    riskLevel: risk,
    hookLine: "",
  });
}

function loyaltyStatusLabel(json: Record<string, unknown>): { label: string; accent: string } {
  const level = String(json.loyalty_level || "");
  const behavior = String(json.behavior_type || "");
  if (level === "high" || behavior === "loyal") {
    return { label: "Devoted Bond", accent: "#22c55e" };
  }
  if (level === "risky" || behavior === "dual-nature") {
    return { label: "Secretive Energy", accent: "#f97316" };
  }
  if (behavior === "emotionally unstable" || level === "unstable") {
    return { label: "Volatile Heart", accent: "#ef4444" };
  }
  if (behavior === "tempted") {
    return { label: "Tempted Pull", accent: "#fbbf24" };
  }
  return { label: "Mixed Signals", accent: "#a855f7" };
}

function loyaltyLevelShort(level: string): string {
  switch (level) {
    case "high":
      return "Strong";
    case "moderate":
      return "Moderate";
    case "unstable":
      return "Weak";
    case "risky":
      return "Risky";
    default:
      return level || "—";
  }
}

function buildCompareFromScores(
  youScore: number,
  partnerScore: number,
  youLevel: string,
  partnerLevel: string,
  tie: Record<string, unknown> | null | undefined,
  duty?: { you?: boolean; partner?: boolean },
): LoyaltyCompareData {
  let higherSide: LoyaltyCompareData["higherSide"] = "tie";
  if (youScore > partnerScore) higherSide = "you";
  else if (partnerScore > youScore) higherSide = "partner";
  else if (tie?.applied && tie.lower_side === "p1") higherSide = "partner";
  else if (tie?.applied && tie.lower_side === "p2") higherSide = "you";

  return {
    youScore,
    partnerScore,
    youLevel,
    partnerLevel,
    higherSide,
    youDutyBound: duty?.you,
    partnerDutyBound: duty?.partner,
  };
}

function parseLoyaltyCompare(json: Record<string, unknown>): LoyaltyCompareData | undefined {
  const tie = json.loyalty_tie_breaker as Record<string, unknown> | null | undefined;

  const pp = json.per_person as Record<string, unknown> | undefined;
  if (pp?.p1 && pp?.p2) {
    const p1 = pp.p1 as Record<string, unknown>;
    const p2 = pp.p2 as Record<string, unknown>;
    return buildCompareFromScores(
      Math.round(Math.max(0, Math.min(100, Number(p1.score) || 0))),
      Math.round(Math.max(0, Math.min(100, Number(p2.score) || 0))),
      String(p1.loyalty_level || ""),
      String(p2.loyalty_level || ""),
      tie,
      {
        you: Boolean(p1.is_duty_bound_loyal),
        partner: Boolean(p2.is_duty_bound_loyal),
      },
    );
  }

  const p1s = Number(json.p1_loyalty_score);
  const p2s = Number(json.p2_loyalty_score);
  if (Number.isFinite(p1s) && Number.isFinite(p2s)) {
    return buildCompareFromScores(
      Math.round(Math.max(0, Math.min(100, p1s))),
      Math.round(Math.max(0, Math.min(100, p2s))),
      String(json.p1_loyalty_level || ""),
      String(json.p2_loyalty_level || ""),
      tie,
      {
        you: Boolean((json.breakdown as Record<string, unknown> | undefined)?.p1_duty_bound),
        partner: Boolean((json.breakdown as Record<string, unknown> | undefined)?.p2_duty_bound),
      },
    );
  }

  const bd = json.breakdown as Record<string, unknown> | undefined;
  const b1 = Number(bd?.p1_person_score);
  const b2 = Number(bd?.p2_person_score);
  if (Number.isFinite(b1) && Number.isFinite(b2)) {
    return buildCompareFromScores(
      Math.round(Math.max(0, Math.min(100, b1))),
      Math.round(Math.max(0, Math.min(100, b2))),
      loyaltyLevelFromScore(b1),
      loyaltyLevelFromScore(b2),
      tie,
      {
        you: Boolean(bd?.p1_duty_bound),
        partner: Boolean(bd?.p2_duty_bound),
      },
    );
  }

  return undefined;
}

function loyaltyLevelFromScore(score: number): string {
  if (score >= 72) return "high";
  if (score >= 52) return "moderate";
  if (score >= 35) return "unstable";
  return "risky";
}

/** Build compare from API JSON — used when mapped display lacks it. */
export function buildLoyaltyCompareFromJson(json: Record<string, unknown>): LoyaltyCompareData | undefined {
  return parseLoyaltyCompare(json);
}

/** Fallback when server lacks per_person — uses love-compat chart affliction weights. */
export function buildLoyaltyCompareFromLoveCompat(
  loveJson: Record<string, unknown>,
): LoyaltyCompareData | undefined {
  const bd = loveJson.breakdown as Record<string, unknown> | undefined;
  if (!bd) return undefined;
  const a1 = Number(bd.p1_affliction);
  const a2 = Number(bd.p2_affliction);
  if (!Number.isFinite(a1) || !Number.isFinite(a2)) return undefined;

  const youScore = clampScore(Math.round(78 - a1 * 0.52));
  const partnerScore = clampScore(Math.round(78 - a2 * 0.52));
  return {
    ...buildCompareFromScores(
      youScore,
      partnerScore,
      loyaltyLevelFromScore(youScore),
      loyaltyLevelFromScore(partnerScore),
      undefined,
    ),
    estimated: true,
  };
}

function clampScore(n: number): number {
  return Math.round(Math.max(0, Math.min(100, n)));
}

/** Merge loyalty + love-compat payloads into compare data. */
export function resolveLoyaltyCompare(
  loyaltyJson: Record<string, unknown> | undefined,
  loveCompatJson: Record<string, unknown> | undefined,
): LoyaltyCompareData | undefined {
  if (loyaltyJson) {
    const direct = parseLoyaltyCompare(loyaltyJson);
    if (direct) return direct;
  }
  if (loveCompatJson) {
    return buildLoyaltyCompareFromLoveCompat(loveCompatJson);
  }
  return undefined;
}

export function loyaltyCompareVerdict(
  compare: LoyaltyCompareData,
  youName: string,
  partnerName: string,
  lang: LoveBasicLang = "en",
): string {
  const you = youName.trim() || pickLoveBasicCopy(lang, "You", "Aap", "आप");
  const partner = partnerName.trim() || pickLoveBasicCopy(lang, "Partner", "Partner", "साथी");

  if (compare.higherSide === "you") {
    return pickLoveBasicCopy(
      lang,
      `${you} shows stronger loyalty than ${partner}.`,
      `${you} zyada loyal hai, ${partner} utna nahi.`,
      `${you} की वफ़ादारी ${partner} से ज़्यादा है।`,
    );
  }
  if (compare.higherSide === "partner") {
    return pickLoveBasicCopy(
      lang,
      `${partner} shows stronger loyalty than ${you}.`,
      `${partner} zyada loyal hai, ${you} utna nahi.`,
      `${partner} की वफ़ादारी ${you} से ज़्यादा है।`,
    );
  }
  return pickLoveBasicCopy(
    lang,
    `${you} and ${partner} show equal loyalty.`,
    `${you} aur ${partner} dono ki loyalty barabar hai.`,
    `${you} और ${partner} की वफ़ादारी बराबर है।`,
  );
}

export function mapLoyaltyCheck(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const { label, accent } = loyaltyStatusLabel(json);
  const compare = parseLoyaltyCompare(json);
  return withProof(json, {
    visual: "status-card",
    statusLabel: label,
    statusAccent: accent,
    hookLine: "",
    loyaltyCompare: compare,
  });
}

function returnStatusLabel(chance: string): { label: string; accent: string } {
  const c = chance.toLowerCase();
  if (c.includes("very")) return { label: "Very Strong Pull", accent: "#22c55e" };
  if (c === "strong") return { label: "Strong Chances", accent: "#4ade80" };
  if (c === "possible") return { label: "Possible Return", accent: "#fbbf24" };
  return { label: "Unlikely Path", accent: "#94a3b8" };
}

export function mapWillReturn(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const chance = String(json.return_chance || "possible");
  const { label, accent } = returnStatusLabel(chance);
  const hook =
    userFacingLine(json.emotional_summary) ||
    `Charts hint at ${chance} reconnection energy — exact timing stays locked in your full report.`;
  return { visual: "status-card", statusLabel: label, statusAccent: accent, hookLine: hook };
}

function futureStatusLabel(json: Record<string, unknown>): { label: string; accent: string } {
  const outcome = String(json.outcome || "").toLowerCase();
  const phase = String(json.current_phase || "");
  const score = Number(json.future_score ?? json.score) || 50;
  if (outcome.includes("thriving") || outcome.includes("growing") || score >= 70) {
    return { label: "Bright Trajectory", accent: "#22c55e" };
  }
  if (outcome.includes("fading") || score < 28) {
    return { label: "Closure Energy", accent: "#ef4444" };
  }
  if (outcome.includes("strained") || (score >= 28 && score < 42)) {
    return { label: "Strained Phase", accent: "#f97316" };
  }
  if (outcome.includes("mixed") || score >= 42) {
    return { label: "Mixed Future", accent: "#fbbf24" };
  }
  if (phase) {
    const short = humanizeDisplayText(phase);
    const clipped = short.length > 28 ? `${short.slice(0, 25)}…` : short;
    return { label: clipped, accent: "#c084fc" };
  }
  return { label: "Evolving Bond", accent: "#a855f7" };
}

function pickFutureReason(json: Record<string, unknown>): string {
  const warning = userFacingLine(json.timeline_validation_warning);
  const raw = (json.reasons as string[] | undefined) ?? [];
  for (const r of raw) {
    const line = userFacingLine(r);
    if (line && line !== warning) return line.length > 120 ? `${line.slice(0, 117)}…` : line;
  }
  return warning.length > 120 ? `${warning.slice(0, 117)}…` : warning;
}

function buildFutureUserLines(
  json: Record<string, unknown>,
  score: number,
  lang: LoveBasicLang,
): FutureOutcomeDetail {
  const reasonFromApi = pickFutureReason(json);

  if (score >= 58) {
    return polishFutureLines({
      verdictLine: pickLoveBasicCopy(
        lang,
        "Yes — the charts point to a strong long-term future for this bond.",
        "Haan, charts is rishte ka long term future strong dikhate hain.",
        "हाँ — कुंडली इस रिश्ते का दीर्घकालिक भविष्य मज़बूत दिखाती है।",
      ),
    });
  }
  if (score >= 42) {
    return polishFutureLines({
      verdictLine: pickLoveBasicCopy(
        lang,
        "The future is mixed — the bond can hold, but the current phase is unstable.",
        "Future mixed hai, rishta tik sakta hai, par abhi phase unstable hai.",
        "भविष्य मिश्रित है — रिश्ता टिक सकता है, पर अभी चरण अस्थिर है।",
      ),
      reasonLine:
        reasonFromApi ||
        pickLoveBasicCopy(
          lang,
          "Timing and dasha will decide whether the bond deepens or drifts.",
          "Timing aur dasha ab decide karenge ki bond deepen hoga ya drift karega.",
          "समय और दशा तय करेंगे कि बंधन गहरा होगा या दूर होगा।",
        ),
    });
  }
  if (score >= 28) {
    return polishFutureLines({
      verdictLine: pickLoveBasicCopy(
        lang,
        "The long-term outlook looks weak right now — stability is not assured.",
        "Abhi long term future weak dikhta hai, stability assured nahi.",
        "अभी दीर्घकालिक भविष्य कमज़ोर दिखता है — स्थिरता तय नहीं।",
      ),
      reasonLine:
        reasonFromApi ||
        pickLoveBasicCopy(
          lang,
          "Emotional fatigue is building — exhaustion is outpacing growth.",
          "Emotional fatigue build ho rahi hai, grow karne ki jagah exhaustion zyada active hai.",
          "भावनात्मक थकान बढ़ रही है — विकास की जगह थकावट ज़्यादा सक्रिय है।",
        ),
    });
  }
  return polishFutureLines({
    verdictLine: pickLoveBasicCopy(
      lang,
      "No — the charts lean toward closure or distance in this bond.",
      "Nahi, charts is rishte mein closure ya distance ki taraf lean karte hain.",
      "नहीं — कुंडली इस रिश्ते में अलगाव या दूरी की ओर झुकती है।",
    ),
    reasonLine:
      reasonFromApi ||
      pickLoveBasicCopy(
        lang,
        "Without long-term stability, emotional exhaustion is the dominant pattern.",
        "Long term stability ke bina emotional exhaustion zyada active hai.",
        "दीर्घकालिक स्थिरता के बिना भावनात्मक थकान ज़्यादा सक्रिय है।",
      ),
  });
}

function polishFutureLines(lines: FutureOutcomeDetail): FutureOutcomeDetail {
  return {
    verdictLine: humanizeDisplayText(lines.verdictLine),
    reasonLine: lines.reasonLine ? humanizeDisplayText(lines.reasonLine) : undefined,
  };
}

function buildFutureUserDetail(
  json: Record<string, unknown>,
  lang: LoveBasicLang,
): FutureOutcomeDetail | undefined {
  const score = Number(json.future_score ?? json.score);
  if (!Number.isFinite(score)) return undefined;
  const rounded = Math.round(Math.max(0, Math.min(100, score)));
  return buildFutureUserLines(json, rounded, lang);
}

export function mapFutureOutcome(
  json: Record<string, unknown>,
  lang: LoveBasicLang = "en",
): LoveRealityBasicDisplay {
  const score = Number(json.future_score ?? json.score) || 0;
  const rounded = Math.round(Math.max(0, Math.min(100, score)));
  const detail = buildFutureUserDetail(json, lang) ?? buildFutureUserLines(json, rounded, lang);
  const { label, accent } = futureStatusLabel(json);
  return withProof(json, {
    visual: "circular",
    percent: rounded,
    statusLabel: label,
    statusAccent: accent,
    hookLine: detail.verdictLine,
    warningLine: detail.reasonLine,
    futureDetail: detail,
  });
}

export function mapLoveRealityResult(
  tool: LoveRealityToolKey,
  json: Record<string, unknown>,
  lang?: string | null,
): LoveRealityBasicDisplay {
  const lane = coerceLoveBasicLang(lang);
  switch (tool) {
    case "love-compat": {
      const mapped = mapLoveCompatibility(json);
      if (!mapped.loveDetail) {
        const detail = buildLoveCompatDetailFromJson(json);
        if (detail) return { ...mapped, loveDetail: detail };
      }
      return mapped;
    }
    case "breakup":
      return mapBreakupChances(json);
    case "loyalty": {
      const mapped = mapLoyaltyCheck(json);
      if (!mapped.loyaltyCompare) {
        const compare = buildLoyaltyCompareFromJson(json);
        if (compare) return { ...mapped, loyaltyCompare: compare };
      }
      return mapped;
    }
    case "will-return":
      return mapWillReturn(json);
    case "future-outcome":
      return mapFutureOutcome(json, lane);
    default:
      return { visual: "status-card", statusLabel: "Reading Ready", statusAccent: "#a855f7", hookLine: fallbackHook("love-compat") };
  }
}
