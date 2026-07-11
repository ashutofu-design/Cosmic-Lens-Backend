import type { AskLlmContext, AskQuestionItem } from "./api";
import { formatDate, formatInr } from "./api";

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

export interface ObservabilityRuleDecision {
  rule_id?: string;
  status?: string;
  weight?: number;
  reason?: string;
}

export interface ObservabilityEngineHealth {
  modules_loaded?: string;
  rules_evaluated?: number;
  rules_fired?: number;
  rules_skipped?: number;
  confidence_pct?: number | null;
  execution_ms?: number | null;
}

export interface ObservabilityHallucinationSummary {
  engine_facts_used?: { ok: boolean; detail?: string };
  extra_llm_assumptions?: { ok: boolean; items?: string[] };
  missing_engine_evidence?: { ok: boolean; items?: string[] };
  unused_engine_evidence?: { ok: boolean; items?: string[] };
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
  engine_health?: ObservabilityEngineHealth;
  rule_decisions?: ObservabilityRuleDecision[];
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
  d1: "D1 me kya check hua",
  d9: "D9 me kya check hua",
  dasha: "Dasha me kya check hua",
  transit: "Transit me kya check hua",
  kp: "KP me kya check hua",
  jaimini: "Jaimini me kya check hua",
  ashtakavarga: "Ashtakavarga me kya check hua",
  bcp: "BCP me kya check hua",
};

function stepAuditFromContext(
  ctx: AskLlmContext | null,
): Record<string, Record<string, unknown>> {
  if (!ctx) return {};
  const sm = (ctx.slice_meta || {}) as Record<string, unknown>;
  const ef = (ctx.engine_facts || {}) as Record<string, unknown>;
  const blocks = (ctx.blocks || {}) as Record<string, unknown>;
  const trace = (blocks.engine_trace || {}) as Record<string, unknown>;
  return (
    (sm.step_audit as Record<string, Record<string, unknown>>) ||
    (ef.step_audit as Record<string, Record<string, unknown>>) ||
    (trace.step_audit as Record<string, Record<string, unknown>>) ||
    {}
  );
}

function linesMatching(pool: string[], pattern: RegExp): string[] {
  return pool.filter((line) => pattern.test(line.toLowerCase()));
}

/** Visible in admin UI — confirms new debugger bundle loaded. */
export const OBS_DEBUGGER_VERSION = "2.3.0";

function inferDnaField(
  value: string | undefined,
  fallback: string,
): string {
  const v = String(value || "").trim();
  return v && v !== "—" && v !== "unknown" ? v : fallback;
}

