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

export interface ObservabilityHealthValidatorCheck {
  id?: string;
  label?: string;
  passed?: boolean;
  issues?: string[];
  detail?: string;
}

export interface ObservabilityHealthSelectedBlock {
  id?: string;
  label?: string;
  why?: string;
  detail?: string;
  rank?: number;
  priority?: number;
  role?: string;
}

export interface ObservabilityHealthSelectedBlocks {
  applies?: boolean;
  source?: string;
  focus?: string;
  focus_label?: string;
  available_blocks?: ObservabilityHealthSelectedBlock[];
  expected_blocks?: ObservabilityHealthSelectedBlock[];
  used_in_answer?: {
    planets?: string[];
    houses?: number[];
    planet_house_cites?: string[];
    dimension_themes?: string[];
    blocks?: ObservabilityHealthSelectedBlock[];
  };
  overlap_notes?: string[];
  contract?: Record<string, string>;
  error?: string;
}

export interface ObservabilityHealthDnaJudge {
  enabled?: boolean;
  passed?: boolean | null;
  issues?: string[];
  fix_hint?: string | null;
  skipped?: string;
}

export interface ObservabilityHealthDnaJudgeAudit {
  applies?: boolean;
  enabled?: boolean;
  passed?: boolean;
  issues?: string[];
  fix_hint?: string | null;
  contract?: Record<string, string>;
  judge_version?: string;
  contract_keys?: string[];
  skipped?: string;
  error?: string;
  source?: string;
  selected_blocks?: ObservabilityHealthSelectedBlocks;
}

/** Map legacy health_validator_audit rows → DNA Judge-only display shape. */
export function normalizeHealthDnaJudgeAudit(
  raw: ObservabilityHealthDnaJudgeAudit | ObservabilityHealthValidatorAudit | undefined,
): ObservabilityHealthDnaJudgeAudit | undefined {
  if (!raw) return undefined;
  if (raw.applies === false) return { applies: false };

  const legacy = raw as ObservabilityHealthValidatorAudit;
  const nested = legacy.dna_judge;
  const hasLegacyChecks = (legacy.checks || []).length > 0;
  const hasLegacyValidator =
    legacy.attempts != null || legacy.released_anyway != null || legacy.final_block != null;

  if (!nested && !hasLegacyChecks && !hasLegacyValidator && raw.contract) {
    return raw as ObservabilityHealthDnaJudgeAudit;
  }

  if (nested || hasLegacyChecks || hasLegacyValidator) {
    const judgeCheck = (legacy.checks || []).find((c) => c.id === "dna_llm_judge");
    return {
      applies: true,
      enabled: nested?.enabled ?? raw.enabled ?? true,
      passed:
        nested?.passed != null
          ? Boolean(nested.passed)
          : judgeCheck?.passed != null
            ? Boolean(judgeCheck.passed)
            : raw.passed,
      issues: [
        ...(nested?.issues || []),
        ...(judgeCheck?.issues || []),
        ...(raw.issues || []),
        ...(legacy.final_issues || []),
      ].filter((x, i, arr) => x && arr.indexOf(x) === i),
      fix_hint: nested?.fix_hint || judgeCheck?.detail || raw.fix_hint || null,
      contract: raw.contract,
      judge_version: raw.judge_version || "health_dna_v2",
      skipped: nested?.skipped,
      source: raw.source || "legacy_validator_audit",
    };
  }

  return raw as ObservabilityHealthDnaJudgeAudit;
}

/** @deprecated use ObservabilityHealthDnaJudgeAudit */
export interface ObservabilityHealthValidatorAudit extends ObservabilityHealthDnaJudgeAudit {
  attempts?: number;
  final_block?: boolean;
  released_anyway?: boolean;
  final_issues?: string[];
  checks?: ObservabilityHealthValidatorCheck[];
  chart_support_signals?: string[];
  dna_judge?: ObservabilityHealthDnaJudge;
}

export interface ObservabilityEngineHealth {
  modules_loaded?: string;
  rules_evaluated?: number;
  rules_fired?: number;
  rules_skipped?: number;
  confidence_pct?: number | null;
  execution_ms?: number | null;
}

