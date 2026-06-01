/** Maps Love Reality API payloads → minimal single-screen UI model */

import { parseChartProof, type ChartProof } from "@/lib/loveRealityChartProof";

export type LoveRealityToolKey =
  | "love-compat"
  | "breakup"
  | "loyalty"
  | "will-return"
  | "future-outcome";

export type LoveVisualKind = "circular" | "risk-gauge" | "status-card";

export interface LoveRealityBasicDisplay {
  visual: LoveVisualKind;
  percent?: number;
  riskScore?: number;
  riskLevel?: string;
  statusLabel?: string;
  statusAccent?: string;
  hookLine: string;
  chartProof?: ChartProof | null;
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

export function mapLoyaltyCheck(json: Record<string, unknown>): LoveRealityBasicDisplay {
  const { label, accent } = loyaltyStatusLabel(json);
  const hook =
    firstReason(json.reasons as string[]) ||
    "Faithfulness has layers in this chart — surface calm can hide a karmic test in loyalty.";
  return withProof(json, { visual: "status-card", statusLabel: label, statusAccent: accent, hookLine: hook });
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
    case "loyalty":
      return mapLoyaltyCheck(json);
    case "will-return":
      return mapWillReturn(json);
    case "future-outcome":
      return mapFutureOutcome(json);
    default:
      return { visual: "status-card", statusLabel: "Reading Ready", statusAccent: "#a855f7", hookLine: fallbackHook("love-compat") };
  }
}
