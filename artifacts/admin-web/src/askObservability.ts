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

export interface AskObservability {
  question_dna_pipeline?: ObservabilityPipelineStep[];
  routing_warning?: string | null;
  engine_execution?: {
    modules?: ObservabilityModule[];
    fired?: ObservabilityRule[];
    ignored?: ObservabilityRule[];
    final_score?: number | string | null;
    verdict_level?: string | null;
    verdict?: string | null;
  };
  planet_evidence?: {
    positive?: ObservabilityEvidence[];
    negative?: ObservabilityEvidence[];
  };
  conflict_resolution?: {
    modules?: { module: string; polarity: string }[];
    conflict?: string;
    reason?: string;
    detected?: boolean;
  };
  scorecard?: Record<string, number>;
  narrator_input?: Record<string, unknown> | null;
  narrator_output?: string | null;
  hallucination_checks?: ObservabilityHallucination[];
  final_trace?: string[];
  has_v2_rules?: boolean;
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

  const pipeline: ObservabilityPipelineStep[] = [
    { label: "Question", value: row.question_text || ctx?.question || "—" },
    { label: "Language Detection", value: String(li.language || "—") },
    { label: "Normalized Question", value: ctx?.question_normalized || ctx?.question || "—" },
    { label: "Domain", value: String(li.domain || li.routed_domain || "—") },
    { label: "Bucket", value: String(li.bucket || li.mr_bucket || row.topic || "—") },
    { label: "Intent", value: String(li.intent || li.question_intent || "—") },
    { label: "Subject", value: String(li.subject || "—") },
    { label: "Target", value: String(li.target || "—") },
    { label: "Question Type", value: String(ctx?.question_type || "—") },
    { label: "Timing?", value: ctx?.is_timing ? "yes" : "no" },
    { label: "Emotion", value: String(li.emotion || "—") },
    { label: "Risk", value: String(li.risk || "—") },
    { label: "Primary Engine", value: String(sm.archetype || li.mr_archetype || "—") },
    { label: "Secondary Engine", value: "—" },
    { label: "Confidence", value: String(li.confidence ?? "—") },
  ];

  const rulesFired = (checks.rules_fired || smChecks.rules_fired || []) as ObservabilityRule[];
  const scorecard = (checks.scorecard || smChecks.scorecard || {}) as Record<string, number>;

  const pos = (ef.evidence_positive || sm.evidence_positive || []) as string[];
  const neg = (ef.evidence_negative || sm.evidence_negative || []) as string[];

  return {
    question_dna_pipeline: pipeline,
    engine_execution: {
      modules: [
        { module: "D1", loaded: true },
        { module: "D9", loaded: true },
        { module: "DASHA", loaded: Boolean(ctx?.is_timing) },
        { module: "TRANSIT", loaded: Boolean(ctx?.is_timing) },
      ],
      fired: rulesFired,
      ignored: [],
      final_score: (checks.primary_score as number) ?? null,
      verdict: String(sm.verdict || ef.verdict || row.verdict_summary || "—"),
      verdict_level: String(checks.level || checks.commitment_level || "—"),
    },
    planet_evidence: {
      positive: pos.map((label) => ({ label, weight: 10, polarity: "positive" })),
      negative: neg.map((label) => ({ label, weight: -5, polarity: "negative" })),
    },
    conflict_resolution: {
      modules: [],
      conflict: checks.contradiction ? "Minor" : "None",
      reason: String(checks.contradiction_pattern || "—"),
      detected: Boolean(checks.contradiction),
    },
    scorecard: Object.fromEntries(
      Object.entries(scorecard).filter(([k]) => k !== "primary").map(([k, v]) => [k, Number(v)]),
    ),
    narrator_input: (checks.narrator_input as Record<string, unknown>) || null,
    narrator_output: row.answer_text,
    hallucination_checks: [],
    final_trace: [
      "Question",
      "DNA",
      "Engine",
      "Modules",
      "Rules Fired",
      "Evidence",
      "Score",
      "Verdict",
      "Narrator JSON",
      "LLM Answer",
    ],
    has_v2_rules: rulesFired.length > 0,
  };
}

export function resolveAskObservability(row: AskQuestionItem): AskObservability {
  const ctx = parseAskLlmContext(row);
  const obs = (ctx as AskLlmContext & { observability?: AskObservability })?.observability;
  if (obs && typeof obs === "object") return obs;
  return buildFallbackObservability(ctx, row);
}