export interface ObservabilityHealthChartFacts {
  schema_version?: string;
  chart?: string;
  ascendant?: string;
  lagnesh?: Record<string, unknown>;
  vitality_score?: number;
  vitality_risk?: string;
  planets?: Array<{
    name?: string;
    sign?: string;
    house?: number;
    degree?: number | null;
    dignity?: string;
    strength_score?: number;
    shadbala?: {
      total?: number;
      required?: number;
      strength_pct?: number;
      parts?: Record<string, unknown>;
    } | null;
    retrograde?: boolean;
    combust?: boolean;
    health_roles?: string[];
  }>;
  houses?: Array<Record<string, unknown>>;
  health_houses?: Array<{
    house?: number;
    sign?: string;
    lord?: string;
    lord_state?: {
      lord?: string;
      lord_house?: number;
      lord_dignity?: string;
      lord_strength_score?: number;
      lord_shadbala?: { strength_pct?: number } | null;
      lord_in_dusthana?: boolean;
    };
    occupants?: string[];
    aspects_received?: Array<{
      planet?: string;
      from_house?: number;
      to_house?: number;
      polarity?: string;
    }>;
    health_roles?: string[];
  }>;
  /** Relationship engine pack uses this key instead of health_houses */
  relationship_houses?: Array<{
    house?: number;
    sign?: string;
    lord?: string;
    lord_state?: {
      lord?: string;
      lord_house?: number;
      lord_dignity?: string;
      lord_strength_score?: number;
      lord_shadbala?: { strength_pct?: number } | null;
      lord_in_dusthana?: boolean;
    };
    occupants?: string[];
    aspects_received?: Array<{
      planet?: string;
      from_house?: number;
      to_house?: number;
      polarity?: string;
    }>;
    health_roles?: string[];
  }>;
  /** Finance engine pack uses this key instead of health_houses */
  finance_houses?: Array<{
    house?: number;
    sign?: string;
    lord?: string;
    lord_state?: {
      lord?: string;
      lord_house?: number;
      lord_dignity?: string;
      lord_strength_score?: number;
      lord_shadbala?: { strength_pct?: number } | null;
      lord_in_dusthana?: boolean;
    };
    occupants?: string[];
    aspects_received?: Array<{
      planet?: string;
      from_house?: number;
      to_house?: number;
      polarity?: string;
    }>;
    health_roles?: string[];
  }>;
  house_lords?: Record<string, Record<string, unknown>>;
  karakas?: Record<string, Record<string, unknown>>;
  shadbala?: Record<string, Record<string, unknown>>;
  aspects?: Array<Record<string, unknown>>;
  afflictions?: string[];
  dimensions?: Record<
    string,
    { verdict?: string; reason?: string; tier?: string; score?: number }
  >;
  wealth_yogas?: string[];
  sub_flags?: Record<string, unknown>;
  error?: string;
}

export type ObservabilityHealthD1Facts = ObservabilityHealthChartFacts;