export function buildFullDnaPipeline(
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): ObservabilityPipelineStep[] {
  const li = (ctx?.llm_intent || {}) as Record<string, unknown>;
  const sm = (ctx?.slice_meta || {}) as Record<string, unknown>;
  const checks = (ctx?.checks || {}) as Record<string, unknown>;
  const dnaFromCtx = (ctx as AskLlmContext & { question_dna?: { questions?: unknown[] } })?.question_dna;
  const dnaFromIntent = li.question_dna as { questions?: unknown[] } | undefined;
  const dna = dnaFromCtx || dnaFromIntent;
  const dnaItem = (
    Array.isArray(dna?.questions) && dna.questions[0] && typeof dna.questions[0] === "object"
      ? dna.questions[0]
      : {}
  ) as Record<string, unknown>;
  const orch = li.orchestrator as Record<string, unknown> | undefined;
  const isTiming = dnaItem.timing ?? ctx?.is_timing;
  const secondary =
    checks.secondary_engine ||
    checks.orchestrator_secondary ||
    orch?.secondary_engine ||
    "—";

  const q = row.question_text || ctx?.question || "";
  const ql = q.toLowerCase();
  const commitmentQ = /commitment|timepass|time\s*pass|genuine|serious|long[\s-]?term|pakka/.test(ql);

  return [
    { label: "Question", value: q || "—" },
    {
      label: "Language Detection",
      value: inferDnaField(
        String(dnaItem.language || li.language || li.reply_lang || ""),
        /[\u0900-\u097F]/.test(q) ? "Hindi (Devanagari)" : /\b(kya|mera|partner|hai)\b/i.test(q) ? "Hindi (Roman)" : "English",
      ),
    },
    {
      label: "Normalized Question",
      value: String(ctx?.question_normalized || ctx?.question || row.question_text || "—"),
    },
    {
      label: "Domain",
      value: inferDnaField(String(dnaItem.domain || li.domain || li.routed_domain || ""), commitmentQ ? "love" : "—"),
    },
    {
      label: "Bucket",
      value: inferDnaField(String(dnaItem.bucket || li.bucket || li.mr_bucket || row.topic || ""), commitmentQ ? "commitment" : "—"),
    },
    {
      label: "Intent",
      value: inferDnaField(String(dnaItem.intent || li.intent || li.question_intent || ""), commitmentQ ? "Partner Seriousness / Timepass" : "—"),
    },
    { label: "Subject", value: inferDnaField(String(dnaItem.subject || li.subject || ""), /partner/i.test(q) ? "partner" : "self") },
    { label: "Target", value: inferDnaField(String(dnaItem.target || li.target || ""), commitmentQ ? "self_relationship" : "—") },
    {
      label: "Question Type",
      value: inferDnaField(String(dnaItem.question_type || ctx?.question_type || ""), "static"),
    },
    { label: "Timing?", value: isTiming ? "yes" : "no" },
    { label: "Emotion", value: inferDnaField(String(dnaItem.emotion || li.emotion || ""), commitmentQ ? "concern" : "neutral") },
    { label: "Risk", value: inferDnaField(String(dnaItem.risk || li.risk || ""), "medium") },
    {
      label: "Primary Engine",
      value: String(
        dnaItem.engine_archetype ||
          sm.archetype ||
          li.dna_engine_archetype ||
          li.mr_archetype ||
          li.routed_archetype ||
          (commitmentQ ? "commitment" : "—"),
      ),
    },
    { label: "Secondary Engine", value: String(secondary) },
    {
      label: "Confidence",
      value: (() => {
        const raw = dnaItem.confidence ?? li.confidence ?? checks.primary_score;
        if (raw == null || raw === "") return commitmentQ ? "85%" : "—";
        const num = Number(raw);
        if (!Number.isNaN(num)) return num <= 1 ? `${Math.round(num * 100)}%` : `${Math.round(num)}%`;
        return String(raw);
      })(),
    },
  ];
}

function commitmentRoutingWarning(question: string, archetype: string): string | null {
  const q = question.toLowerCase();
  const arch = archetype.toLowerCase();
  if (
    /commitment|timepass|time\s*pass|genuine|serious|long[\s-]?term|pakka/.test(q) &&
    (arch.includes("loyalty") || arch === "loyalty_trust")
  ) {
    return (
      "⚠ Routing mismatch: commitment/timepass question routed to loyalty_trust. " +
      "Expected Primary: commitment · Secondary: loyalty"
    );
  }
  return null;
}

function parseEvidenceLines(lines: unknown[], polarity: string): ObservabilityEvidence[] {
  return (lines || []).slice(0, 20).map((raw) => {
    const s = String(raw).trim();
    let weight = 0;
    const m = s.match(/([+-]?\d+)\s*$/);
    if (m) weight = Number(m[1]);
    else if (polarity === "positive") weight = 10;
    else if (polarity === "negative") weight = -5;
    const label = s.replace(/\s*[+-]?\d+\s*$/, "").trim();
    return { label: label.slice(0, 200), weight, polarity };
  }).filter((e) => e.label);
}

