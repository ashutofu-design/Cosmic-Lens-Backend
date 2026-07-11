import type { AskLlmContext, AskQuestionItem } from "./api";
import { parseAskLlmContext } from "./AskLlmContextPanel";

export interface ObservabilityPipelineStep {
  label: string;
  value: string;
}

export interface ObservabilityModule {
  module: string;
  loaded: boolean;
}

export interface ObservabilityRule {
  rule_id?: string;
  module?: string;
  polarity?: string;
  weight?: number;
  note?: string;
  reason?: string;
}

export interface ObservabilityEvidence {
  label: string;
  weight: number;
  polarity: string;
}

export interface ObservabilityHallucination {
  field: string;
  engine: string;
  narrator: string;
  ok: boolean;
}

export interface ObservabilityHallucinationSummary {
  engine_facts_used?: { ok: boolean; detail?: string };
  extra_llm_assumptions?: { ok: boolean; items?: string[] };
  missing_engine_evidence?: { ok: boolean; items?: string[] };
}

export interface AskObservability {
  user_question?: ObservabilityPipelineStep[];
  question_dna_pipeline?: ObservabilityPipelineStep[];
  routing_decision?: {
    selected_engine?: string;
    why_selected?: string;
    rejected_engines?: string[];
    routing_warning?: string | null;
  };
  routing_warning?: string | null;
  engine_execution?: {
    engine_name?: string;
    engine_version?: string;
    modules?: ObservabilityModule[];
    modules_skipped?: string[];
    execution_time_ms?: number | null;
    fired?: ObservabilityRule[];
    ignored?: ObservabilityRule[];
    final_score?: number | string | null;
    verdict_level?: string | null;
    verdict?: string | null;
  };
  astrology_checks?: Record<string, string[]>;
  planet_evidence?: {
    positive?: ObservabilityEvidence[];
    negative?: ObservabilityEvidence[];
    neutral?: ObservabilityEvidence[];
  };
  conflict_resolution?: {
    modules?: { module: string; polarity: string }[];
    d1_vs_d9?: string;
    dasha_vs_transit?: string;
    conflict?: string;
    final_result?: string;
    reason?: string;
    detected?: boolean;
  };
  scorecard?: Record<string, number>;
  engine_verdict?: {
    verdict?: string | null;
    level?: string | null;
    confidence?: number | string | null;
    strongest?: string[] | ObservabilityEvidence[];
    weakest?: string[] | ObservabilityEvidence[];
    timing?: string | null;
    warnings?: string[];
  };
  narrator_input?: Record<string, unknown> | null;
  narrator_output?: string | null;
  hallucination_checks?: ObservabilityHallucination[];
  hallucination_summary?: ObservabilityHallucinationSummary;
  performance?: {
    model?: string | null;
    max_tokens?: number | null;
    chart_chars?: number;
    system_prompt_chars?: number;
    llm_called?: boolean;
    cache_hit?: boolean | null;
    total_tokens?: number | null;
    prompt_tokens?: number | null;
    completion_tokens?: number | null;
    cached_tokens?: number | null;
    cost_inr?: number | null;
    cost_usd?: number | null;
    response_time_ms?: number | null;
  };
  final_trace?: ObservabilityPipelineStep[];
  final_trace_labels?: string[];
  has_v2_rules?: boolean;
  has_step_audit?: boolean;
}

export const SCORECARD_ORDER = [
  "Trust",
  "Commitment",
  "Communication",
  "Compatibility",
  "Chemistry",
  "Family",
  "Overall",
  "Overall Score",
] as const;

export const ASTRO_MODULE_LABELS: Record<string, string> = {
  d1: "D1 — what was checked",
  d9: "D9 — what was checked",
  dasha: "Dasha — what was checked",
  transit: "Transit — what was checked",
  kp: "KP — what was checked",
  jaimini: "Jaimini — what was checked",
  ashtakavarga: "Ashtakavarga — what was checked",
  bcp: "BCP — what was checked",
};

export function orderScorecardEntries(
  scorecard: Record<string, number>,
): [string, number][] {
  const entries = Object.entries(scorecard);
  const orderMap = new Map(
    SCORECARD_ORDER.map((k, i) => [k.toLowerCase(), i]),
  );
  return entries.sort(([a], [b]) => {
    const ai = orderMap.get(a.toLowerCase()) ?? 99;
    const bi = orderMap.get(b.toLowerCase()) ?? 99;
    if (ai !== bi) return ai - bi;
    return a.localeCompare(b);
  });
}

