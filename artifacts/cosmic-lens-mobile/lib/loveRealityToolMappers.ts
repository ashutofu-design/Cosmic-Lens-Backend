/** Maps Love Reality API payloads → minimal single-screen UI model */

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

export interface LoveRealityBasicDisplay {
  visual: LoveVisualKind;
  percent?: number;
  riskScore?: number;
  riskLevel?: string;
  statusLabel?: string;
  statusAccent?: string;
  hookLine: string;
  chartProof?: ChartProof | null;
  loyaltyCompare?: LoyaltyCompareData;
}

function withProof(json: Record<string, unknown>, base: LoveRealityBasicDisplay): LoveRealityBasicDisplay {
  const chartProof = parseChartProof(json);
  const hookLine = chartProof?.cosmicHook?.trim() || base.hookLine;
  return { ...base, chartProof, hookLine };
}

function firstReason(reasons?: string[]): string {
  const r = reasons?.find(x => typeof x === "string" && x.trim());
  if (!r) return "";
  const t = r.trim();
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

export function mapLoveCompatibility(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const score = Number(json.score) || 0;
  const reasons = json.reasons as string[] | undefined;
  const hook =
    firstReason(reasons) ||
    (score >= 75
      ? "Strong cosmic tuning — yet one blind spot can still create emotional distance."
      : score >= 50
        ? "Real connection is present — a temporary planetary shadow is testing patience."
        : "Attraction exists — but misaligned rhythms are amplifying misunderstandings.");
  return withProof(json, {
    visual: "circular",
    percent: Math.round(Math.max(0, Math.min(100, score))),
    hookLine: hook,
  });
}

export function mapBreakupChances(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const score = Number(json.breakup_score) || 0;
  const risk = String(json.risk_level || "medium");
  const hook =
    firstReason(json.reasons as string[]) ||
    (risk.includes("high")
      ? "Breakup pressure is elevated — one trigger window needs careful awareness."
      : risk.includes("low")
        ? "Bond resilience is strong — still, one transit can stir old friction."
        : "Mixed stress signals — small choices in the next phase carry outsized weight.");
  return withProof(json, {
    visual: "risk-gauge",
    riskScore: Math.round(Math.max(0, Math.min(100, score))),
    riskLevel: risk,
    hookLine: hook,
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
): string {
  const you = youName.trim() || "Aap";
  const partner = partnerName.trim() || "Partner";
  const yLv = loyaltyLevelShort(compare.youLevel);
  const pLv = loyaltyLevelShort(compare.partnerLevel);

  if (compare.higherSide === "you") {
    return `${you} ki loyalty zyada hai (${compare.youScore}/100, ${yLv}) — ${partner} thodi kam stable (${compare.partnerScore}/100, ${pLv}).`;
  }
  if (compare.higherSide === "partner") {
    return `${partner} ki loyalty zyada hai (${compare.partnerScore}/100, ${pLv}) — ${you} ke chart mein zyada risk signs (${compare.youScore}/100, ${yLv}).`;
  }
  return `${you} aur ${partner} dono ki loyalty same level par hai (${compare.youScore}/100) — behavior aur timing decide karenge.`;
}

export function mapLoyaltyCheck(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const { label, accent } = loyaltyStatusLabel(json);
  const compare = parseLoyaltyCompare(json);
  const tie = json.loyalty_tie_breaker as Record<string, unknown> | null | undefined;
  const dutyBound = Boolean(json.is_duty_bound_loyal);
  const hook =
    firstReason(json.reasons as string[]) ||
    (dutyBound
      ? "Saturn–Moon duty-bound pattern — dukh sahen karte hain, dhoka ka pattern kam."
      : null) ||
    (tie?.applied && typeof tie.note === "string" ? tie.note : null) ||
    "Dono charts mein loyalty alag-alag layer par dikhti hai — neeche compare dekho.";
  return withProof(json, {
    visual: "status-card",
    statusLabel: label,
    statusAccent: accent,
    hookLine: hook,
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
    firstReason(json.reasons as string[]) ||
    `Charts hint at ${chance} reconnection energy — exact timing stays locked in your full report.`;
  return { visual: "status-card", statusLabel: label, statusAccent: accent, hookLine: hook };
}

function futureStatusLabel(json: Record<string, unknown>): { label: string; accent: string } {
  const outcome = String(json.outcome || "").toLowerCase();
  const phase = String(json.current_phase || "");
  const score = Number(json.future_score) || 50;
  if (outcome.includes("positive") || outcome.includes("strong") || score >= 70) {
    return { label: "Bright Trajectory", accent: "#22c55e" };
  }
  if (outcome.includes("challeng") || score < 40) {
    return { label: "Karmic Test", accent: "#ef4444" };
  }
  if (phase) {
    const short = phase.length > 28 ? `${phase.slice(0, 25)}…` : phase;
    return { label: short, accent: "#c084fc" };
  }
  return { label: "Evolving Bond", accent: "#a855f7" };
}

export function mapFutureOutcome(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const { label, accent } = futureStatusLabel(json);
  const hook =
    firstReason(json.reasons as string[]) ||
    fallbackHook("future-outcome");
  return withProof(json, { visual: "status-card", statusLabel: label, statusAccent: accent, hookLine: hook });
}

export function mapLoveRealityResult(
  tool: LoveRealityToolKey,
  json: Record<string, unknown>,
): LoveRealityBasicDisplay {
  switch (tool) {
    case "love-compat":
      return mapLoveCompatibility(json);
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
      return mapFutureOutcome(json);
    default:
      return { visual: "status-card", statusLabel: "Reading Ready", statusAccent: "#a855f7", hookLine: fallbackHook("love-compat") };
  }
}