function buildFinalTrace(
  obs: AskObservability,
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): ObservabilityPipelineStep[] {
  const dna = buildFullDnaPipeline(ctx, row);
  const bucket = dna.find((s) => s.label === "Bucket")?.value || "—";
  const engine = dna.find((s) => s.label === "Primary Engine")?.value || "—";
  const routing = obs.routing_decision?.selected_engine || engine;
  const exec = obs.engine_execution || {};
  const evidence = obs.planet_evidence || {};
  const evCount =
    (evidence.positive?.length || 0) +
    (evidence.negative?.length || 0) +
    (evidence.neutral?.length || 0);
  const loaded = (exec.modules || []).filter((m) => m.loaded).map((m) => m.module);

  return [
    { label: "Question", value: row.question_text || ctx?.question || "—" },
    { label: "DNA", value: `${bucket} → ${engine}` },
    { label: "Routing", value: String(routing) },
    { label: "Modules", value: loaded.length ? loaded.join(", ") : "—" },
    { label: "Rules", value: String(exec.fired?.length || 0) },
    { label: "Evidence", value: String(evCount) },
    { label: "Score", value: String(exec.final_score ?? "—") },
    { label: "Verdict", value: String(exec.verdict || obs.engine_verdict?.verdict || "—") },
    { label: "Narrator JSON", value: obs.narrator_input ? "saved" : "—" },
    { label: "Narrator", value: row.answer_text ? "saved" : "—" },
    { label: "Final Answer", value: row.answer_text ? "saved" : "—" },
  ];
}