function buildFallbackObservability(
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): AskObservability {
  const li = ctx?.llm_intent || {};
  const sm = ctx?.slice_meta || {};
  const checks = (ctx?.checks || {}) as Record<string, unknown>;
  const smChecks = (sm.checks || {}) as Record<string, unknown>;
  const ef = ctx?.engine_facts || {};

  const userQuestion: ObservabilityPipelineStep[] = [
    { label: "Original Question", value: row.question_text || ctx?.question || "—" },
    { label: "Normalized Question", value: ctx?.question_normalized || ctx?.question || "—" },
    { label: "Language", value: String(li.language || "—") },
    { label: "Answer Language", value: String(li.reply_lang || li.language || "—") },
  ];

  const pipeline: ObservabilityPipelineStep[] = [
    { label: "Domain", value: String(li.domain || li.routed_domain || "—") },
    { label: "Bucket", value: String(li.bucket || li.mr_bucket || row.topic || "—") },
    { label: "Intent", value: String(li.intent || li.question_intent || "—") },
    { label: "Subject", value: String(li.subject || "—") },
    { label: "Target", value: String(li.target || "—") },
    { label: "Question Type", value: String(ctx?.question_type || "—") },
    { label: "Timing / Non-Timing", value: ctx?.is_timing ? "Timing" : "Non-Timing" },
    { label: "Emotion", value: String(li.emotion || "—") },
    { label: "Risk", value: String(li.risk || "—") },
    { label: "Primary Engine", value: String(sm.archetype || li.mr_archetype || "—") },
    { label: "Secondary Engine", value: "—" },
    { label: "DNA Confidence", value: String(li.confidence ?? "—") },
  ];

  const rulesFired = (checks.rules_fired || smChecks.rules_fired || []) as ObservabilityRule[];
  const scorecard = (checks.scorecard || smChecks.scorecard || {}) as Record<string, number>;

  const pos = (ef.evidence_positive || sm.evidence_positive || []) as string[];
  const neg = (ef.evidence_negative || sm.evidence_negative || []) as string[];
  const neu = (ef.evidence_neutral || sm.evidence_neutral || []) as string[];

  const modules = [
    { module: "D1", loaded: true },
    { module: "D9", loaded: true },
    { module: "DASHA", loaded: Boolean(ctx?.is_timing) },
    { module: "TRANSIT", loaded: Boolean(ctx?.is_timing) },
    { module: "KP", loaded: false },
    { module: "ASHTAKAVARGA", loaded: false },
  ];

  return {
    user_question: userQuestion,
    question_dna_pipeline: pipeline,
    routing_decision: {
      selected_engine: String(sm.archetype || li.mr_archetype || "—"),
      why_selected: String(ctx?.engine_route_reason || "—"),
      rejected_engines: [],
    },
    engine_execution: {
      engine_name: String(sm.archetype || "—"),
      modules,
      modules_skipped: modules.filter((m) => !m.loaded).map((m) => m.module),
      fired: rulesFired,
      ignored: [],
      final_score: (checks.primary_score as number) ?? null,
      verdict: String(sm.verdict || ef.verdict || row.verdict_summary || "—"),
      verdict_level: String(checks.level || checks.commitment_level || "—"),
    },
    astrology_checks: {},
    planet_evidence: {
      positive: pos.map((label) => ({ label, weight: 10, polarity: "positive" })),
      negative: neg.map((label) => ({ label, weight: -5, polarity: "negative" })),
      neutral: neu.map((label) => ({ label, weight: 0, polarity: "neutral" })),
    },
    conflict_resolution: {
      modules: [],
      d1_vs_d9: "—",
      dasha_vs_transit: "—",
      conflict: checks.contradiction ? "Minor" : "None",
      final_result: checks.contradiction ? "Minor conflict detected" : "No conflict",
      reason: String(checks.contradiction_pattern || "—"),
      detected: Boolean(checks.contradiction),
    },
    scorecard: Object.fromEntries(
      Object.entries(scorecard).filter(([k]) => k !== "primary").map(([k, v]) => [k, Number(v)]),
    ),
    engine_verdict: {
      verdict: String(sm.verdict || "—"),
      level: String(checks.level || checks.commitment_level || "—"),
      confidence: (checks.primary_score as number) ?? null,
      strongest: pos.slice(0, 3),
      weakest: neg.slice(0, 2),
      timing: "—",
      warnings: [],
    },
    narrator_input: (checks.narrator_input as Record<string, unknown>) || null,
    narrator_output: row.answer_text,
    hallucination_checks: [],
    hallucination_summary: {
      engine_facts_used: { ok: pos.length + neg.length > 0, detail: "fallback — limited data" },
      extra_llm_assumptions: { ok: true, items: [] },
      missing_engine_evidence: { ok: true, items: [] },
    },
    performance: {
      model: row.llm_model,
      llm_called: ctx?.llm_called !== false,
      total_tokens: row.total_tokens,
      prompt_tokens: row.prompt_tokens,
      completion_tokens: row.completion_tokens,
      cached_tokens: row.cached_tokens,
      cost_inr: row.cost_inr,
      cost_usd: row.cost_usd,
      cache_hit: row.cached_tokens ? true : row.total_tokens ? false : null,
    },
    final_trace: [
      { label: "Question", value: row.question_text || "—" },
      { label: "DNA", value: String(li.domain || "—") },
      { label: "Routing", value: String(sm.archetype || "—") },
      { label: "Engine", value: String(sm.archetype || "—") },
      { label: "Modules", value: String(modules.filter((m) => m.loaded).length) },
      { label: "Rules", value: String(rulesFired.length) },
      { label: "Evidence", value: String(pos.length + neg.length) },
      { label: "Score", value: String(checks.primary_score ?? "—") },
      { label: "Verdict", value: String(sm.verdict || "—") },
      { label: "Narrator JSON", value: checks.narrator_input ? "saved" : "—" },
      { label: "LLM Answer", value: row.answer_text ? "saved" : "—" },
    ],
    has_v2_rules: rulesFired.length > 0,
    has_step_audit: Boolean(sm.step_audit),
  };
}

export function resolveAskObservability(row: AskQuestionItem): AskObservability {
  const ctx = parseAskLlmContext(row);
  const obs = (ctx as AskLlmContext & { observability?: AskObservability })?.observability;
  if (obs && typeof obs === "object") return obs;
  return buildFallbackObservability(ctx, row);
}