export interface ObservabilityHealthEngineExecution {
  schema_version?: string;
  d1?: ObservabilityHealthChartFacts;
  d9?: ObservabilityHealthChartFacts;
  lagnesh?: {
    d1?: Record<string, unknown>;
    d9?: Record<string, unknown>;
  };
  vargottama_planets?: string[];
  vargottama_details?: Array<{
    planet?: string;
    d1_sign?: string;
    d1_house?: number;
    d9_sign?: string;
    d9_house?: number;
    vargottama?: boolean;
  }>;
  /** Timing asks only — current MD/AD/PD + ranked windows */
  dasha_timing_compact?: {
    schema_version?: string;
    horizon_years?: number;
    max_windows?: number;
    current?: {
      md?: string;
      ad?: string;
      pd?: string;
      window?: string | null;
      role?: string;
      why?: string;
    } | null;
    top_windows?: Array<{
      md?: string;
      ad?: string;
      pd?: string;
      window?: string | null;
      role?: string;
      score?: number;
      why?: string;
    }>;
    llm_note?: string;
    error?: string;
  };
  manglik?: {
    mars_house?: number | null;
    is_manglik?: boolean;
    classic_houses?: number[];
    [key: string]: unknown;
  };
  relationship_signals?: Record<string, unknown>;
  /** Finance pack top-level fields (also mirrored on d1) */
  dimensions?: Record<
    string,
    { verdict?: string; reason?: string; tier?: string; score?: number }
  >;
  wealth_yogas?: string[];
  sub_flags?: Record<string, unknown>;
  afflictions?: string[];
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
  health_dna_judge_audit?: ObservabilityHealthDnaJudgeAudit;
  health_selected_blocks?: ObservabilityHealthSelectedBlocks;
  /** @deprecated alias — same payload as health_dna_judge_audit */
  health_validator_audit?: ObservabilityHealthDnaJudgeAudit;
  relationship_dna_judge_audit?: ObservabilityHealthDnaJudgeAudit;
  relationship_selected_blocks?: ObservabilityHealthSelectedBlocks;
  finance_dna_judge_audit?: ObservabilityHealthDnaJudgeAudit;
  finance_selected_blocks?: ObservabilityHealthSelectedBlocks;
  travel_dna_judge_audit?: ObservabilityHealthDnaJudgeAudit;
  travel_selected_blocks?: ObservabilityHealthSelectedBlocks;
  engine_execution?: {
    display_mode?: "health_charts" | "relationship_charts" | "finance_charts" | "travel_charts" | "domain_charts" | "engine_rules";
    health_engine_execution?: ObservabilityHealthEngineExecution | null;
    relationship_engine_execution?: ObservabilityHealthEngineExecution | null;
    finance_engine_execution?: ObservabilityHealthEngineExecution | null;
    travel_engine_execution?: ObservabilityHealthEngineExecution | null;
    domain_engine_execution?: ObservabilityHealthEngineExecution | null;
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
    d1_health_facts?: ObservabilityHealthD1Facts | null;
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

export function isHealthAskRow(row: AskQuestionItem, ctx: AskLlmContext | null, exec: AskObservability["engine_execution"]): boolean {
  if (exec?.display_mode === "health_charts" || exec?.health_engine_execution) {
    return true;
  }
  const topic = (row.topic || "").trim().toLowerCase();
  if (topic === "health" || topic === "sehat") {
    return true;
  }
  const sm = (ctx?.slice_meta || {}) as Record<string, unknown>;
  const li = (ctx?.llm_intent || {}) as Record<string, unknown>;
  if (String(sm.slice || "").includes("health")) {
    return true;
  }
  if (String(li.domain || "").toLowerCase() === "health") {
    return true;
  }
  const arch = String(sm.archetype || li.mr_archetype || "").toLowerCase();
  return arch.includes("health") || arch.includes("vitality") || arch.includes("chronic");
}

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
export const OBS_DEBUGGER_VERSION = "2.6.7";

const DNA_DOMAIN_LABEL: Record<string, string> = {
  love: "Relationship",
  marriage: "Marriage",
  career: "Career",
  finance: "Finance",
  health: "Health",
  family: "Family",
  education: "Education",
  travel: "Travel",
  legal: "Legal",
  spiritual: "Spiritual",
  general: "General",
};

const DNA_BUCKET_LABEL: Record<string, string> = {
  relationship_promise: "Relationship Promise",
  love_feelings: "Love & Feelings",
  partner_nature: "Partner Nature",
  compatibility: "Compatibility",
  commitment: "Commitment",
  trust_loyalty: "Trust & Loyalty",
  communication: "Communication",
  emotional_bonding: "Emotional Bonding",
  physical_intimacy: "Physical & Intimacy",
  third_person_infidelity: "Third Person / Infidelity",
  dating_courtship: "Dating & Courtship",
  long_distance: "Long Distance",
  family_social_acceptance: "Family & Social Acceptance",
  relationship_challenges: "Relationship Challenges",
  toxicity_red_flags: "Toxicity & Red Flags",
  breakup_separation: "Breakup & Separation",
  reconciliation_ex: "Reconciliation & Ex",
  marriage_potential: "Marriage Potential",
  relationship_future: "Relationship Outcome / Long-term Stability",
  relationship_decisions: "Relationship Decisions",
  spiritual_karmic: "Soulmate & Karmic Connection",
  relationship_remedies: "Relationship Remedies",
  unknown_relationship_intent: "Unknown (Audit)",
  general_mr: "Marriage General",
};

const DNA_ENGINE_ARCHETYPE_LABEL: Record<string, string> = {
  karmic_marriage: "Soulmate & Karmic Connection",
  relationship_future: "Relationship Outcome / Long-term Stability",
};

const DNA_SUBJECT_LABEL: Record<string, string> = {
  self: "Self",
  partner: "Partner",
  spouse: "Spouse",
  family_member: "Family Member",
  other_person: "Other Person",
  subject_person: "Subject Person",
};

const DNA_TARGET_LABEL: Record<string, string> = {
  self: "Self",
  self_relationship: "Self (Relationship)",
  subject_person: "Subject Person",
  event: "Event",
  situation: "Situation",
};

function dnaDisplayLabel(map: Record<string, string>, key?: string | null): string {
  if (!key) return "—";
  return map[key] || key.replace(/_/g, " ");
}

function dnaYesNo(v?: boolean | null): string {
  if (v === true) return "Yes";
  if (v === false) return "No";
  return "—";
}

function dnaConfPct(v?: number | null): string {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  const pct = v <= 1 ? v * 100 : v;
  return `${Math.round(pct)}%`;
}

function dnaQuestionType(v?: string | null): string {
  const s = String(v || "").trim();
  if (!s || s === "—" || s === "unknown") return "—";
  return s.replace(/_/g, " ");
}

function dnaBucketMatch(
  confidence?: string | null,
  score?: number | null,
): string {
  const bmc = String(confidence || "").trim();
  if (!bmc) return "—";
  if (typeof score === "number" && !Number.isNaN(score)) {
    const pct = score <= 1 ? score * 100 : score;
    return `${bmc.toUpperCase()} (${Math.round(pct)}%)`;
  }
  return bmc.toUpperCase();
}

const DNA_ANSWER_STYLE_LABEL: Record<string, string> = {
  short_2_3_lines: "Short (2-3 lines)",
  short_paragraph: "Short paragraph (4-6 lines)",
  detailed_explain: "Detailed explanation",
};

function dnaUnderstandingConfidence(v?: number | null): string {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  const n = v <= 1 ? v : v / 100;
  const pct = Math.round(n * 100);
  let level = "Low";
  if (n >= 0.95) level = "Very high";
  else if (n >= 0.85) level = "High";
  else if (n >= 0.70) level = "Moderate";
  return `${pct}% (${level} — question understood clearly)`;
}

function dnaAnswerStyleLabel(style?: string | null): string {
  const s = String(style || "").trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (!s) return "—";
  return DNA_ANSWER_STYLE_LABEL[s] || s.replace(/_/g, " ");
}

function deriveUserWants(
  dnaItem: Record<string, unknown>,
  li: Record<string, unknown>,
  normalized: string,
): string {
  const raw = String(dnaItem.user_wants || li.user_wants || "").trim();
  if (raw) return raw;
  const intent = String(dnaItem.intent || li.intent || li.question_intent || "").trim();
  if (intent) return `User wants to know: ${intent}`;
  if (normalized && normalized !== "—") return `User wants to know: ${normalized}`;
  return "User question could not be fully decoded.";
}

function deriveAnswerApproach(
  dnaItem: Record<string, unknown>,
  li: Record<string, unknown>,
  domain: string,
  questionType: string,
  timing: boolean,
  intent: string,
  risk: string,
): string {
  const raw = String(dnaItem.answer_approach || li.answer_approach || "").trim();
  if (raw) return raw;
  const parts: string[] = [];
  if (domain === "health") {
    parts.push(
      "Use D1/D9 health chart JSON — plain language, supportive tone; no disease diagnosis or cure guarantees.",
    );
  } else {
    parts.push("Answer from chart evidence for the routed engine/archetype.");
  }
  if (timing) {
    parts.push("Lead with timing window (dasha/transit), then brief supporting reason.");
  } else if (questionType === "decision") {
    parts.push("Balanced guidance — avoid absolute yes/no unless chart is very clear.");
  } else if (questionType === "current_state") {
    parts.push("Direct present-state read — what is happening now.");
  } else if (questionType === "risk") {
    parts.push("Acknowledge emotional sensitivity; cautious wording.");
  } else if (questionType === "explanation" || questionType === "cause") {
    parts.push("Explain why/how with 2–4 supporting chart factors.");
  } else if (intent) {
    parts.push(`Focus on: ${intent}.`);
  }
  if (risk === "high") parts.push("Keep tone gentle and non-alarmist.");
  return parts.join(" ") || "—";
}

function deriveAnswerStyle(
  dnaItem: Record<string, unknown>,
  li: Record<string, unknown>,
  questionType: string,
  timing: boolean,
  isFollowup: boolean,
): string {
  const raw = String(dnaItem.answer_style || li.answer_style || "").trim();
  if (raw) return dnaAnswerStyleLabel(raw);
  if (questionType === "explanation" || questionType === "cause" || questionType === "chart_fact") {
    return DNA_ANSWER_STYLE_LABEL.detailed_explain;
  }
  if (
    questionType === "decision" ||
    questionType === "compatibility" ||
    questionType === "verification" ||
    timing
  ) {
    return DNA_ANSWER_STYLE_LABEL.short_paragraph;
  }
  if (
    (questionType === "current_state" ||
      questionType === "risk" ||
      questionType === "prediction") &&
    !timing
  ) {
    return DNA_ANSWER_STYLE_LABEL.short_2_3_lines;
  }
  if (isFollowup) return DNA_ANSWER_STYLE_LABEL.short_2_3_lines;
  return DNA_ANSWER_STYLE_LABEL.short_paragraph;
}

export function buildFullDnaPipeline(
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): ObservabilityPipelineStep[] {
  const li = (ctx?.llm_intent || {}) as Record<string, unknown>;
  const dnaFromCtx = (ctx as AskLlmContext & { question_dna?: { questions?: unknown[] } })?.question_dna;
  const dnaFromIntent = li.question_dna as { questions?: unknown[] } | undefined;
  const dna = dnaFromCtx || dnaFromIntent;
  const questions = Array.isArray(dna?.questions) ? dna!.questions : [];
  const dnaItem = (
    questions[0] && typeof questions[0] === "object" ? questions[0] : {}
  ) as Record<string, unknown>;

  const domain = String(dnaItem.domain || li.domain || li.routed_domain || "").trim().toLowerCase();
  const bucket = String(dnaItem.bucket || li.bucket || li.mr_bucket || "").trim().toLowerCase();
  const subject = String(dnaItem.subject || li.subject || "").trim().toLowerCase();
  const target = String(dnaItem.target || li.target || "").trim().toLowerCase();
  const engineArch = String(
    dnaItem.engine_archetype || li.dna_engine_archetype || li.mr_archetype || li.routed_archetype || "",
  ).trim().toLowerCase();

  const normalized =
    String(dnaItem.normalized_question || "").trim() ||
    String(ctx?.question_normalized || ctx?.question || row.question_text || "").trim() ||
    "—";

  const domainDisplay = domain
    ? `${dnaDisplayLabel(DNA_DOMAIN_LABEL, domain)} (${domain})`
    : "—";
  const bucketDisplay = bucket
    ? `${dnaDisplayLabel(DNA_BUCKET_LABEL, bucket)} (${bucket})`
    : "—";
  const subjectDisplay = subject
    ? `${dnaDisplayLabel(DNA_SUBJECT_LABEL, subject)} (${subject})`
    : "—";
  const targetDisplay = target
    ? `${dnaDisplayLabel(DNA_TARGET_LABEL, target)} (${target})`
    : "—";

  const tense = String(dnaItem.tense || "").trim().toLowerCase();
  const timeContext = tense && tense !== "unspecified" ? tense : "—";
  const timingVal = dnaItem.timing ?? ctx?.is_timing;
  const mods = (dnaItem.required_modules || li.required_modules) as unknown;
  const modules =
    Array.isArray(mods) && mods.length > 0
      ? mods.map((m) => String(m).trim().toUpperCase()).filter(Boolean).join(", ")
      : "—";
  const questionType = String(dnaItem.question_type || ctx?.question_type || "").trim().toLowerCase();
  const intent = String(dnaItem.intent || li.intent || li.question_intent || "").trim();
  const risk = String(dnaItem.risk || li.risk || "").trim().toLowerCase();
  const isFollowup = dnaItem.is_followup === true;
  const understandingConf =
    typeof dnaItem.understanding_confidence === "number"
      ? (dnaItem.understanding_confidence as number)
      : typeof dnaItem.confidence === "number"
        ? (dnaItem.confidence as number)
        : typeof li.understanding_confidence === "number"
          ? (li.understanding_confidence as number)
          : typeof li.confidence === "number"
            ? (li.confidence as number)
            : null;

  return [
    { label: "Normalized", value: normalized },
    { label: "Domain", value: domainDisplay },
    { label: "Bucket", value: bucketDisplay },
    {
      label: "Intent",
      value: String(dnaItem.intent || li.intent || li.question_intent || "—"),
    },
    { label: "Subject", value: subjectDisplay },
    { label: "Target", value: targetDisplay },
    {
      label: "Question Type",
      value: dnaQuestionType(String(dnaItem.question_type || ctx?.question_type || "")),
    },
    { label: "Timing Required", value: dnaYesNo(timingVal as boolean | null | undefined) },
    { label: "Time Context", value: timeContext },
    { label: "Follow-up", value: dnaYesNo(dnaItem.is_followup as boolean | null | undefined) },
    { label: "Multiple Questions", value: questions.length > 1 ? "Yes" : "No" },
    {
      label: "Emotion",
      value: dnaQuestionType(String(dnaItem.emotion || li.emotion || "")),
    },
    { label: "Risk", value: String(dnaItem.risk || li.risk || "—") },
    {
      label: "Engine Archetype",
      value: dnaDisplayLabel(DNA_ENGINE_ARCHETYPE_LABEL, engineArch),
    },
    { label: "Modules", value: modules },
    {
      label: "Confidence",
      value: dnaConfPct(
        typeof dnaItem.confidence === "number"
          ? dnaItem.confidence
          : typeof li.confidence === "number"
            ? (li.confidence as number)
            : null,
      ),
    },
    {
      label: "Bucket Match",
      value: dnaBucketMatch(
        String(dnaItem.bucket_match_confidence || ""),
        typeof dnaItem.bucket_match_score === "number"
          ? dnaItem.bucket_match_score
          : null,
      ),
    },
    {
      label: "LLM Understand Question",
      value: deriveUserWants(dnaItem, li, normalized),
    },
    {
      label: "Understanding Confidence",
      value: dnaUnderstandingConfidence(understandingConf),
    },
    {
      label: "Answer Style",
      value: deriveAnswerStyle(dnaItem, li, questionType, timingVal === true, isFollowup),
    },
    {
      label: "LLM Answer Plan",
      value: deriveAnswerApproach(
        dnaItem,
        li,
        domain,
        questionType,
        timingVal === true,
        intent,
        risk,
      ),
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

function getDnaPrimaryItem(ctx: AskLlmContext | null): Record<string, unknown> | null {
  const li = (ctx?.llm_intent || {}) as Record<string, unknown>;
  const dnaFromCtx = (ctx as AskLlmContext & { question_dna?: { questions?: unknown[] } })
    ?.question_dna;
  const dnaFromIntent = li.question_dna as { questions?: unknown[] } | undefined;
  const dna = dnaFromCtx || dnaFromIntent;
  const questions = Array.isArray(dna?.questions) ? dna!.questions : [];
  const item = questions[0];
  return item && typeof item === "object" ? (item as Record<string, unknown>) : null;
}

function resolveDnaPipeline(
  obs: AskObservability,
  ctx: AskLlmContext | null,
  row: AskQuestionItem,
): ObservabilityPipelineStep[] {
  // Prefer live question_dna (same source as mobile DNA Check).
  const dnaItem = getDnaPrimaryItem(ctx);
  if (dnaItem?.bucket) {
    return buildFullDnaPipeline(ctx, row);
  }
  const server = obs.question_dna_pipeline;
  const bucket = server?.find((s) => s.label === "Bucket")?.value?.trim() || "";
  if (server && server.length >= 10 && bucket && bucket !== "—") {
    return server;
  }
  return buildFullDnaPipeline(ctx, row);
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
  if (!exec.health_engine_execution) {
    const healthPack =
      checks.health_engine_execution ||
      smChecks.health_engine_execution ||
      (checks.d1_health_facts || smChecks.d1_health_facts
        ? {
            schema_version: "health_engine_execution_v1",
            d1: checks.d1_health_facts || smChecks.d1_health_facts,
            d9: checks.d9_health_facts || smChecks.d9_health_facts || { error: "d9 missing" },
          }
        : null);
    if (healthPack && typeof healthPack === "object") {
      exec.health_engine_execution = healthPack as ObservabilityHealthEngineExecution;
      exec.display_mode = "health_charts";
    }
  }
  if (isHealthAskRow(row, ctx, exec) && exec.health_engine_execution) {
    exec.display_mode = "health_charts";
  }
  if (!exec.relationship_engine_execution) {
    const relPack =
      checks.relationship_engine_execution ||
      smChecks.relationship_engine_execution ||
      null;
    if (relPack && typeof relPack === "object") {
      exec.relationship_engine_execution = relPack as ObservabilityHealthEngineExecution;
      if (exec.display_mode !== "health_charts") {
        exec.display_mode = "relationship_charts";
      }
    }
  }
  if (
    exec.display_mode !== "health_charts" &&
    exec.relationship_engine_execution &&
    (String(sm.slice || "") === "mr_engine_v1" ||
      checks.unified_execution ||
      smChecks.unified_execution)
  ) {
    exec.display_mode = "relationship_charts";
  }
  if (!exec.finance_engine_execution) {
    const finPack =
      checks.finance_engine_execution ||
      smChecks.finance_engine_execution ||
      null;
    if (finPack && typeof finPack === "object") {
      exec.finance_engine_execution = finPack as ObservabilityHealthEngineExecution;
      if (
        exec.display_mode !== "health_charts" &&
        exec.display_mode !== "relationship_charts"
      ) {
        exec.display_mode = "finance_charts";
      }
    }
  }
  if (
    exec.display_mode !== "health_charts" &&
    exec.display_mode !== "relationship_charts" &&
    exec.finance_engine_execution &&
    (String(sm.slice || "") === "finance_engine_v1" ||
      String(checks.engine_version || smChecks.engine_version || "") ===
        "finance_engine_execution_v1" ||
      checks.finance_engine_execution ||
      smChecks.finance_engine_execution)
  ) {
    exec.display_mode = "finance_charts";
  }
  if (!exec.travel_engine_execution) {
    const trvPack =
      checks.travel_engine_execution ||
      smChecks.travel_engine_execution ||
      null;
    if (trvPack && typeof trvPack === "object") {
      exec.travel_engine_execution = trvPack as ObservabilityHealthEngineExecution;
      if (
        exec.display_mode !== "health_charts" &&
        exec.display_mode !== "relationship_charts" &&
        exec.display_mode !== "finance_charts"
      ) {
        exec.display_mode = "travel_charts";
      }
    }
  }
  if (
    exec.display_mode !== "health_charts" &&
    exec.display_mode !== "relationship_charts" &&
    exec.display_mode !== "finance_charts" &&
    exec.travel_engine_execution &&
    (String(sm.slice || "") === "travel_engine_v1" ||
      String(checks.engine_version || smChecks.engine_version || "") ===
        "travel_engine_execution_v1" ||
      checks.travel_engine_execution ||
      smChecks.travel_engine_execution)
  ) {
    exec.display_mode = "travel_charts";
  }
  // Generic unified domain EE (career/education/children/…/gap topics)
  if (!exec.travel_engine_execution && !exec.finance_engine_execution && !exec.health_engine_execution) {
    const unifiedDom = String(checks.unified_domain || smChecks.unified_domain || "").trim();
    const eeKey = unifiedDom ? `${unifiedDom}_engine_execution` : "";
    const uniPack =
      (eeKey && (checks[eeKey] || smChecks[eeKey])) ||
      Object.entries({ ...smChecks, ...checks }).find(
        ([k, v]) => k.endsWith("_engine_execution") && v && typeof v === "object",
      )?.[1] ||
      null;
    if (uniPack && typeof uniPack === "object") {
      (exec as { domain_engine_execution?: unknown }).domain_engine_execution = uniPack;
      if (
        !exec.display_mode ||
        exec.display_mode === "engine_rules"
      ) {
        exec.display_mode = "domain_charts" as typeof exec.display_mode;
      }
    }
  }
  if (!exec.d1_health_facts) {
    const d1HealthFacts =
      exec.health_engine_execution?.d1 ||
      checks.d1_health_facts ||
      smChecks.d1_health_facts;
    if (d1HealthFacts && typeof d1HealthFacts === "object") {
      exec.d1_health_facts = d1HealthFacts as ObservabilityHealthD1Facts;
    }
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
    question_dna_pipeline: resolveDnaPipeline(obs, ctx, row),
    routing_warning: routingWarning,
    routing_decision: {
      ...(obs.routing_decision || {}),
      routing_warning: routingWarning,
    },
    engine_health: obs.engine_health,
    rule_decisions: obs.rule_decisions,
    health_selected_blocks:
      (obs.health_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      ((obs.health_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined)?.selected_blocks as
        | ObservabilityHealthSelectedBlocks
        | undefined) ||
      (checks.health_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.health_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      ((checks.health_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined)?.selected_blocks as
        | ObservabilityHealthSelectedBlocks
        | undefined),
    health_dna_judge_audit: normalizeHealthDnaJudgeAudit(
      obs.health_dna_judge_audit ||
        (checks.health_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (smChecks.health_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        obs.health_validator_audit ||
        (checks.health_validator_audit as ObservabilityHealthValidatorAudit | undefined) ||
        (smChecks.health_validator_audit as ObservabilityHealthValidatorAudit | undefined),
    ),
    health_validator_audit: normalizeHealthDnaJudgeAudit(
      obs.health_dna_judge_audit ||
        obs.health_validator_audit ||
        (checks.health_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (checks.health_validator_audit as ObservabilityHealthValidatorAudit | undefined),
    ),
    relationship_selected_blocks:
      (obs.relationship_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      ((obs.relationship_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined)
        ?.selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.relationship_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.relationship_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.relationship_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.relationship_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined),
    relationship_dna_judge_audit: normalizeHealthDnaJudgeAudit(
      obs.relationship_dna_judge_audit ||
        (checks.relationship_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (smChecks.relationship_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined),
    ),
    finance_selected_blocks:
      (obs.finance_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      ((obs.finance_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined)
        ?.selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.finance_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.finance_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.finance_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.finance_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined),
    finance_dna_judge_audit: normalizeHealthDnaJudgeAudit(
      obs.finance_dna_judge_audit ||
        (checks.finance_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (smChecks.finance_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined),
    ),
    travel_selected_blocks:
      (obs.travel_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      ((obs.travel_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined)
        ?.selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.travel_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.travel_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
      (checks.travel_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined) ||
      (smChecks.travel_selected_blocks_preview as ObservabilityHealthSelectedBlocks | undefined),
    travel_dna_judge_audit: normalizeHealthDnaJudgeAudit(
      obs.travel_dna_judge_audit ||
        (checks.travel_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (smChecks.travel_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined),
    ),
    // Unified remaining domains (career/education/…)
    ...((): Partial<AskObservability> => {
      const uniAudit =
        (obs as AskObservability & { unified_dna_judge_audit?: ObservabilityHealthDnaJudgeAudit })
          .unified_dna_judge_audit ||
        (checks.unified_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined) ||
        (smChecks.unified_dna_judge_audit as ObservabilityHealthDnaJudgeAudit | undefined);
      const uniBlocks =
        (checks.unified_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
        (smChecks.unified_selected_blocks as ObservabilityHealthSelectedBlocks | undefined) ||
        (uniAudit?.selected_blocks as ObservabilityHealthSelectedBlocks | undefined);
      if (!uniAudit && !uniBlocks) return {};
      return {
        // Reuse finance slots as fallback display when domain-specific empty
        finance_dna_judge_audit: obs.finance_dna_judge_audit || normalizeHealthDnaJudgeAudit(uniAudit),
        finance_selected_blocks: obs.finance_selected_blocks || uniBlocks,
      };
    })(),
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
      display_mode: isHealthAskRow(row, ctx, undefined) ? "health_charts" : "engine_rules",
      health_engine_execution:
        (checks.health_engine_execution as ObservabilityHealthEngineExecution | undefined) ||
        (smChecks.health_engine_execution as ObservabilityHealthEngineExecution | undefined) ||
        ((checks.d1_health_facts || smChecks.d1_health_facts)
          ? {
              schema_version: "health_engine_execution_v1",
              d1: (checks.d1_health_facts || smChecks.d1_health_facts) as ObservabilityHealthChartFacts,
              d9: (checks.d9_health_facts || smChecks.d9_health_facts || { error: "d9 missing" }) as ObservabilityHealthChartFacts,
            }
          : null),
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
    "=== 2. ENGINE EXECUTION ===",
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
  if (exec.health_engine_execution) {
    lines.push(
      "",
      "Health Engine Execution (D1 + D9):",
      JSON.stringify(exec.health_engine_execution, null, 2),
    );
  } else if (exec.relationship_engine_execution) {
    lines.push(
      "",
      "Relationship Engine Execution (D1 + D9):",
      JSON.stringify(exec.relationship_engine_execution, null, 2),
    );
  } else if (exec.finance_engine_execution) {
    lines.push(
      "",
      "Finance Engine Execution (D1 + D9):",
      JSON.stringify(exec.finance_engine_execution, null, 2),
    );
  } else if (exec.travel_engine_execution) {
    lines.push(
      "",
      "Travel Engine Execution (D1 + D9):",
      JSON.stringify(exec.travel_engine_execution, null, 2),
    );
  } else if (exec.d1_health_facts) {
    lines.push(
      "",
      "D1 Health Fact Pack:",
      JSON.stringify(exec.d1_health_facts, null, 2),
    );
  }
  lines.push("");

  lines.push("=== 3. QUESTION DNA JUDGE ===");
  const judgeCandidates = [
    obs.health_dna_judge_audit,
    obs.health_validator_audit,
    obs.relationship_dna_judge_audit,
    obs.finance_dna_judge_audit,
    obs.travel_dna_judge_audit,
  ];
  const judgeObs =
    judgeCandidates.find((a) => a?.applies) || judgeCandidates.find(Boolean);
  if (!judgeObs?.applies) {
    lines.push("— (health / relationship / finance / travel unified questions only)", "");
  } else {
    lines.push(
      `Enabled: ${judgeObs.enabled ? "yes" : "no"} | Passed: ${judgeObs.passed ? "yes" : "no"} | Source: ${judgeObs.source || "—"}`,
    );
    const contract = judgeObs.contract || {};
    if (contract.user_wants) {
      lines.push(`User wants: ${contract.user_wants}`);
    }
    if (contract.normalized_question) {
      lines.push(`Normalized Q: ${contract.normalized_question}`);
    }
    if (contract.answer_style) {
      lines.push(`Answer style: ${contract.answer_style}`);
    }
    if (contract.answer_approach) {
      lines.push(`Answer plan: ${contract.answer_approach}`);
    }
    if ((judgeObs.issues || []).length) {
      lines.push(`Issues: ${(judgeObs.issues || []).join(", ")}`);
    }
    if (judgeObs.fix_hint) {
      lines.push(`Fix hint: ${judgeObs.fix_hint}`);
    }
    lines.push("");
  }

  lines.push("=== 4. LLM SELECTED JSON BLOCKS ===");
  const blocksCandidates = [
    obs.health_selected_blocks,
    obs.relationship_selected_blocks,
    obs.finance_selected_blocks,
    obs.travel_selected_blocks,
    obs.health_dna_judge_audit?.selected_blocks,
    obs.relationship_dna_judge_audit?.selected_blocks,
    obs.finance_dna_judge_audit?.selected_blocks,
    obs.travel_dna_judge_audit?.selected_blocks,
  ];
  const blocksObs =
    blocksCandidates.find((b) => b?.applies) || blocksCandidates.find(Boolean);
  if (!blocksObs?.applies) {
    lines.push("— (health / relationship / finance / travel unified questions only)", "");
  } else {
    lines.push(`Focus: ${blocksObs.focus_label || blocksObs.focus || "—"}`);
    lines.push("Expected blocks:");
    for (const b of blocksObs.expected_blocks || []) {
      lines.push(`  • ${b.id}: ${b.label} — ${b.why || ""}`);
    }
    lines.push("Used in answer:");
    for (const b of blocksObs.used_in_answer?.blocks || []) {
      lines.push(`  • ${b.label}: ${b.detail || ""}`);
    }
    for (const note of blocksObs.overlap_notes || []) {
      lines.push(`Note: ${note}`);
    }
    lines.push("");
  }

  return lines.join("\n").trim() + "\n";
}