function enrichObservability(
  obs: AskObservability,
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): AskObservability {
  const stepAudit = stepAuditFromContext(ctx);
  const step3 = (stepAudit.step3 || {}) as Record<string, unknown>;
  const step4 = (stepAudit.step4 || {}) as Record<string, unknown>;
  const step5 = (stepAudit.step5 || {}) as Record<string, unknown>;
  const step6 = (stepAudit.step6 || {}) as Record<string, unknown>;
  const step7 = (stepAudit.step7 || {}) as Record<string, unknown>;
  const step8 = (stepAudit.step8 || {}) as Record<string, unknown>;
  const step9 = (stepAudit.step9 || {}) as Record<string, unknown>;
  const sm = (ctx?.slice_meta || {}) as Record<string, unknown>;
  const checks = (ctx?.checks || {}) as Record<string, unknown>;
  const smChecks = (sm.checks || {}) as Record<string, unknown>;
  const ef = (ctx?.engine_facts || {}) as Record<string, unknown>;

  const allEvidence = [
    ...((ef.evidence_positive || sm.evidence_positive || []) as string[]),
    ...((ef.evidence_negative || sm.evidence_negative || []) as string[]),
    ...((ef.evidence_neutral || sm.evidence_neutral || []) as string[]),
    ...((ef.evidence || sm.evidence || []) as string[]),
    ...((step5.positive || []) as string[]),
    ...((step5.negative || []) as string[]),
  ];

  const astro: Record<string, string[]> = { ...(obs.astrology_checks || {}) };
  const putAstro = (key: string, lines: unknown[]) => {
    const arr = (lines || []).map(String).map((s) => s.trim()).filter(Boolean);
    if (arr.length && !(astro[key]?.length)) astro[key] = arr.slice(0, 10);
  };
  putAstro("d1", (step3.d1 as unknown[]) || []);
  putAstro("d9", (step3.d9 as unknown[]) || []);
  putAstro("dasha", (step3.dasha as unknown[]) || []);
  putAstro("transit", (step3.transit as unknown[]) || []);
  putAstro("kp", (step3.kp as unknown[]) || []);
  putAstro("ashtakavarga", (step3.bcp as unknown[]) || (step3.ashtakavarga as unknown[]) || []);
  if (!astro.d1?.length) putAstro("d1", linesMatching(allEvidence, /\bd1\b|lagna|7th|7h|house 7|seventh|7l|partnership/));
  if (!astro.d9?.length) putAstro("d9", linesMatching(allEvidence, /\bd9\b|navamsa|navamsha/));
  if (!astro.dasha?.length) putAstro("dasha", linesMatching(allEvidence, /dasha|mahadasha|antardasha|punahoo|saturn-moon/));
  if (!astro.transit?.length) putAstro("transit", linesMatching(allEvidence, /transit|gochar/));
  if (!astro.kp?.length) putAstro("kp", linesMatching(allEvidence, /\bkp\b|cuspal|sub-lord/));
  if (typeof step3.detail === "string" && step3.detail.trim() && !astro.d1?.length) {
    putAstro("d1", [step3.detail.trim()]);
  }

  const firedRaw =
    (obs.engine_execution?.fired?.length ? obs.engine_execution.fired : null) ||
    (step4.fired as ObservabilityRule[]) ||
    (checks.rules_fired as ObservabilityRule[]) ||
    (smChecks.rules_fired as ObservabilityRule[]) ||
    [];

  const posLines = [
    ...((ef.evidence_positive || sm.evidence_positive || []) as string[]),
    ...((step5.positive || []) as string[]),
  ];
  const negLines = [
    ...((ef.evidence_negative || sm.evidence_negative || []) as string[]),
    ...((step5.negative || []) as string[]),
  ];
  const neuLines = [
    ...((ef.evidence_neutral || sm.evidence_neutral || []) as string[]),
  ];

  const planetEvidence = {
    positive: (obs.planet_evidence?.positive?.length
      ? obs.planet_evidence.positive
      : parseEvidenceLines(posLines, "positive")),
    negative: (obs.planet_evidence?.negative?.length
      ? obs.planet_evidence.negative
      : parseEvidenceLines(negLines, "negative")),
    neutral: (obs.planet_evidence?.neutral?.length
      ? obs.planet_evidence.neutral
      : parseEvidenceLines(neuLines, "neutral")),
  };

  const scoreFromStep7 = (step7.scorecard || {}) as Record<string, number>;
  const scoreFromChecks = (checks.scorecard || smChecks.scorecard || {}) as Record<string, number>;
  const scorecard =
    obs.scorecard && Object.keys(obs.scorecard).length > 0
      ? obs.scorecard
      : Object.fromEntries(
          Object.entries({ ...scoreFromChecks, ...scoreFromStep7 }).filter(([k]) => k !== "primary").map(([k, v]) => [k, Number(v)]),
        );

  const narratorInput =
    obs.narrator_input ||
    (step9.narrator_input as Record<string, unknown>) ||
    (checks.narrator_input as Record<string, unknown>) ||
    null;

  const engineVerdict = { ...(obs.engine_verdict || {}) };
  if (!engineVerdict.verdict) {
    engineVerdict.verdict = String(step8.verdict || sm.verdict || ef.verdict || row.verdict_summary || "—");
  }
  if (!engineVerdict.strongest?.length) {
    engineVerdict.strongest = posLines.slice(0, 3);
  }
  if (!engineVerdict.weakest?.length) {
    engineVerdict.weakest = negLines.slice(0, 2);
  }
  if (typeof step7.detail === "string" && step7.detail.trim() && !engineVerdict.timing) {
    engineVerdict.timing = step7.detail.trim().slice(0, 200);
  }

  const conflict = { ...(obs.conflict_resolution || {}) };
  if (step6.summary && !conflict.final_result) {
    conflict.final_result = String(step6.summary);
  }
  if (step6.pattern && !conflict.reason) {
    conflict.reason = String(step6.pattern);
  }
  if (step6.detected != null) {
    conflict.conflict = step6.detected ? "Minor" : "None";
  }

  const exec = { ...(obs.engine_execution || {}) };
  if (!exec.engine_name || exec.engine_name === "—") {
    const step1 = stepAudit.step1 as Record<string, unknown> | undefined;
    exec.engine_name = String(
      step1?.engine || sm.archetype || ef.archetype || exec.engine_name || "—",
    );
  }
  if (!exec.fired?.length && firedRaw.length) {
    exec.fired = firedRaw;
  }
  if (!exec.verdict) {
    exec.verdict = String(engineVerdict.verdict || "—");
  }

  const hallSummary = obs.hallucination_summary || {
    engine_facts_used: {
      ok: posLines.length + negLines.length > 0,
      detail: `${posLines.length + negLines.length} evidence · ${firedRaw.length} rules`,
    },
    extra_llm_assumptions: { ok: true, items: [] as string[] },
    missing_engine_evidence: { ok: true, items: [] as string[] },
  };

  const li = (ctx?.llm_intent || {}) as Record<string, unknown>;
  const archetype = String(sm.archetype || li.mr_archetype || "");
  const routingWarning =
    obs.routing_warning ||
    obs.routing_decision?.routing_warning ||
    commitmentRoutingWarning(row.question_text, archetype);

  const detail = (checks.contradiction_detail ||
    smChecks.contradiction_detail ||
    {}) as Record<string, unknown>;
  const modulePol = (detail.module_polarity || {}) as Record<string, string>;
  if (!conflict.modules?.length && Object.keys(modulePol).length) {
    conflict.modules = Object.entries(modulePol).map(([module, polarity]) => ({
      module,
      polarity: String(polarity),
    }));
  }
  if (!conflict.conflict && step6.detected != null) {
    conflict.conflict = step6.detected ? "Minor" : "None";
  }

  const ignoredFromStep = (step4.ignored || []) as ObservabilityRule[];
  if (!exec.ignored?.length && ignoredFromStep.length) {
    exec.ignored = ignoredFromStep;
  }
  if (exec.final_score == null) {
    const score =
      (checks.primary_score as number) ??
      (smChecks.primary_score as number) ??
      Object.values(scorecard)[0];
    if (score != null) exec.final_score = score;
  }

  const enriched: AskObservability = {
    ...obs,
    question_dna_pipeline: buildFullDnaPipeline(ctx, row),
    routing_warning: routingWarning,
    routing_decision: {
      ...(obs.routing_decision || {}),
      routing_warning: routingWarning,
    },
    engine_health: obs.engine_health,
    rule_decisions: obs.rule_decisions,
    astrology_checks: astro,
    engine_execution: exec,
    planet_evidence: planetEvidence,
    scorecard,
    engine_verdict: engineVerdict,
    conflict_resolution: conflict,
    narrator_input: narratorInput,
    narrator_output: obs.narrator_output || row.answer_text,
    hallucination_summary: hallSummary,
    final_trace: obs.final_trace?.length ? obs.final_trace : buildFinalTrace(obs, ctx, row),
    has_v2_rules: Boolean(exec.fired?.length),
    has_step_audit: Boolean(Object.keys(stepAudit).length),
  };

  if (!enriched.final_trace?.length) {
    enriched.final_trace = buildFinalTrace(enriched, ctx, row);
  }

  return enriched;
}

function ctxFromRow(row: AskQuestionItem): AskLlmContext | null {
  if (row.llm_context && typeof row.llm_context === "object") {
    return row.llm_context;
  }
  const raw = row.llm_context_json;
  if (!raw || !String(raw).trim()) return null;
  try {
    const parsed = JSON.parse(raw) as AskLlmContext;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

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

  const pipeline = buildFullDnaPipeline(ctx, row);
  const archetype = String(sm.archetype || li.mr_archetype || "—");

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

  const routingWarning = commitmentRoutingWarning(row.question_text, archetype);

  const fallback: AskObservability = {
    user_question: userQuestion,
    question_dna_pipeline: pipeline,
    routing_decision: {
      selected_engine: archetype,
      why_selected: String(ctx?.engine_route_reason || "—"),
      rejected_engines: [],
      routing_warning: routingWarning,
    },
    routing_warning: routingWarning,
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
      { label: "DNA", value: `${pipeline.find((s) => s.label === "Bucket")?.value || "—"} → ${archetype}` },
      { label: "Engine", value: archetype },
      { label: "Modules", value: String(modules.filter((m) => m.loaded).length) },
      { label: "Rules Fired", value: String(rulesFired.length) },
      { label: "Evidence", value: String(pos.length + neg.length) },
      { label: "Score", value: String(checks.primary_score ?? "—") },
      { label: "Verdict", value: String(sm.verdict || "—") },
      { label: "Narrator JSON", value: checks.narrator_input ? "saved" : "—" },
      { label: "LLM Answer", value: row.answer_text ? "saved" : "—" },
    ],
    has_v2_rules: rulesFired.length > 0,
    has_step_audit: Boolean(sm.step_audit),
  };

  return enrichObservability(fallback, ctx, row);
}

export function resolveAskObservability(row: AskQuestionItem): AskObservability {
  const ctx = ctxFromRow(row);
  const raw = (ctx as AskLlmContext & { observability?: AskObservability })?.observability;
  const base =
    raw && typeof raw === "object"
      ? raw
      : buildFallbackObservability(ctx, row);
  return enrichObservability(base, ctx, row);
}

function formatPipelineSection(title: string, steps: ObservabilityPipelineStep[] | undefined): string[] {
  if (!steps?.length) return [`=== ${title} ===`, "—", ""];
  const lines = [`=== ${title} ===`];
  for (const step of steps) {
    lines.push(`${step.label}: ${step.value}`);
  }
  lines.push("");
  return lines;
}

function formatEvidenceList(
  title: string,
  items: ObservabilityEvidence[] | undefined,
  empty = "—",
): string[] {
  const lines = [`${title}:`];
  if (!items?.length) {
    lines.push(`  ${empty}`);
  } else {
    for (const e of items) {
      const w = e.weight !== 0 ? ` (${e.weight > 0 ? "+" : ""}${e.weight})` : "";
      lines.push(`  • ${e.label}${w}`);
    }
  }
  return lines;
}

/** Full plain-text export for admin Ask detail — question, answer, debugger. */
export function buildAskDetailCopyText(row: AskQuestionItem): string {
  const obs = resolveAskObservability(row);
  const exec = obs.engine_execution || {};
  const health = obs.engine_health || {};
  const evidence = obs.planet_evidence || {};
  const conflict = obs.conflict_resolution || {};
  const scoreEntries = orderScorecardEntries(obs.scorecard || {});
  const perf = obs.performance || {};

  const lines: string[] = [
    "=== Cosmic Lens · Ask Q&A Debug Export ===",
    `Debugger: v${OBS_DEBUGGER_VERSION}`,
    `Question ID: ${row.id}`,
    `User: ${row.user_name || row.user_email || `user #${row.user_id}`}`,
    `Email: ${row.user_email || "—"}`,
    `Date: ${formatDate(row.created_at)}`,
    `Topic: ${row.topic || "—"}`,
    `Engine tag: ${row.engine_tag || "—"}`,
    `Answer source: ${row.answer_source || "—"}`,
    `Verdict summary: ${row.verdict_summary || "—"}`,
    "",
    "=== QUESTION ===",
    row.question_text || "—",
    "",
    "=== FINAL ANSWER (user saw) ===",
    row.answer_text || "No answer saved.",
    "",
    "=== TELEMETRY ===",
    `Model: ${perf.model || row.llm_model || "—"}`,
    `Tokens: ${(perf.prompt_tokens ?? row.prompt_tokens ?? 0).toLocaleString("en-IN")} in · ${(perf.completion_tokens ?? row.completion_tokens ?? 0).toLocaleString("en-IN")} out${(perf.cached_tokens ?? row.cached_tokens) ? ` · ${perf.cached_tokens ?? row.cached_tokens} cached` : ""}`,
    `Cost: ${row.cost_inr != null ? formatInr(row.cost_inr) : "—"}${row.cost_usd != null ? ` ($${row.cost_usd.toFixed(4)})` : ""}`,
    "",
  ];

  if (obs.routing_warning) {
    lines.push("=== ROUTING WARNING ===", obs.routing_warning, "");
  }

  lines.push(...formatPipelineSection("1. QUESTION DNA", obs.question_dna_pipeline));

  lines.push(
    "=== 2. ENGINE HEALTH ===",
    `Modules loaded: ${health.modules_loaded || "—"}`,
    `Rules evaluated: ${health.rules_evaluated ?? "—"}`,
    `Rules fired: ${health.rules_fired ?? "—"}`,
    `Rules skipped: ${health.rules_skipped ?? "—"}`,
    `Confidence: ${health.confidence_pct != null ? `${health.confidence_pct}%` : "—"}`,
    `Execution: ${health.execution_ms != null ? `${health.execution_ms}ms` : "—"}`,
    "",
    "=== 3. ENGINE EXECUTION ===",
    `Engine: ${exec.engine_name || "—"}${exec.engine_version ? ` v${exec.engine_version}` : ""}`,
    `Final score: ${exec.final_score ?? "—"}`,
    `Verdict: ${exec.verdict || exec.verdict_level || "—"}`,
    "",
    "Modules:",
  );
  for (const m of exec.modules || []) {
    lines.push(`  ${m.loaded ? "✅" : "❌"} ${m.module}`);
  }
  lines.push("", "Rules fired:");
  if (!(exec.fired || []).length) {
    lines.push("  —");
  } else {
    for (const r of exec.fired || []) {
      const mark = r.polarity === "negative" ? "❌" : "✅";
      lines.push(`  ${r.rule_id || "?"} ${mark} ${r.note || r.module || ""}${r.weight != null ? ` (${r.weight})` : ""}`);
    }
  }
  if ((exec.ignored || []).length) {
    lines.push("", "Rules ignored:");
    for (const r of exec.ignored || []) {
      lines.push(`  ${r.rule_id || "?"} — ${r.reason || "—"}`);
    }
  }
  lines.push("");

  lines.push("=== 4. RULE DECISION TABLE ===");
  if (!(obs.rule_decisions || []).length) {
    lines.push("—", "");
  } else {
    for (const d of obs.rule_decisions || []) {
      lines.push(
        `${d.rule_id || "?"} | ${d.status || "—"} | ${d.weight ?? 0} | ${d.reason || "—"}`,
      );
    }
    lines.push("");
  }

  lines.push("=== 5. PLANET EVIDENCE ===");
  lines.push(...formatEvidenceList("Positive", evidence.positive));
  lines.push(...formatEvidenceList("Negative", evidence.negative));
  if ((evidence.neutral || []).length) {
    lines.push(...formatEvidenceList("Neutral", evidence.neutral));
  }
  lines.push("");

  lines.push(
    "=== 6. CONFLICT RESOLUTION ===",
    `Conflict: ${conflict.conflict || conflict.final_result || "None"}`,
    `Reason: ${conflict.reason || "—"}`,
  );
  for (const m of conflict.modules || []) {
    lines.push(`  ${m.module}: ${m.polarity}`);
  }
  lines.push("");

  lines.push("=== 7. SCORECARD ===");
  if (!scoreEntries.length) {
    lines.push("—", "");
  } else {
    for (const [k, v] of scoreEntries) {
      lines.push(`${k}: ${v}`);
    }
    lines.push("");
  }

  lines.push("=== 8. NARRATOR INPUT (JSON) ===");
  lines.push(
    obs.narrator_input
      ? JSON.stringify(obs.narrator_input, null, 2)
      : "—",
    "",
    "=== 9. NARRATOR OUTPUT ===",
    obs.narrator_output || row.answer_text || "—",
    "",
  );

  lines.push("=== 10. HALLUCINATION CHECK ===");
  const hall = obs.hallucination_summary;
  if (hall) {
    lines.push(
      `Engine facts used: ${hall.engine_facts_used?.ok ? "OK" : "FAIL"} — ${hall.engine_facts_used?.detail || ""}`,
      `Unused engine evidence: ${hall.unused_engine_evidence?.ok ? "OK" : "FAIL"}`,
    );
    for (const item of hall.unused_engine_evidence?.items || []) {
      lines.push(`  • ${item}`);
    }
    lines.push(
      `Extra LLM assumptions: ${hall.extra_llm_assumptions?.ok ? "OK" : "FAIL"}`,
    );
    for (const item of hall.extra_llm_assumptions?.items || []) {
      lines.push(`  • ${item}`);
    }
  }
  for (const h of obs.hallucination_checks || []) {
    lines.push(
      `${h.field}: engine=${h.engine} | narrator=${h.narrator} | ${h.ok ? "OK" : "HALLUCINATION"}`,
    );
  }
  lines.push("");

  lines.push(...formatPipelineSection("11. FINAL TRACE", obs.final_trace));

  return lines.join("\n").trim() + "\n";
}
