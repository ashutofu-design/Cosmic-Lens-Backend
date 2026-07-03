import type { AskLlmContext, AskQuestionItem, EngineVerificationSummary } from "./api";
import { resolveEngineDisplayFromContext } from "./engineDisplay";

function fmtCheckValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "yes" : "no";
  return String(v);
}

export function resolveQuestionUnderstoodWord(
  ctx: AskLlmContext | null,
): "Yes" | "No" | null {
  if (!ctx) return null;
  const line = ctx.understanding_line?.trim();
  if (line === "Yes" || line === "No") return line;
  if (line?.startsWith("Yes ")) return "Yes";
  if (line?.startsWith("No ")) return "No";
  const qu = ctx.question_understood?.toLowerCase();
  if (qu === "yes") return "Yes";
  if (qu === "no") return "No";
  const li = ctx.llm_intent;
  if (
    li?.domain &&
    li.domain !== "general" &&
    (li.confidence ?? 0) >= 0.5
  ) {
    return "Yes";
  }
  if (ctx.skip_reason?.toLowerCase().includes("engine_required") && li?.domain) {
    return "Yes";
  }
  return null;
}

export function resolveLlmUnderstoodLine(ctx: AskLlmContext | null): string {
  if (!ctx) return "";
  const meaning = ctx.question_meaning?.trim() || ctx.llm_intent?.question_summary?.trim();
  const summary = meaning;
  const line = ctx.understanding_line?.trim();
  if (line && line.includes(" — ")) return line;
  if (summary && line) {
    const word = resolveQuestionUnderstoodWord(ctx);
    if (word) return `${word} — ${summary}`;
  }
  const word = resolveQuestionUnderstoodWord(ctx);
  const detail = ctx.understanding_detail?.trim();
  if (word && detail) return `${word} — ${detail}`;
  if (line) return line;
  if (summary) {
    const w = word || "Yes";
    return `${w} — ${summary}`;
  }
  if (word) return word;
  return "";
}

export function resolveQuestionScope(ctx: AskLlmContext | null): string {
  if (!ctx) return "";
  const direct = (ctx.question_scope || ctx.llm_intent?.question_scope || "").trim().toLowerCase();
  if (direct) return direct;
  const meaning = ctx.question_meaning?.trim() || ctx.llm_intent?.question_summary?.trim() || "";
  const m = meaning.match(/^\[([a-z][a-z0-9_]*)\]/i);
  return m ? m[1].toLowerCase() : "";
}

export function resolveQuestionMeaningText(ctx: AskLlmContext | null): string {
  if (!ctx) return "";
  const direct =
    ctx.question_meaning?.trim() ||
    ctx.llm_intent?.question_summary?.trim() ||
    ctx.llm_intent?.interpretation?.trim() ||
    "";
  if (direct) {
    return direct.replace(/^\[[a-z][a-z0-9_]*\]\s*\n?/i, "").trim() || direct;
  }

  const line = ctx.understanding_line?.trim() || "";
  const parsed = line.match(/^(?:Yes|No) — (?:\[[a-z][a-z0-9_]*\]\s*)?(.+)$/i);
  if (parsed) {
    const rest = parsed[1];
    const routeSplit = rest.split(" · ");
    return routeSplit[0].replace(/\.$/, "").trim();
  }
  return ctx.understanding_detail?.trim() || "";
}

export function resolveQuestionRoutingHint(ctx: AskLlmContext | null): string {
  if (!ctx) return "";
  const detail = ctx.understanding_detail?.trim();
  if (detail) return detail;

  const line = ctx.understanding_line?.trim() || "";
  const parsed = line.match(/^(?:Yes|No) — .+ · (.+)$/);
  if (parsed) return parsed[1].replace(/\.$/, "").trim();
  return "";
}

function clipUnderstandingText(text: string, maxChars = 1800): string {
  const t = text.trim();
  if (t.length <= maxChars) return t;
  const cut = t.slice(0, maxChars);
  const lastNl = cut.lastIndexOf("\n");
  if (lastNl > maxChars * 0.5) return `${cut.slice(0, lastNl)}…`;
  return `${cut.replace(/\s+\S*$/, "")}…`;
}

function splitScopedExplanation(text: string): { scope: string; body: string } {
  const raw = text.trim();
  const m = raw.match(/^\[([a-z][a-z0-9_]*)\]\s*\n?([\s\S]*)$/i);
  if (m) {
    return { scope: m[1].toLowerCase(), body: m[2].trim() };
  }
  return { scope: "", body: raw };
}

export function LlmQuestionUnderstandingBrief({ ctx }: { ctx: AskLlmContext | null }) {
  const scope = resolveQuestionScope(ctx);
  const rawMeaning =
    ctx?.question_meaning?.trim() ||
    ctx?.llm_intent?.question_summary?.trim() ||
    "";
  const parsed = splitScopedExplanation(
    rawMeaning || (scope ? `[${scope}]\n${resolveQuestionMeaningText(ctx)}` : resolveQuestionMeaningText(ctx)),
  );
  const displayScope = parsed.scope || scope;
  const body = clipUnderstandingText(parsed.body || resolveQuestionMeaningText(ctx));
  const routingHint = clipUnderstandingText(resolveQuestionRoutingHint(ctx));
  const understood = resolveQuestionUnderstoodWord(ctx);
  const source = (ctx?.understanding_source || ctx?.intent_source || "").trim();

  if (!body && !routingHint && !understood) {
    return (
      <span className="detail-muted">
        Not saved for this row — deploy latest API and ask again.
      </span>
    );
  }

  return (
    <div className="ask-detail-llm-understanding">
      {displayScope ? (
        <p className="ask-detail-llm-scope">
          <span className="ask-scope-inline">[{displayScope}]</span>
        </p>
      ) : null}
      {body ? <pre className="ask-detail-llm-meaning">{body}</pre> : null}
      {routingHint && routingHint !== body ? (
        <p className="ask-detail-llm-route detail-muted">{routingHint}</p>
      ) : null}
      <div className="ask-detail-understood-row">
        {understood ? (
          <span className={`ask-understood-pill ask-understood-pill--${understood.toLowerCase()}`}>
            Understood: {understood}
          </span>
        ) : null}
        {source ? (
          <span className="detail-muted ask-detail-understanding-source">
            via <code>{source}</code>
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function LlmUnderstoodOneLine({ ctx }: { ctx: AskLlmContext | null }) {
  const line = resolveLlmUnderstoodLine(ctx);
  if (!line) return null;
  const m = line.match(/^(Yes|No)( — .+)?$/);
  if (!m) {
    return (
      <>
        <strong>LLM understood:</strong> {line}
      </>
    );
  }
  return (
    <>
      <strong>LLM understood:</strong>{" "}
      <strong className={`ask-understood-word ask-understood-word--${m[1].toLowerCase()}`}>
        {m[1]}
      </strong>
      {m[2] || null}
    </>
  );
}

export function QuestionUnderstandingPanel({ ctx }: { ctx: AskLlmContext | null }) {
  if (!ctx) return null;
  const raw = (ctx.question_raw || ctx.question || "").trim();
  const norm = (ctx.question_normalized || "").trim();
  const meaning = (ctx.question_meaning || ctx.llm_intent?.question_summary || "").trim();
  const typoFixed = Boolean(
    ctx.typo_corrected && raw && norm && raw.toLowerCase() !== norm.toLowerCase(),
  );
  const source = (ctx.understanding_source || "").trim();
  const understood = resolveQuestionUnderstoodWord(ctx);

  if (!meaning && !typoFixed && !understood) return null;

  return (
    <div className="question-understanding-panel">
      {typoFixed ? (
        <p className="question-typo-row">
          <strong>Typos fixed:</strong>{" "}
          <span className="question-typo-raw">{raw}</span>
          <span className="question-typo-arrow"> → </span>
          <span className="question-typo-norm">{norm}</span>
        </p>
      ) : null}
      {meaning ? (
        <p className="question-meaning-row">
          <strong>LLM meaning:</strong> {meaning}
          {understood ? (
            <>
              {" "}
              <span
                className={`ask-understood-pill ask-understood-pill--${understood.toLowerCase()}`}
              >
                {understood}
              </span>
            </>
          ) : null}
        </p>
      ) : (
        <p>
          <LlmUnderstoodOneLine ctx={ctx} />
        </p>
      )}
      {source ? (
        <p className="detail-muted question-understanding-source">
          Understanding source: <code>{source}</code>
        </p>
      ) : null}
    </div>
  );
}

export function parseAskLlmContext(row: AskQuestionItem): AskLlmContext | null {
  if (row.llm_context && typeof row.llm_context === "object") {
    const salvaged = salvageRawLlmContext(row.llm_context as AskLlmContext);
    if (salvaged) return salvaged;
  }
  const raw = row.llm_context_json;
  if (!raw || !String(raw).trim()) return null;
  try {
    const parsed = JSON.parse(raw) as AskLlmContext;
    if (parsed && typeof parsed === "object") {
      return salvageRawLlmContext(parsed) ?? parsed;
    }
    return null;
  } catch {
    return salvageRawLlmContext({ raw: String(raw).slice(0, 8000) }) ?? {
      raw: String(raw).slice(0, 8000),
    };
  }
}

function salvageRawLlmContext(ctx: AskLlmContext): AskLlmContext | null {
  if (!ctx || typeof ctx !== "object") return null;
  const hasMeta = Boolean(
    ctx.question_meaning ||
      ctx.engine_verification_summary?.label ||
      ctx.engine_facts?.evidence?.length ||
      ctx.understanding_line ||
      ctx.slice_meta,
  );
  if (hasMeta && !ctx.raw) return ctx;

  const raw = String((ctx as { raw?: string }).raw || "").trim();
  if (!raw.startsWith("{")) return hasMeta ? ctx : null;

  const tryParse = (text: string): AskLlmContext | null => {
    try {
      const parsed = JSON.parse(text) as AskLlmContext;
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch {
      return null;
    }
  };

  const direct = tryParse(raw);
  if (direct) return direct;

  for (const suffix of ['"]}', '"}]}', '"}]}}', "}"]) {
    const parsed = tryParse(raw + suffix);
    if (parsed) return parsed;
  }
  return hasMeta ? ctx : null;
}

export type AnswerPathCode = "engine_then_llm" | "engine_only" | "direct_llm" | "unknown";

export function resolveEngineVerificationSummary(
  ctx: AskLlmContext | null,
): EngineVerificationSummary | null {
  if (!ctx) return null;
  const direct = ctx.engine_verification_summary;
  if (direct && typeof direct === "object" && direct.label) {
    return direct;
  }
  const display = ctx.engine_display;
  if (display?.admin_line) {
    return {
      status: "correct",
      label: "Correct engine",
      reason: "output_ok",
      engine_no: display.engine_no ?? null,
      engine_slice: (display.slice_id as string) || null,
      ran_archetype: (display.archetype as string) || null,
      engine_admin_line: display.admin_line,
      recovered: false,
    };
  }
  const slice = String(ctx.slice_meta?.slice || ctx.checks?.slice_type || "");
  if (slice.includes("marriage_timing") || slice === "timing_marriage_engine") {
    const disp = resolveEngineDisplayFromContext(ctx);
    if (disp.adminLine !== "—") {
      return {
        status: "correct",
        label: "Correct engine",
        reason: "output_ok",
        engine_no: disp.engineNo,
        engine_slice: disp.sliceId,
        ran_archetype: disp.archetype,
        engine_admin_line: disp.adminLine,
        recovered: false,
      };
    }
  }
  return null;
}

export function EngineVerificationBadge({
  summary,
}: {
  summary: EngineVerificationSummary | null;
}) {
  if (!summary) {
    return <span className="engine-verify-badge engine-verify-unknown">Unknown</span>;
  }
  if (summary.status === "none") {
    return (
      <span
        className="engine-verify-badge engine-verify-none"
        title={summary.reason || undefined}
      >
        {summary.label}
      </span>
    );
  }
  return (
    <span
      className={`engine-verify-badge engine-verify-${summary.status}`}
      title={summary.reason || undefined}
    >
      {summary.label}
    </span>
  );
}

export function EngineVerificationPanel({
  ctx,
  defaultOpen,
  id,
}: {
  ctx: AskLlmContext | null;
  defaultOpen?: boolean;
  id?: string;
}) {
  const summary = resolveEngineVerificationSummary(ctx);
  const sliceMeta = (ctx?.slice_meta || {}) as Record<string, unknown>;
  const archetype =
    summary?.ran_archetype ||
    (ctx?.engine_facts?.archetype as string | undefined) ||
    (sliceMeta.archetype as string | undefined);

  return (
    <details
      id={id}
      className="engine-verify-panel"
      open={defaultOpen || undefined}
    >
      <summary>
        Engine verification
        {summary ? (
          <>
            {" — "}
            <EngineVerificationBadge summary={summary} />
          </>
        ) : null}
      </summary>
      {!summary ? (
        <p className="detail-muted">
          No verification snapshot — deploy latest API and ask a new question.
        </p>
      ) : summary.status === "none" ? (
        <p className="detail-muted">
          Direct LLM only — no domain engine ran for this question.
        </p>
      ) : (
        <div className="engine-verify-body">
          <p>
            <strong>Status:</strong>{" "}
            <EngineVerificationBadge summary={summary} />
          </p>
          <p>
            <strong>Reason:</strong> {summary.reason}
          </p>
          {summary.selected_engine ? (
            <p>
              <strong>Engine ran:</strong>{" "}
              <code>
                {summary.engine_admin_line ||
                  (summary.engine_no != null ? `Engine #${summary.engine_no}` : summary.selected_engine)}
              </code>
            </p>
          ) : null}
          {archetype ? (
            <p>
              <strong>Archetype:</strong> <code>{archetype}</code>
            </p>
          ) : null}
          {summary.recovered ? (
            <p className="engine-verify-recovered-note">
              System detected a wrong first pick and rerouted before answering.
            </p>
          ) : null}
        </div>
      )}
    </details>
  );
}

export function resolveAnswerPath(
  ctx: AskLlmContext | null,
  row?: Pick<AskQuestionItem, "answer_source" | "engine_tag" | "total_tokens">,
): { code: AnswerPathCode; label: string } {
  if (ctx?.answer_path && ctx?.answer_path_label) {
    return {
      code: ctx.answer_path as AnswerPathCode,
      label: String(ctx.answer_path_label),
    };
  }

  const src = (row?.answer_source || "").toLowerCase();
  if (src === "direct_llm_no_engine" || src.includes("direct_llm")) {
    return { code: "direct_llm", label: "Direct LLM (no engine)" };
  }
  if (src === "mr_engine_template" || src.includes("deterministic")) {
    return { code: "engine_only", label: "Engine only (no LLM)" };
  }
  if (src === "mr_engine_then_llm" || row?.engine_tag === "ans-engine") {
    return { code: "engine_then_llm", label: "Engine → LLM" };
  }
  if (ctx?.llm_called === false) {
    return { code: "engine_only", label: "Engine only (no LLM)" };
  }
  if (row?.total_tokens != null && row.total_tokens > 0) {
    const hasFacts = Boolean(
      ctx?.engine_facts?.verdict ||
        (ctx?.engine_facts?.evidence && ctx.engine_facts.evidence.length > 0) ||
        ctx?.slice_meta?.verdict ||
        (ctx?.slice_meta?.evidence && ctx.slice_meta.evidence.length > 0),
    );
    if (hasFacts) {
      return { code: "engine_then_llm", label: "Engine → LLM" };
    }
    return { code: "direct_llm", label: "Direct LLM (no engine facts)" };
  }
  return { code: "unknown", label: "Unknown path" };
}

function engineFactsFromContext(ctx: AskLlmContext) {
  const ef = ctx.engine_facts;
  const sm = ctx.slice_meta || {};
  const smTiming = (sm.timing_evidence as string[] | undefined) || [];
  const efTiming = (ef as { timing_evidence?: string[] } | undefined)?.timing_evidence || [];
  const mergedEvidence =
    (ef?.evidence && ef.evidence.length > 0
      ? ef.evidence
      : (sm.evidence as string[] | undefined)) ||
    (efTiming.length > 0 ? efTiming : smTiming.length > 0 ? smTiming : []);
  const hasFacts = Boolean(
    ef?.verdict ||
      sm.verdict ||
      mergedEvidence.length > 0 ||
      (ef?.summary && ef.summary.length > 0) ||
      ((sm.summary as string[] | undefined)?.length ?? 0) > 0,
  );
  if (ef && hasFacts) {
    return {
      ...ef,
      evidence: mergedEvidence,
      timing_evidence: efTiming.length > 0 ? efTiming : smTiming,
      step_audit: (ef as { step_audit?: unknown }).step_audit || sm.step_audit,
      timing_audit: (ef as { timing_audit?: unknown }).timing_audit || sm.timing_audit,
      calculation_steps:
        (ef as { calculation_steps?: string[] }).calculation_steps ||
        (sm.calculation_steps as string[] | undefined),
      evidence_positive:
        ef.evidence_positive && ef.evidence_positive.length > 0
          ? ef.evidence_positive
          : (sm.evidence_positive as string[] | undefined) || ef.evidence_positive || [],
      evidence_negative:
        ef.evidence_negative && ef.evidence_negative.length > 0
          ? ef.evidence_negative
          : (sm.evidence_negative as string[] | undefined) || ef.evidence_negative || [],
      evidence_neutral:
        ef.evidence_neutral && ef.evidence_neutral.length > 0
          ? ef.evidence_neutral
          : (sm.evidence_neutral as string[] | undefined) || ef.evidence_neutral || [],
    };
  }
  return {
    archetype: sm.archetype,
    verdict: sm.verdict,
    summary: (sm.summary as string[] | undefined) || [],
    evidence: mergedEvidence,
    timing_evidence: smTiming,
    step_audit: sm.step_audit,
    timing_audit: sm.timing_audit,
    calculation_steps: sm.calculation_steps as string[] | undefined,
    evidence_positive: (sm.evidence_positive as string[] | undefined) || [],
    evidence_negative: (sm.evidence_negative as string[] | undefined) || [],
    evidence_neutral: (sm.evidence_neutral as string[] | undefined) || [],
    ignore: (sm.ignore as string[] | undefined) || [],
    love_score: undefined,
    arrange_score: undefined,
    verdict_public: undefined,
    confidence_ratio: undefined,
  };
}

type EngineTrace = {
  engine?: string;
  pipeline_version?: string;
  primary_window?: string;
  running_dasha_window?: string;
  running_dasha?: {
    md?: string;
    ad?: string;
    pd?: string;
    lords?: string;
    start?: string;
    end?: string;
  };
  backup_window?: string;
  key_trigger?: string;
  verdict?: string;
  band?: string;
  user_age?: number | string;
  step_audit?: Record<string, Record<string, unknown>>;
  step_order?: string[];
  timing_audit?: {
    status?: string;
    issues?: string[];
    expected_reply?: string;
    primary_window?: string;
    checks?: { name?: string; ok?: boolean; detail?: string }[];
    primary_dasha?: Record<string, unknown>;
    running_dasha?: Record<string, unknown>;
    bcp?: Record<string, unknown>;
    transit?: Record<string, unknown>;
  };
  top_3_windows?: Record<string, unknown>[];
  factors?: string[];
  risk_flags?: string[];
};

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === "object" && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : null;
}

function formatStep7TransitDetail(step: Record<string, unknown>): string {
  const typeLabel =
    typeof step.transit_type_label === "string" ? step.transit_type_label : "";
  const byMonth = Array.isArray(step.by_month) ? step.by_month : [];
  let body = "";
  if (byMonth.length > 0) {
    body = byMonth
      .map((row) => {
        const r = asRecord(row);
        if (!r) return "";
        const month = String(r.month || "");
        const lineBits: string[] = [];
        for (const [planet, label] of [
          ["jupiter", "Guru"],
          ["saturn", "Shani"],
        ] as const) {
          const rashi = String(r[`${planet}_rashi`] || "");
          if (!rashi) continue;
          const active = Boolean(r[`${planet}_active`]);
          const act = String(r[`${planet}_activation`] || "7H/7L par nahi");
          lineBits.push(`${label} ${rashi} (${active ? act : "7H/7L par nahi"})`);
        }
        return lineBits.length ? `${month}: ${lineBits.join(" · ")}` : month;
      })
      .filter(Boolean)
      .join(" · ");
  } else {
    body = typeof step.detail === "string" ? step.detail : "";
  }
  if (typeLabel) {
    return body ? `${body} | ${typeLabel}` : typeLabel;
  }
  return body;
}

function stepOneLiner(
  stepKey: string,
  step: Record<string, unknown>,
  engine?: string,
): string {
  const name = String(step.name || stepKey);
  if (engine === "career_timing_v1" && typeof step.detail === "string" && step.detail) {
    return `${name} · ${step.detail}`;
  }
  if (engine?.endsWith("_timing_v1") && typeof step.detail === "string" && step.detail) {
    return `${name} · ${step.detail}`;
  }
  if (stepKey === "step1" && (step.current_end || step.current_start)) {
    const lords = step.current_lords ? String(step.current_lords) : "—";
    const end = step.current_end ? String(step.current_end) : "?";
    return `${name} · MD/AD/PD ${lords} · kab tak ${end}`;
  }
  if (stepKey === "step2") {
    return `${name} · ${fmtCheckValue(step.detail)} · ${step.status || "—"}`;
  }
  if (stepKey === "step4") {
    return `${name} · ${fmtCheckValue(step.detail)}`;
  }
  if (stepKey === "step0") {
    const r = asRecord(step.result);
    const verdict = r?.verdict ? String(r.verdict) : "";
    const age = step.user_age != null ? `age ${step.user_age}` : "";
    return [name, verdict, age].filter(Boolean).join(" · ");
  }
  if (stepKey === "step0a") {
    const focus = Array.isArray(step.focus_ages) ? step.focus_ages.join(", ") : "";
    return `${name} · primary ref age ${fmtCheckValue(step.primary_reference_age)}${focus ? ` · focus ${focus}` : ""}`;
  }
  if (stepKey === "step1" || stepKey === "step2") {
    const r = asRecord(step.result);
    const disp = fmtCheckValue(r?.lords_of_planets_in_7th_house);
    return `${name} · 7L ${fmtCheckValue(r?.seventh_lord)} · in 7H ${fmtCheckValue(r?.planets_in_7th_house)} · 7H swami ${disp}`;
  }
  if (stepKey === "step3") {
    return `${name} · D1/D9 7H planets + aspect (see lines below)`;
  }
  if (stepKey === "step4") {
    return `${name} · common planets (see line below)`;
  }
  if (stepKey === "step5") {
    return `${name} · weighted rank (see lines below)`;
  }
  if (stepKey === "step6") {
    const matched = Array.isArray(step.selected_windows) ? step.selected_windows.length : 0;
    const cand = Array.isArray(step.candidate_windows) ? step.candidate_windows.length : 0;
    const suffix =
      matched > 0
        ? `${matched} transit-matched final`
        : cand > 0
          ? `${cand} dasha, 0 transit match`
          : "see lines below";
    return `${name} · ${suffix}`;
  }
  if (stepKey === "step7") {
    const cc = asRecord(step.chart_context);
    const chartHint = cc
      ? `Lagna ${cc.lagna || "?"} · 7H ${cc.seventh_house || "?"} · 7L ${cc.seventh_lord || "?"} (${cc.seventh_lord_sign || "?"})`
      : "";
    const detail = formatStep7TransitDetail(step);
    const parts = [name, `transit ${step.transit_confirmed ? "confirmed" : "not confirmed"}`];
    if (chartHint) parts.push(chartHint);
    if (detail) parts.push(detail);
    return parts.join(" · ");
  }
  if (stepKey === "step8") {
    return `${name} · ${fmtCheckValue(step.verdict)} · band ${fmtCheckValue(step.band)}`;
  }
  return name;
}

function marriageAuditStepTitle(key: string, step?: Record<string, unknown>): string {
  const labels: Record<string, string> = {
    step3: "Step 3 — D1+D9 7H linkage",
    step4: "Step 4 — Common planets (D1+D9)",
    step5: "Step 5 — Rank significators (weighted points)",
    step6: "Step 6 — Final dasha (Guru/Shani match)",
    step7: "Step 7 — Guru/Shani transit on 7H/7L",
    step8: "Step 8 — Final gate",
  };
  return labels[key] || String(step?.name || key);
}

function fmtPlanetNameList(val: unknown): string {
  if (!Array.isArray(val) || val.length === 0) return "nil";
  return val.map((x) => String(x)).join(", ");
}

function fmtLordName(val: unknown): string {
  if (val == null || val === "") return "nil";
  return String(val);
}

/** Step 3 — one line per D1/D9 7H + 7L rule. */
function formatMarriageStep37HLinkage(
  stepAudit: Record<string, Record<string, unknown>>,
): string[] {
  const d1 = asRecord(stepAudit.step1?.result);
  const d9 = asRecord(stepAudit.step2?.result);
  if (!d1 && !d9 && !stepAudit.step3) {
    return [
      "— (trace save nahi hua — NAYA marriage timing question puchein.)",
    ];
  }
  return [
    `D1 7H planets: ${fmtPlanetNameList(d1?.planets_in_7th_house)}`,
    `D1 7H aspect: ${fmtPlanetNameList(d1?.planets_aspecting_7th_house)}`,
    `D1 7L: ${fmtLordName(d1?.seventh_lord)}`,
    `D1 with 7L: ${fmtPlanetNameList(d1?.planets_conjunct_or_aspecting_7th_lord)}`,
    `D9 7H planets: ${fmtPlanetNameList(d9?.planets_in_7th_house)}`,
    `D9 7H aspect: ${fmtPlanetNameList(d9?.planets_aspecting_7th_house)}`,
    `D9 7L: ${fmtLordName(d9?.seventh_lord)}`,
    `D9 with 7L: ${fmtPlanetNameList(d9?.planets_conjunct_or_aspecting_7th_lord)}`,
  ];
}

function formatMarriageStep3Planets(
  stepAudit: Record<string, Record<string, unknown>>,
  step3?: Record<string, unknown>,
): string {
  void step3;
  return formatMarriageStep37HLinkage(stepAudit).join("\n");
}

function getCommonMarriagePlanets(
  stepAudit: Record<string, Record<string, unknown>>,
): string[] {
  const s4 = stepAudit.step4;
  if (Array.isArray(s4?.common_planets) && s4.common_planets.length) {
    return s4.common_planets.map((x) => String(x));
  }
  const s3 = stepAudit.step3;
  if (Array.isArray(s3?.common_planets) && s3.common_planets.length) {
    return s3.common_planets.map((x) => String(x));
  }
  const top = s3?.top_merged;
  if (Array.isArray(top)) {
    const fromBoth = top
      .map((row) => asRecord(row))
      .filter((r) => r?.both_divisions && r?.name)
      .map((r) => String(r!.name));
    if (fromBoth.length) return fromBoth;
  }
  const mgp = s3?.marriage_giving_planets;
  if (Array.isArray(mgp)) {
    return mgp
      .map((row) => asRecord(row))
      .filter((r) => {
        const d1 = Array.isArray(r?.d1_links) && r!.d1_links!.length > 0;
        const d9 = Array.isArray(r?.d9_links) && r!.d9_links!.length > 0;
        return d1 && d9 && r?.name;
      })
      .map((r) => String(r!.name));
  }
  return [];
}

function formatMarriageStep4CommonPlanets(
  stepAudit: Record<string, Record<string, unknown>>,
): string {
  const names = getCommonMarriagePlanets(stepAudit);
  return `Common planets: ${names.length ? names.join(", ") : "nil"}`;
}

function getRankedMarriageSignificators(
  stepAudit: Record<string, Record<string, unknown>>,
): Record<string, unknown>[] {
  const s5 = stepAudit.step5;
  if (Array.isArray(s5?.ranked_top) && s5.ranked_top.length) {
    return s5.ranked_top.map((r) => asRecord(r) || {});
  }
  const top = stepAudit.step3?.top_merged;
  if (Array.isArray(top) && top.length) {
    return [...top]
      .map((r) => asRecord(r) || {})
      .sort(
        (a, b) =>
          Number(b.natal_points ?? b.score ?? 0) - Number(a.natal_points ?? a.score ?? 0),
      );
  }
  return [];
}

function formatMarriageStep5RankedLines(
  stepAudit: Record<string, Record<string, unknown>>,
): string[] {
  const ranked = getRankedMarriageSignificators(stepAudit);
  if (!ranked.length) {
    return ["— (not saved)"];
  }
  return ranked.map((row, idx) => {
    const name = String(row.name || "?");
    const score = row.score ?? row.natal_points ?? "—";
    const d1 = row.d1_points ?? row.d1 ?? 0;
    const d9 = row.d9_points ?? row.d9 ?? 0;
    const both =
      row.both_bonus != null && Number(row.both_bonus) > 0
        ? ` +both ${row.both_bonus}`
        : "";
    const kp =
      row.kp_points != null && Number(row.kp_points) > 0
        ? ` +KP ${row.kp_points}`
        : "";
    const links = Array.isArray(row.links)
      ? row.links.map(String).join(", ")
      : [
          ...(Array.isArray(row.d1_links) ? row.d1_links.map(String) : []),
          ...(Array.isArray(row.d9_links) ? row.d9_links.map(String) : []),
        ].join(", ");
    return `${idx + 1}. ${name}: score ${score} (D1=${d1} D9=${d9}${both}${kp}) · ${links || "—"}`;
  });
}

function formatMarriageStep5Ranked(
  stepAudit: Record<string, Record<string, unknown>>,
): string {
  return formatMarriageStep5RankedLines(stepAudit).join("\n");
}

function getMarriageDashaWindows(
  stepAudit: Record<string, Record<string, unknown>>,
  trace?: EngineTrace,
): Record<string, unknown>[] {
  const s6 = stepAudit.step6;
  if (Array.isArray(s6?.selected_windows) && s6.selected_windows.length) {
    return s6.selected_windows
      .map((w) => asRecord(w))
      .filter((r): r is Record<string, unknown> => Boolean(r));
  }
  if (Array.isArray(trace?.top_3_windows) && trace.top_3_windows.length) {
    return trace.top_3_windows
      .map((w) => asRecord(w))
      .filter((r): r is Record<string, unknown> => Boolean(r));
  }
  return [];
}

function formatMarriageStep6Period(row: Record<string, unknown>): string {
  const window = row.window ? String(row.window) : "";
  if (window) return window;
  const start = row.start_iso ? String(row.start_iso) : "";
  const end = row.end_iso ? String(row.end_iso) : "";
  if (start && end) return `${start} → ${end}`;
  return "—";
}

function formatMarriageStep6DashaLord(row: Record<string, unknown>): string {
  const md = row.md ? String(row.md) : "";
  const ad = row.ad ? String(row.ad) : "";
  const pd = row.pd ? String(row.pd) : "";
  if (row.pd_only_activation && pd) {
    return `PD ${pd}`;
  }
  if (ad && pd) {
    return `AD ${ad} · PD ${pd}`;
  }
  if (ad) {
    return `AD ${ad}`;
  }
  if (pd) {
    return `PD ${pd}`;
  }
  if (md) {
    return `MD ${md}`;
  }
  return "—";
}

function formatMarriageStep6TransitSuffix(row: Record<string, unknown>): string {
  if (!row.transit_confirmed) return "";
  const bits: string[] = [];
  if (row.jup) bits.push("Guru ✓");
  if (row.sat) bits.push("Shani ✓");
  if (row.dt) bits.push("double transit");
  const detail = row.dt_detail ? String(row.dt_detail) : "";
  const transit = bits.length ? bits.join(" · ") : "transit ✓";
  return detail ? ` · ${transit} · ${detail}` : ` · ${transit}`;
}

function formatMarriageStep6DashaLines(
  stepAudit: Record<string, Record<string, unknown>>,
  trace?: EngineTrace,
): string[] {
  const windows = getMarriageDashaWindows(stepAudit, trace);
  if (!windows.length) {
    const s6 = stepAudit.step6;
    const cands = Array.isArray(s6?.candidate_windows) ? s6.candidate_windows.length : 0;
    if (cands > 0) {
      return [
        `— (top ${cands} dasha mila, par kisi par Guru/Shani 7H/7L transit match nahi)`,
      ];
    }
    return ["— (dasha period save nahi hua — chart me dasha chain chahiye)"];
  }
  return windows.slice(0, 3).map((row, idx) => {
    const lords = formatMarriageStep6DashaLord(row);
    const period = formatMarriageStep6Period(row);
    const transit = formatMarriageStep6TransitSuffix(row);
    return `${idx + 1}. ${lords} → ${period}${transit}`;
  });
}

function formatMarriageStep7PerDashaLines(
  stepAudit: Record<string, Record<string, unknown>>,
): string[] {
  const s7 = stepAudit.step7;
  const perDasha = Array.isArray(s7?.per_dasha_windows) ? s7.per_dasha_windows : [];
  if (perDasha.length) {
    return perDasha.map((raw, idx) => {
      const row = asRecord(raw);
      if (!row) return "";
      const lords = formatMarriageStep6DashaLord(row);
      const period = formatMarriageStep6Period(row);
      const detail = formatStep7TransitDetail(row);
      return `${idx + 1}. ${lords} → ${period} · ${detail}`;
    }).filter(Boolean);
  }
  const detail = s7 ? formatStep7TransitDetail(s7) : "";
  if (detail) return [detail];
  if (s7?.status === "NO_TRANSIT_MATCH") {
    return ["— (koi dasha par Guru/Shani 7H/7L transit match nahi)"];
  }
  return ["— (transit verify pending)"];
}

function formatMarriageStep6Dasha(
  stepAudit: Record<string, Record<string, unknown>>,
  trace?: EngineTrace,
): string {
  return formatMarriageStep6DashaLines(stepAudit, trace).join("\n");
}

function MarriageStep7TransitLines({
  stepAudit,
}: {
  stepAudit: Record<string, Record<string, unknown>>;
}) {
  const lines = formatMarriageStep7PerDashaLines(stepAudit);
  const cc = asRecord(stepAudit.step7?.chart_context);
  const chartHint = cc
    ? `Lagna ${cc.lagna || "?"} · 7H ${cc.seventh_house || "?"} · 7L ${cc.seventh_lord || "?"} (${cc.seventh_lord_sign || "?"})`
    : "";
  return (
    <>
      {chartHint ? (
        <p className="detail-muted engine-marriage-step7-chart">{chartHint}</p>
      ) : null}
      <ul className="llm-check-list engine-marriage-step7-transit">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </>
  );
}

function MarriageStep6DashaLines({
  stepAudit,
  trace,
}: {
  stepAudit: Record<string, Record<string, unknown>>;
  trace?: EngineTrace;
}) {
  const lines = formatMarriageStep6DashaLines(stepAudit, trace);
  return (
    <ul className="llm-check-list engine-marriage-step6-dasha">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}

function MarriageStep5RankedLines({
  stepAudit,
}: {
  stepAudit: Record<string, Record<string, unknown>>;
}) {
  const lines = formatMarriageStep5RankedLines(stepAudit);
  const weightNote = String(stepAudit.step5?.weight_note || "").trim();
  return (
    <>
      <ul className="llm-check-list engine-marriage-step5-ranked">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {weightNote ? (
        <p className="detail-muted engine-marriage-step5-weights">{weightNote}</p>
      ) : null}
    </>
  );
}

function MarriageStep3LinkageLines({
  stepAudit,
}: {
  stepAudit: Record<string, Record<string, unknown>>;
}) {
  const lines = formatMarriageStep37HLinkage(stepAudit);
  return (
    <ul className="llm-check-list engine-marriage-step3-linkage">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}

function stepAuditFromMarriageContext(
  ctx: AskLlmContext,
  trace?: EngineTrace,
  sliceMeta?: Record<string, unknown>,
  engineFacts?: Record<string, unknown>,
): Record<string, Record<string, unknown>> {
  const blocks = (ctx.blocks || {}) as Record<string, unknown>;
  const blockTrace = blocks.engine_trace as { step_audit?: Record<string, Record<string, unknown>> } | undefined;
  const merged: Record<string, Record<string, unknown>> = {};
  const sources = [
    blockTrace?.step_audit,
    trace?.step_audit,
    sliceMeta?.step_audit as Record<string, Record<string, unknown>> | undefined,
    engineFacts?.step_audit as Record<string, Record<string, unknown>> | undefined,
  ];
  for (const src of sources) {
    if (!src || typeof src !== "object") continue;
    for (const [key, val] of Object.entries(src)) {
      if (!val || typeof val !== "object") continue;
      const row = val as Record<string, unknown>;
      if (Object.keys(row).length === 0) continue;
      merged[key] = { ...(merged[key] || {}), ...row };
    }
  }
  return merged;
}

function isDashaFirstTimingEngine(engineId: string): boolean {
  return (
    engineId.endsWith("_timing_v1") &&
    engineId !== "marriage_timing_m17" &&
    engineId !== "marriage_timing_v1"
  );
}

function isNewDashaStep1(step: Record<string, unknown> | undefined): boolean {
  if (!step) return false;
  const name = String(step.name || "");
  return (
    name.includes("Active dasha") ||
    Boolean(step.current_end || step.current_lords || (step.md && step.ad))
  );
}

function formatRunningDashaDetail(
  trace: EngineTrace | undefined,
  stepAudit: Record<string, Record<string, unknown>>,
  timingAudit: EngineTrace["timing_audit"],
): string {
  const rd = trace?.running_dasha;
  if (rd?.lords || rd?.end || rd?.md) {
    const md = rd.md || "?";
    const ad = rd.ad || "?";
    const pd = rd.pd || "?";
    const lords = rd.lords || `${md}/${ad}/${pd}`;
    const parts = [`MD ${md} · AD ${ad} · PD ${pd}`, `lords ${lords}`];
    if (rd.start && rd.end) parts.push(`${rd.start} → ${rd.end}`);
    if (rd.end) parts.push(`kab tak ${rd.end}`);
    return parts.join(" · ");
  }

  const s1 = stepAudit.step1;
  if (isNewDashaStep1(s1)) {
    const md = fmtCheckValue(s1.md);
    const ad = fmtCheckValue(s1.ad);
    const pd = fmtCheckValue(s1.pd);
    const lords = s1.current_lords ? String(s1.current_lords) : `${md}/${ad}/${pd}`;
    const parts = [`MD ${md} · AD ${ad} · PD ${pd}`, `lords ${lords}`];
    if (s1.current_start && s1.current_end) {
      parts.push(`${s1.current_start} → ${s1.current_end}`);
    }
    if (s1.current_end) parts.push(`kab tak ${s1.current_end}`);
    return parts.join(" · ");
  }

  if (trace?.running_dasha_window) return trace.running_dasha_window;

  const ta = timingAudit?.running_dasha;
  if (ta?.lords || ta?.end) {
    const parts = [`lords ${fmtCheckValue(ta.lords)}`];
    if (ta.start && ta.end) parts.push(`${fmtCheckValue(ta.start)} → ${fmtCheckValue(ta.end)}`);
    if (ta.end) parts.push(`kab tak ${fmtCheckValue(ta.end)}`);
    return parts.join(" · ");
  }

  return "— (re-ask question after API deploy for running dasha)";
}

function JsonDetail({ data, label }: { data: unknown; label?: string }) {
  if (data == null) return null;
  return (
    <details className="engine-step-detail">
      <summary>{label || "Full step data"}</summary>
      <pre className="llm-context-pre">{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}

function summaryWindowFromMeta(
  sliceMeta: Record<string, unknown>,
  engineFacts: ReturnType<typeof engineFactsFromContext>,
): string | undefined {
  const summaries = (engineFacts.summary?.length ? engineFacts.summary : sliceMeta.summary) as
    | string[]
    | undefined;
  if (summaries?.length) {
    const first = String(summaries[0]);
    if (first.includes("Marriage timing:")) {
      return first.split("Marriage timing:")[1]?.trim();
    }
    return first.trim();
  }
  for (const line of engineFacts.evidence || []) {
    const ls = String(line);
    if (/^primary window:/i.test(ls)) return ls.split(":").slice(1).join(":").trim();
    if (/^answer window:/i.test(ls)) return ls.split(":").slice(1).join(":").trim();
  }
  return undefined;
}

function isMarriageM17Trace(engineId: string, ctx: AskLlmContext): boolean {
  const checks = (ctx.checks || {}) as Record<string, unknown>;
  const slice = String(ctx.slice_meta?.slice || checks.slice_type || "");
  return (
    engineId === "marriage_timing_m17" ||
    slice === "marriage_timing_m17" ||
    checks.slice_type === "timing_marriage_engine"
  );
}

function formatMarriageEarlyLateStep(step0?: Record<string, unknown>): {
  title: string;
  detail: string;
} {
  if (!step0) {
    return {
      title: "Step 1 — Early / Late marriage",
      detail:
        "— (trace save nahi hua — admin question dubara kholein ya naya marriage timing question puchein. Primary profile chart ho to bhi purane row me blank reh sakta hai jab tak API deploy + restart na ho.)",
    };
  }
  const r = asRecord(step0.result);
  const verdict = String(r?.verdict || "").trim();
  const combined = String(r?.combined_pace || r?.combined || "").trim();
  const d1 = String(r?.d1_pace || "").trim();
  const d9 = String(r?.d9_pace || "").trim();
  const age = step0.user_age != null ? ` · user age ${step0.user_age}` : "";

  const v = verdict.toUpperCase();
  const paceBlob = `${combined} ${d1} ${d9}`.toUpperCase();
  let label = "On-time marriage chart";
  if (v === "DELAYED" || v === "LATE" || paceBlob.includes("LATE") || paceBlob.includes("VERY_LATE")) {
    label = "Late marriage chart";
  } else if (v === "EARLY" || paceBlob.includes("EARLY")) {
    label = "Early marriage chart";
  }

  const parts = [label];
  if (verdict) parts.push(verdict);
  if (d1 || d9) parts.push(`D1 ${d1 || "—"} · D9 ${d9 || "—"}`);
  return {
    title: "Step 1 — Early / Late marriage",
    detail: parts.filter(Boolean).join(" · ") + age,
  };
}

function marriageStep0FromContext(
  ctx: AskLlmContext,
  stepAudit: Record<string, Record<string, unknown>>,
): Record<string, unknown> | undefined {
  if (stepAudit.step0) return stepAudit.step0;
  const sm = (ctx.slice_meta || {}) as Record<string, unknown>;
  const ef = ctx.engine_facts as { step_audit?: Record<string, Record<string, unknown>> } | undefined;
  return sm.step_audit
    ? (sm.step_audit as Record<string, Record<string, unknown>>).step0
    : ef?.step_audit?.step0;
}

function marriageStep0aFromContext(
  stepAudit: Record<string, Record<string, unknown>>,
  sliceMeta?: Record<string, unknown>,
  evidence?: string[],
): Record<string, unknown> {
  const linkage = (sliceMeta?.bcp_linkage || {}) as Record<string, unknown>;
  const base = { ...(stepAudit.step0a || {}), ...linkage };
  const parsed = parseBcpLinkageFromEvidence(evidence);
  const merged = mergeBcpLinkage(base, parsed);
  if (linkage.bcp_house_display && !merged.bcp_house_display) {
    merged.bcp_house_display = linkage.bcp_house_display;
  }
  return merged;
}

function mergeBcpLinkage(
  ...sources: Array<Record<string, unknown> | undefined>
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const src of sources) {
    if (!src || typeof src !== "object") continue;
    for (const [key, val] of Object.entries(src)) {
      if (val == null) continue;
      if (Array.isArray(val) && val.length === 0 && out[key]) continue;
      if (out[key] == null || out[key] === "" || (Array.isArray(out[key]) && !(out[key] as unknown[]).length)) {
        out[key] = val;
      }
    }
  }
  return out;
}

function parseBcpLinkageFromEvidence(evidence?: string[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  if (!evidence?.length) return out;
  for (const line of evidence) {
    const s = String(line);
    let m = s.match(/BCP_LINKAGE\s+D1\s+7L=(\w+)\s+placement=(\d+)\s+aspects=([\d,]*)/i);
    if (m) {
      out.d1_seventh_lord = m[1];
      out.d1_7l_placement_house = parseInt(m[2], 10);
      out.d1_7l_aspect_houses = m[3]
        ? m[3].split(",").map((x) => parseInt(x.trim(), 10)).filter((n) => !isNaN(n))
        : [];
      continue;
    }
    m = s.match(/BCP_LINKAGE\s+D9\s+7L=(\w+)\s+placement=(\d+)\s+aspects=([\d,]*)/i);
    if (m) {
      out.d9_seventh_lord = m[1];
      out.d9_7l_placement_house = parseInt(m[2], 10);
      out.d9_7l_aspect_houses = m[3]
        ? m[3].split(",").map((x) => parseInt(x.trim(), 10)).filter((n) => !isNaN(n))
        : [];
      continue;
    }
    m = s.match(/BCP-D1:\s+7L\s+(\w+)@(\d+)H/i);
    if (m) {
      if (!out.d1_seventh_lord) out.d1_seventh_lord = m[1];
      if (!out.d1_7l_placement_house) out.d1_7l_placement_house = parseInt(m[2], 10);
    }
    m = s.match(/BCP-D9:\s+7L\s+(\w+)@(\d+)H/i);
    if (m) {
      if (!out.d9_seventh_lord) out.d9_seventh_lord = m[1];
      if (!out.d9_7l_placement_house) out.d9_7l_placement_house = parseInt(m[2], 10);
    }
    m = s.match(/D1\s+7L=([A-Za-z]+)/);
    if (m && !out.d1_seventh_lord) out.d1_seventh_lord = m[1];
    m = s.match(/D9\s+7L=([A-Za-z]+)/);
    if (m && !out.d9_seventh_lord) out.d9_seventh_lord = m[1];
    m = s.match(/BCP_SHARED_HOUSES\s+([\d,]+)/i);
    if (m) {
      out.shared_7l_linkage_houses = m[1]
        .split(",")
        .map((x) => parseInt(x.trim(), 10))
        .filter((n) => !isNaN(n));
    }
    m = s.match(/BCP_HOUSE\s+(D1|D9)\s+(placement|aspect)=(\d+)\s+ages=([\d,]*)/i);
    if (m) {
      const div = m[1].toUpperCase();
      const kind = m[2].toLowerCase();
      const house = parseInt(m[3], 10);
      const ages = m[4]
        ? m[4].split(",").map((x) => parseInt(x.trim(), 10)).filter((n) => !isNaN(n))
        : [];
      const key = div === "D1" ? "d1" : "d9";
      if (kind === "placement") {
        out[`${key}_7l_placement_house`] = house;
      } else {
        const aspKey = `${key}_7l_aspect_houses`;
        const cur = (out[aspKey] as number[]) || [];
        if (!cur.includes(house)) cur.push(house);
        out[aspKey] = cur.sort((a, b) => a - b);
      }
      if (!out.bcp_house_display) out.bcp_house_display = { d1: { items: [] }, d9: { items: [] } };
      const disp = out.bcp_house_display as { d1?: BcpDivDisplay; d9?: BcpDivDisplay };
      const bucket = div === "D1" ? disp.d1 : disp.d9;
      if (bucket) {
        bucket.items = bucket.items || [];
        bucket.items.push({ type: kind, house, ages });
      }
    }
  }
  return out;
}

function parseUserAgeFromEvidence(evidence?: string[]): number | null {
  if (!evidence?.length) return null;
  for (const line of evidence) {
    const m =
      line.match(/user_age=(\d+)/i) ||
      line.match(/User age (\d+)/i) ||
      line.match(/age=(\d+)/i);
    if (m) {
      const n = parseInt(m[1], 10);
      if (!isNaN(n)) return n;
    }
  }
  return null;
}

function parseBcpAgesFromEvidence(evidence?: string[]): number[] {
  if (!evidence?.length) return [];
  const ages: number[] = [];
  for (const line of evidence) {
    const patterns = [
      /focus\s*\[([^\]]+)\]/i,
      /bcp_5y=\[([^\]]+)\]/i,
      /bcp_focus_ages['"]?\s*[:=]\s*\[([^\]]+)\]/i,
    ];
    for (const rx of patterns) {
      const m = line.match(rx);
      if (!m) continue;
      for (const part of m[1].split(",")) {
        const n = parseInt(part.trim(), 10);
        if (!isNaN(n)) ages.push(n);
      }
    }
  }
  return ages;
}

function formatHouseList(houses: unknown): string {
  if (!Array.isArray(houses) || houses.length === 0) return "—";
  return houses.map((h) => `${h}H`).join(", ");
}

function marriageBcpAgesFromStep0a(
  step0a: Record<string, unknown> | undefined,
  userAge: number | null,
  evidence?: string[],
): { ages: number[]; priorityAges: Set<number> } {
  const pool: number[] = [];
  const priority = new Set<number>();
  const add = (arr: unknown, asPriority = false) => {
    if (!Array.isArray(arr)) return;
    for (const x of arr) {
      const n = typeof x === "number" ? x : parseInt(String(x), 10);
      if (!isNaN(n)) {
        pool.push(n);
        if (asPriority) priority.add(n);
      }
    }
  };
  if (step0a) {
    add(step0a.shared_house_priority_ages, true);
    add(step0a.bcp_ages_next_years);
    add(step0a.focus_ages);
    add(step0a.priority_ages);
    add(step0a.future_priority_ages);
    for (const key of ("next_activation_age", "primary_reference_age") as const) {
      const v = step0a[key];
      if (v != null) {
        const n = typeof v === "number" ? v : parseInt(String(v), 10);
        if (!isNaN(n)) pool.push(n);
      }
    }
  }
  if (pool.length === 0) {
    pool.push(...parseBcpAgesFromEvidence(evidence));
  }
  const uniq = [...new Set(pool)].sort((a, b) => a - b);
  if (userAge == null || isNaN(userAge)) {
    return { ages: uniq.slice(0, 4), priorityAges: priority };
  }

  const fromCurrent = uniq.filter((a) => a >= userAge);
  if (fromCurrent.length > 0) {
    return { ages: fromCurrent.slice(0, 4), priorityAges: priority };
  }

  if (uniq.includes(userAge)) {
    const rest = uniq.filter((a) => a > userAge);
    return { ages: [userAge, ...rest].slice(0, 4), priorityAges: priority };
  }
  return { ages: uniq.slice(0, 4), priorityAges: priority };
}

function formatOneHouse(h: unknown): string {
  if (h == null || h === "") return "—";
  const n = typeof h === "number" ? h : parseInt(String(h), 10);
  return isNaN(n) ? String(h) : `${n}H`;
}

function bcpAgesForHouse(house: number, userAge: number | null): number[] {
  const ages: number[] = [];
  for (let a = house; a <= 96; a += 12) ages.push(a);
  if (userAge == null || isNaN(userAge)) return ages.slice(0, 4);
  return ages.filter((a) => a >= userAge).slice(0, 4);
}

type BcpHouseItem = { type?: string; house?: number; ages?: number[] };
type BcpDivDisplay = { seventh_lord?: string; items?: BcpHouseItem[] };

function formatDivisionBcpLine(
  div: BcpDivDisplay | undefined,
  prefix: string,
  fallbackLord: string,
  userAge: number | null,
  step0a?: Record<string, unknown>,
): string {
  const lord = div?.seventh_lord || fallbackLord;
  const items = div?.items || [];
  if (items.length > 0) {
    const parts = items
      .filter((it) => typeof it.house === "number")
      .map((it) => {
        const h = it.house as number;
        const ages =
          it.ages && it.ages.length > 0 ? it.ages : bcpAgesForHouse(h, userAge);
        const ageStr = ages.length ? ages.join(", ") : "—";
        return it.type === "placement"
          ? `baitha ${h}H → ages ${ageStr}`
          : `aspect ${h}H → ages ${ageStr}`;
      });
    if (parts.length) return `${prefix} ${lord}: ${parts.join(" · ")}`;
  }

  const sitKey = prefix === "D1" ? "d1_7l_placement_house" : "d9_7l_placement_house";
  const aspKey = prefix === "D1" ? "d1_7l_aspect_houses" : "d9_7l_aspect_houses";
  const sit = step0a?.[sitKey];
  const asp = step0a?.[aspKey];
  const chunks: string[] = [];
  if (sit != null && sit !== "") {
    const h = Number(sit);
    if (!isNaN(h)) {
      const ages = bcpAgesForHouse(h, userAge);
      chunks.push(`baitha ${h}H → ages ${ages.join(", ") || "—"}`);
    }
  }
  if (Array.isArray(asp) && asp.length) {
    for (const h of asp) {
      const hn = Number(h);
      if (!isNaN(hn)) {
        const ages = bcpAgesForHouse(hn, userAge);
        chunks.push(`aspect ${hn}H → ages ${ages.join(", ") || "—"}`);
      }
    }
  }
  return chunks.length
    ? `${prefix} ${lord}: ${chunks.join(" · ")}`
    : `${prefix} ${lord}: —`;
}

function rebuildBcpHouseDisplayFromStep0a(
  step0a: Record<string, unknown> | undefined,
  userAge: number | null,
): { d1?: BcpDivDisplay; d9?: BcpDivDisplay } {
  const buildDiv = (
    lordKey: string,
    sitKey: string,
    aspKey: string,
  ): BcpDivDisplay => {
    const lord = String(step0a?.[lordKey] || "7L");
    const items: BcpHouseItem[] = [];
    const sit = step0a?.[sitKey];
    if (sit != null && sit !== "") {
      const h = Number(sit);
      if (!isNaN(h)) {
        items.push({ type: "placement", house: h, ages: bcpAgesForHouse(h, userAge) });
      }
    }
    const asp = step0a?.[aspKey];
    if (Array.isArray(asp)) {
      for (const x of asp) {
        const h = Number(x);
        if (!isNaN(h)) {
          items.push({ type: "aspect", house: h, ages: bcpAgesForHouse(h, userAge) });
        }
      }
    }
    return { seventh_lord: lord, items };
  };
  return {
    d1: buildDiv("d1_seventh_lord", "d1_7l_placement_house", "d1_7l_aspect_houses"),
    d9: buildDiv("d9_seventh_lord", "d9_7l_placement_house", "d9_7l_aspect_houses"),
  };
}

function buildBcpLinkageLines(
  step0a: Record<string, unknown> | undefined,
  userAge: number | null,
): string[] {
  const saved = (step0a?.bcp_house_display || {}) as {
    d1?: BcpDivDisplay;
    d9?: BcpDivDisplay;
    shared_house_items?: { house?: number; ages?: number[] }[];
  };
  const rebuilt = rebuildBcpHouseDisplayFromStep0a(step0a, userAge);
  const hasSavedItems =
    (saved.d1?.items?.length || 0) > 0 || (saved.d9?.items?.length || 0) > 0;
  const hasRebuiltItems =
    (rebuilt.d1?.items?.length || 0) > 0 || (rebuilt.d9?.items?.length || 0) > 0;
  const display = hasSavedItems
    ? saved
    : hasRebuiltItems
      ? { ...saved, ...rebuilt }
      : saved;
  const d1Lord = String(step0a?.d1_seventh_lord || display.d1?.seventh_lord || "7L");
  const d9Lord = String(step0a?.d9_seventh_lord || display.d9?.seventh_lord || "7L");
  const lines = [
    formatDivisionBcpLine(display.d1, "D1", d1Lord, userAge, step0a),
    formatDivisionBcpLine(display.d9, "D9", d9Lord, userAge, step0a),
  ];
  const shared = display.shared_house_items || [];
  if (shared.length) {
    const parts = shared
      .filter((s) => typeof s.house === "number")
      .map((s) => {
        const ages =
          s.ages && s.ages.length
            ? s.ages
            : bcpAgesForHouse(s.house as number, userAge);
        return `${s.house}H → ages ${ages.join(", ") || "—"}`;
      });
    if (parts.length) {
      lines.push(`D1+D9 same ghar (★ priority): ${parts.join(" · ")}`);
    }
  } else {
    const sharedHouses = formatHouseList(step0a?.shared_7l_linkage_houses);
    if (sharedHouses !== "—") {
      lines.push(`D1+D9 same ghar → priority: ${sharedHouses}`);
    }
  }
  return lines;
}

function formatMarriageBcpAgesStep(
  step0a: Record<string, unknown> | undefined,
  userAge: number | null,
  evidence?: string[],
): {
  title: string;
  detail: string;
  ages: number[];
  linkageLines: string[];
} {
  const { ages, priorityAges } = marriageBcpAgesFromStep0a(step0a, userAge, evidence);
  const linkageLines = buildBcpLinkageLines(step0a, userAge);

  if (ages.length === 0) {
    return {
      title: "Step 2 — BCP ages",
      detail:
        userAge != null
          ? `age ${userAge} se — BCP ages not saved (re-ask after deploy)`
          : "— (not saved)",
      ages: [],
      linkageLines,
    };
  }

  const mode =
    step0a?.timing_mode != null ? String(step0a.timing_mode).replace(/_/g, " ") : "";
  const ageLabel = ages
    .map((a) => (priorityAges.has(a) ? `${a}★` : String(a)))
    .join(", ");
  const cur = userAge != null && !isNaN(userAge) ? userAge : null;
  const detail =
    cur != null
      ? `age ${cur} se → ${ageLabel}${mode ? ` · ${mode}` : ""}`
      : ageLabel;

  return {
    title: "Step 2 — BCP ages",
    detail,
    ages,
    linkageLines,
  };
}

function marriageUserAge(
  step0: Record<string, unknown> | undefined,
  evidence?: string[],
): number | null {
  if (step0?.user_age != null) {
    const n = Number(step0.user_age);
    if (!isNaN(n)) return n;
  }
  return parseUserAgeFromEvidence(evidence);
}

function marriageBcpFmtFromRow(
  row: Pick<AskQuestionItem, "marriage_bcp_step2">,
  step0a: Record<string, unknown> | undefined,
  userAge: number | null,
  evidence?: string[],
): ReturnType<typeof formatMarriageBcpAgesStep> {
  const api = row.marriage_bcp_step2;
  if (api?.linkage_lines?.length) {
    return {
      title: api.title || "Step 2 — BCP ages",
      detail: api.detail || "—",
      ages: api.ages || [],
      linkageLines: api.linkage_lines,
    };
  }
  const mergedStep0a =
    api?.step0a && Object.keys(api.step0a).length
      ? { ...(step0a || {}), ...api.step0a }
      : step0a;
  return formatMarriageBcpAgesStep(mergedStep0a, userAge ?? api?.user_age ?? null, evidence);
}

export function EngineTracePanel({
  ctx,
  row,
}: {
  ctx: AskLlmContext;
  row: Pick<AskQuestionItem, "answer_text" | "answer_source" | "question_text" | "marriage_bcp_step2">;
}) {
  const blocks = (ctx.blocks || {}) as Record<string, unknown>;
  const sliceMeta = (ctx.slice_meta || {}) as Record<string, unknown>;
  const engineFacts = engineFactsFromContext(ctx);
  let trace = (
    blocks.engine_trace ||
    blocks.marriage_engine_trace ||
    blocks.career_engine_trace
  ) as EngineTrace | undefined;
  if (!trace?.step_audit && !trace?.timing_audit) {
    const stepAudit = (sliceMeta.step_audit || engineFacts.step_audit) as
      | Record<string, Record<string, unknown>>
      | undefined;
    const timingAudit = (sliceMeta.timing_audit || engineFacts.timing_audit) as
      | EngineTrace["timing_audit"]
      | undefined;
    if (stepAudit || timingAudit) {
      trace = {
        engine: String(sliceMeta.slice || "marriage_timing_m17"),
        step_audit: stepAudit,
        timing_audit: timingAudit,
        primary_window: summaryWindowFromMeta(sliceMeta, engineFacts),
      };
    }
  }
  const stepOrder =
    trace?.step_order?.length
      ? trace.step_order.filter((k) => !k.startsWith("step0"))
      : ["step1", "step2", "step3", "step4", "step5", "step6"];
  const stepAudit = stepAuditFromMarriageContext(ctx, trace, sliceMeta, engineFacts);
  if (trace && !trace.step_audit && Object.keys(stepAudit).length > 0) {
    trace = { ...trace, step_audit: stepAudit };
  }
  const timingAudit = trace?.timing_audit;
  const engineId = String(trace?.engine || "");
  const marriageM17 = isMarriageM17Trace(engineId, ctx);
  const marriageStepOrder = [
    "step3",
    "step4",
    "step5",
    "step6",
    "step7",
    "step8",
  ];
  const marriageStepCardsOrder = [
    "step1",
    "step2",
    "step3",
    "step4",
    "step5",
    "step6",
    "step7",
    "step8",
  ];
  const hasTrace = Boolean(
    (trace && (trace.step_audit || trace.timing_audit)) ||
      (marriageM17 && marriageStepOrder.some((k) => stepAudit[k])),
  );
  const dashaFirst = isDashaFirstTimingEngine(engineId);
  const marriageStep0 = marriageM17 ? marriageStep0FromContext(ctx, stepAudit) : undefined;
  const marriageStep0Fmt = formatMarriageEarlyLateStep(marriageStep0);
  const marriageEvidence =
    (engineFacts.evidence as string[] | undefined) ||
    (sliceMeta.evidence as string[] | undefined) ||
    [];
  const marriageUserAgeVal = marriageM17
    ? marriageUserAge(marriageStep0, marriageEvidence)
    : null;
  const marriageStep0a = marriageM17
    ? marriageStep0aFromContext(stepAudit, sliceMeta, marriageEvidence)
    : undefined;
  const marriageBcpFmt = marriageM17
    ? marriageBcpFmtFromRow(row, marriageStep0a, marriageUserAgeVal, marriageEvidence)
    : null;

  const pipelineChecksTitle = marriageM17
    ? "Marriage timing — Steps 1–8 (early/late → BCP → shadi planets → dasha)"
    : dashaFirst
      ? `Engine checks — step 2 onward (${engineId.replace("_timing_v1", "")})`
      : engineId === "career_timing_v1"
        ? "Timing pipeline — career (dasha-first)"
        : engineId === "marriage_timing_m17"
          ? "Marriage engine checks (M17)"
          : "Timing engine checks";

  const requestMeta = [
    {
      title: "Question",
      detail: ctx.question || row.question_text || "—",
    },
    {
      title: "Intent routing",
      detail:
        ctx.intent_source === "llm" && ctx.llm_intent
          ? `LLM → ${ctx.llm_intent.mr_archetype || ctx.llm_intent.domain || "general"} (confidence ${ctx.llm_intent.confidence ?? "?"})`
          : `Regex / rules · route ${ctx.route || "—"} · type ${ctx.question_type || "—"}`,
    },
    {
      title: "Engine",
      detail: (() => {
        const disp = resolveEngineDisplayFromContext(ctx, row);
        return disp.adminLine !== "—" ? disp.adminLine : String(
          trace?.engine ||
            (ctx.checks as Record<string, unknown> | undefined)?.slice_type ||
            "chart analysis",
        );
      })(),
    },
    {
      title: ctx.llm_called === false ? "LLM skipped" : "LLM narrator",
      detail:
        ctx.llm_called === false
          ? ctx.skip_reason || "Deterministic template reply"
          : `Model ${ctx.model || "—"} · max tokens ${ctx.max_tokens ?? "—"}`,
    },
    {
      title: "User answer",
      detail: row.answer_text || trace?.timing_audit?.expected_reply || "—",
    },
  ];

  const pipeline = marriageM17
    ? [
        {
          n: 1,
          title: marriageStep0Fmt.title,
          detail: marriageStep0Fmt.detail,
          hero: true,
        },
        {
          n: 2,
          title: marriageBcpFmt?.title || "Step 2 — BCP ages",
          detail: marriageBcpFmt?.detail || "—",
          hero: false,
        },
        ...marriageStepOrder.map((key, idx) => {
          const step = stepAudit[key];
          const title = marriageAuditStepTitle(key, step);
          const detail =
            key === "step3"
              ? formatMarriageStep3Planets(stepAudit, step)
              : key === "step4"
                ? formatMarriageStep4CommonPlanets(stepAudit)
                : key === "step5"
                  ? formatMarriageStep5Ranked(stepAudit)
                  : key === "step6"
                    ? formatMarriageStep6Dasha(stepAudit, trace)
                    : step
                ? stepOneLiner(key, step, engineId || "marriage_timing_m17")
                : "— (not saved)";
          return {
            n: idx + 3,
            title,
            detail,
            hero: key === "step3",
          };
        }),
      ]
    : dashaFirst
    ? [
        {
          n: 1,
          title: "Active dasha — abhi kya chal raha hai",
          detail: formatRunningDashaDetail(trace, stepAudit, timingAudit),
          hero: true,
        },
        ...stepOrder
          .filter((key) => key !== "step1")
          .map((key, idx) => {
            const step = stepAudit[key];
            if (!step) return null;
            return {
              n: idx + 2,
              title: String(step.name || key),
              detail: stepOneLiner(key, step, engineId),
              hero: false,
            };
          })
          .filter(Boolean) as { n: number; title: string; detail: string; hero: boolean }[],
      ]
    : requestMeta.map((item, i) => ({
        n: i + 1,
        title: item.title,
        detail: item.detail,
        hero: false,
      }));

  const marriageHasFullTrace = marriageM17
    ? Boolean(
        stepAudit.step0 ||
          stepAudit.step3 ||
          stepAudit.step1 ||
          marriageStep0?.recomputed_from_chart ||
          (trace?.step_audit && Object.keys(trace.step_audit).length > 0),
      )
    : false;
  const stepCardsOrder = marriageM17
    ? marriageStepCardsOrder
    : dashaFirst
      ? stepOrder.filter((k) => k !== "step1")
      : stepOrder;

  return (
    <details className="engine-trace-panel" open={hasTrace}>
      <summary>
        {marriageM17
          ? marriageHasFullTrace
            ? "Marriage timing — full trace (Steps 1–8)"
            : "Marriage timing — Steps 1–2 (engine trace incomplete)"
          : dashaFirst
            ? "Timing pipeline — step 1 = running dasha"
            : "Engine pipeline — step by step"}
        {hasTrace || marriageHasFullTrace
          ? ""
          : " (limited — re-ask after API deploy for full trace)"}
      </summary>
      <div className="engine-trace-body">
        <ol className="engine-pipeline-overview">
          {pipeline.map((p) => (
            <li key={p.n} className={p.hero ? "engine-pipeline-hero" : undefined}>
              <span className="engine-pipeline-num">{p.n}</span>
              <div>
                <strong>{p.title}</strong>
                {p.detail.includes("\n") ? (
                  <ul className="llm-check-list engine-marriage-step3-linkage">
                    {p.detail.split("\n").map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-muted engine-pipeline-detail">{p.detail}</p>
                )}
              </div>
            </li>
          ))}
        </ol>

        {marriageM17 && marriageBcpFmt?.linkageLines?.length ? (
          <ul className="llm-check-list engine-marriage-bcp-linkage">
            {marriageBcpFmt.linkageLines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        ) : null}

        {dashaFirst ? (
          <details className="engine-request-meta">
            <summary>Question, intent &amp; LLM (admin meta)</summary>
            <ol className="engine-pipeline-overview engine-pipeline-meta">
              {requestMeta.map((item, i) => (
                <li key={item.title}>
                  <span className="engine-pipeline-num meta">{i + 1}</span>
                  <div>
                    <strong>{item.title}</strong>
                    <p className="detail-muted engine-pipeline-detail">{item.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          </details>
        ) : null}

        {trace?.running_dasha_window || trace?.primary_window || trace?.backup_window ? (
          <div className="engine-outcome-box">
            {!dashaFirst && trace?.running_dasha_window ? (
              <p>
                <strong>Running dasha (abhi):</strong> {trace.running_dasha_window}
              </p>
            ) : !dashaFirst && timingAudit?.running_dasha?.end ? (
              <p>
                <strong>Running dasha (abhi):</strong>{" "}
                {fmtCheckValue(timingAudit.running_dasha.lords)} · kab tak{" "}
                {fmtCheckValue(timingAudit.running_dasha.end)}
              </p>
            ) : null}
            {(trace as { used_window?: string }).used_window === "backup" ? (
              <>
                <p>
                  <strong>Backup window (answered):</strong>{" "}
                  {trace.backup_window || "—"}
                </p>
                {trace.primary_window ? (
                  <p className="detail-muted">
                    <strong>Primary (rejected):</strong> {trace.primary_window}
                  </p>
                ) : null}
              </>
            ) : (
              <p>
                <strong>Primary window:</strong> {trace.primary_window || "—"}
              </p>
            )}
            {trace.backup_window ? (
              <p>
                <strong>Backup:</strong> {trace.backup_window}
              </p>
            ) : null}
            {trace.key_trigger ? (
              <p>
                <strong>Key trigger:</strong> {trace.key_trigger}
              </p>
            ) : null}
          </div>
        ) : null}

        {hasTrace ? (
          <>
            <p className="detail-summary">{pipelineChecksTitle}</p>
            <div className="engine-steps-list">
              {stepCardsOrder.map((key, idx) => {
                const step = stepAudit[key];
                if (!step) return null;
                const status = String(step.status || "DONE");
                const stepLabel = marriageM17
                  ? (
                      {
                        step1: "D1",
                        step2: "D9",
                        step3: "3",
                        step4: "4",
                        step5: "5",
                        step6: "6",
                        step7: "7",
                        step8: "8",
                      }[key] || key
                    )
                  : dashaFirst
                    ? String(idx + 2)
                    : key;
                return (
                  <details key={key} className="engine-step-card">
                    <summary>
                      <span className="engine-step-key">{stepLabel}</span>
                      <span className="engine-step-oneline">{stepOneLiner(key, step, engineId)}</span>
                      <span className={`engine-step-status status-${status.toLowerCase()}`}>
                        {status}
                      </span>
                    </summary>
                    <JsonDetail
                      data={
                        key === "step7"
                          ? {
                              transit_confirmed: step.transit_confirmed,
                              double_transit: step.double_transit,
                              transit_type: step.transit_type,
                              transit_type_label: step.transit_type_label,
                              chart_context: step.chart_context,
                              jupiter_hit: step.jupiter_hit,
                              saturn_hit: step.saturn_hit,
                              matched_count: step.matched_count,
                              candidate_count: step.candidate_count,
                              per_dasha_windows: step.per_dasha_windows,
                              months: step.months,
                              by_month: step.by_month,
                              detail: formatStep7TransitDetail(step),
                              per_dasha_lines: formatMarriageStep7PerDashaLines(stepAudit),
                            }
                          : key === "step3" && Array.isArray(step.marriage_giving_planets)
                            ? {
                                merged_count: step.merged_count,
                                planet_names: step.planet_names,
                                marriage_giving_planets: step.marriage_giving_planets,
                                top_merged: step.top_merged,
                              }
                            : step
                      }
                      label={key === "step7" ? "Transit by month" : "Step JSON"}
                    />
                  </details>
                );
              })}
            </div>

            {!marriageM17 && timingAudit ? (
              <details open className="engine-audit-panel">
                <summary>
                  Final validation · status {timingAudit.status || "—"}
                  {timingAudit.issues?.length
                    ? ` · ${timingAudit.issues.length} issue(s)`
                    : ""}
                </summary>
                <div className="engine-audit-body">
                  {timingAudit.expected_reply ? (
                    <p>
                      <strong>Locked reply template:</strong> {timingAudit.expected_reply}
                    </p>
                  ) : null}
                  {timingAudit.primary_dasha ? (
                    <p className="detail-muted">
                      <strong>Primary dasha:</strong>{" "}
                      {fmtCheckValue(timingAudit.primary_dasha.md)}-
                      {fmtCheckValue(timingAudit.primary_dasha.ad)}-
                      {fmtCheckValue(timingAudit.primary_dasha.pd)}{" "}
                      {fmtCheckValue(timingAudit.primary_dasha.start_iso)} →{" "}
                      {fmtCheckValue(timingAudit.primary_dasha.end_iso)}
                    </p>
                  ) : null}
                  {Array.isArray(timingAudit.checks) && timingAudit.checks.length > 0 ? (
                    <ul className="llm-check-list engine-audit-checks">
                      {timingAudit.checks.map((c, i) => (
                        <li key={`${c.name}-${i}`}>
                          <span className={c.ok ? "audit-ok" : "audit-warn"}>
                            {c.ok ? "✓" : "⚠"}
                          </span>{" "}
                          <code>{c.name}</code>: {c.detail || (c.ok ? "ok" : "failed")}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {timingAudit.issues && timingAudit.issues.length > 0 ? (
                    <>
                      <p>
                        <strong>Issues:</strong>
                      </p>
                      <ul className="llm-check-list">
                        {timingAudit.issues.map((issue) => (
                          <li key={issue}>{issue}</li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                  <JsonDetail data={timingAudit} label="Full timing audit JSON" />
                </div>
              </details>
            ) : null}

            {trace.factors && trace.factors.length > 0 ? (
              <details>
                <summary>Engine factors ({trace.factors.length})</summary>
                <ul className="llm-check-list">
                  {trace.factors.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </details>
            ) : null}

            {trace.top_3_windows && trace.top_3_windows.length > 0 ? (
              <details>
                <summary>Top timing windows ({trace.top_3_windows.length})</summary>
                <pre className="llm-context-pre">
                  {JSON.stringify(trace.top_3_windows, null, 2)}
                </pre>
              </details>
            ) : null}
          </>
        ) : !hasTrace ? (
          <p className="detail-muted">
            Structured step audit not saved for this row. Deploy latest API, restart server, then
            ask again. Until then use Checks / chart context below.
          </p>
        ) : null}

        {typeof blocks.marriage_engine === "string" && blocks.marriage_engine.trim() && !marriageM17 ? (
          <details>
            <summary>Marriage locked-facts block (prompt text)</summary>
            <pre className="llm-context-pre">{String(blocks.marriage_engine)}</pre>
          </details>
        ) : null}
      </div>
    </details>
  );
}

export function AnswerPathBadge({
  ctx,
  row,
}: {
  ctx: AskLlmContext | null;
  row: Pick<AskQuestionItem, "answer_source" | "engine_tag" | "total_tokens">;
}) {
  const { code, label } = resolveAnswerPath(ctx, row);
  return <span className={`answer-path-badge answer-path-${code}`}>{label}</span>;
}

export function AskLlmContextPanel({
  row,
  panelId,
  defaultOpen = false,
}: {
  row: AskQuestionItem;
  panelId?: string;
  defaultOpen?: boolean;
}) {
  const ctx = parseAskLlmContext(row);
  const id = panelId || `ask-llm-context-${row.id}`;

  if (!ctx) {
    return (
      <details id={id} className="llm-context-panel llm-context-missing" open={defaultOpen || undefined}>
        <summary>Engine evidence — not saved for this question</summary>
        <p className="detail-muted">
          Deploy latest API + admin-web, restart cosmic-api, run DB migration, then ask a
          new question. Rows before deploy will not have this data.
        </p>
      </details>
    );
  }

  const checks = (ctx.checks || {}) as Record<string, unknown>;
  const sliceMeta = (ctx.slice_meta || {}) as Record<string, unknown>;
  const engineFacts = engineFactsFromContext(ctx);
  const evidence =
    (engineFacts.evidence && engineFacts.evidence.length > 0
      ? engineFacts.evidence
      : (sliceMeta.evidence as string[] | undefined)) || undefined;
  const calculationSteps =
    ((engineFacts as Record<string, unknown>).calculation_steps as string[] | undefined) ||
    (sliceMeta.calculation_steps as string[] | undefined);
  const evidencePositive =
    (engineFacts.evidence_positive && engineFacts.evidence_positive.length > 0
      ? engineFacts.evidence_positive
      : (sliceMeta.evidence_positive as string[] | undefined)) ?? [];
  const evidenceNegative =
    (engineFacts.evidence_negative && engineFacts.evidence_negative.length > 0
      ? engineFacts.evidence_negative
      : (sliceMeta.evidence_negative as string[] | undefined)) ?? [];
  const evidenceNeutral =
    (engineFacts.evidence_neutral && engineFacts.evidence_neutral.length > 0
      ? engineFacts.evidence_neutral
      : (sliceMeta.evidence_neutral as string[] | undefined)) ?? [];
  const sliceName = String(sliceMeta.slice || checks.slice_type || "");
  const marriageM17 = isMarriageM17Trace(sliceName, ctx);
  const marriageStepAudit = stepAuditFromMarriageContext(
    ctx,
    (((ctx.blocks || {}) as Record<string, unknown>).engine_trace as EngineTrace | undefined),
    sliceMeta,
    engineFacts as Record<string, unknown>,
  );
  const marriageEngineTrace = ((ctx.blocks || {}) as Record<string, unknown>)
    .engine_trace as EngineTrace | undefined;
  const marriageStep0Fmt = formatMarriageEarlyLateStep(marriageStepAudit.step0);
  const marriageUserAgeVal = marriageM17
    ? marriageUserAge(marriageStepAudit.step0, evidence)
    : null;
  const marriageBcpFmt = marriageM17
    ? marriageBcpFmtFromRow(
        row,
        marriageStep0aFromContext(marriageStepAudit, sliceMeta, evidence),
        marriageUserAgeVal,
        evidence,
      )
    : null;
  const isTimingEngineSlice =
    sliceName.includes("timing") || Boolean(ctx.is_timing || ctx.question_type === "TIMING");
  const isMrEngineSlice =
    sliceName === "mr_engine_v1" || checks.slice_type === "mr_engine_v1";
  const hasSplitEvidence = Boolean(
    isMrEngineSlice &&
      !isTimingEngineSlice &&
      (evidencePositive.length > 0 ||
        evidenceNegative.length > 0 ||
        evidenceNeutral.length > 0),
  );
  const summary =
    (engineFacts.summary && engineFacts.summary.length > 0
      ? engineFacts.summary
      : (sliceMeta.summary as string[] | undefined)) || undefined;
  const verdict = engineFacts.verdict
    ? String(engineFacts.verdict)
    : sliceMeta.verdict
      ? String(sliceMeta.verdict)
      : "";
  const archetype = engineFacts.archetype
    ? String(engineFacts.archetype)
    : sliceMeta.archetype
      ? String(sliceMeta.archetype)
      : "";
  const engineDisplay = resolveEngineDisplayFromContext(ctx, row);
  const dashaTrace = (
    (engineFacts as Record<string, unknown>).dasha_trace ||
    sliceMeta.dasha_trace
  ) as Record<string, unknown> | undefined;
  const rawOnly = typeof (ctx as { raw?: string }).raw === "string";

  return (
    <details id={id} className="llm-context-panel" open={defaultOpen || undefined}>
      <summary>
        Engine evidence
        {engineDisplay.engineNo != null
          ? ` · Engine #${engineDisplay.engineNo}`
          : archetype
            ? ` · ${archetype}`
            : ""}
      </summary>
      <div className="llm-context-body">
        {rawOnly ? (
          <pre className="llm-context-pre">{(ctx as { raw: string }).raw}</pre>
        ) : !marriageM17 && !verdict && (!evidence || evidence.length === 0) && !hasSplitEvidence ? (
          <p className="detail-muted">No structured engine facts for this question.</p>
        ) : marriageM17 &&
          !marriageStepAudit.step0 &&
          !(summary && summary.length) &&
          !(evidence && evidence.length) ? (
          <p className="detail-muted">
            Step 1 (early / late) not saved — marriage question dubara puchein (API restart +
            birth profile saved honi chahiye).
          </p>
        ) : (
          <div className="engine-facts-box">
            {engineDisplay.adminLine !== "—" ? (
              <p>
                <strong>Engine:</strong> <code>{engineDisplay.adminLine}</code>
              </p>
            ) : null}
            {archetype && !marriageM17 ? (
              <p>
                <strong>Archetype:</strong> {archetype}
              </p>
            ) : null}
            {verdict && !marriageM17 ? (
              <p>
                <strong>Verdict:</strong> {verdict}
              </p>
            ) : null}
            {marriageM17 ? (
              <>
                <p className="engine-marriage-step0">
                  <strong>{marriageStep0Fmt.title}:</strong> {marriageStep0Fmt.detail}
                </p>
                <p className="engine-marriage-step0">
                  <strong>{marriageBcpFmt?.title || "Step 2 — BCP ages"}:</strong>{" "}
                  {marriageBcpFmt?.detail || "—"}
                </p>
                {marriageBcpFmt?.linkageLines?.length ? (
                  <ul className="llm-check-list engine-marriage-bcp-linkage">
                    {marriageBcpFmt.linkageLines.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : null}
                <div className="engine-marriage-step0 engine-marriage-step3">
                  <strong>Step 3 — D1+D9 7H linkage:</strong>
                  <MarriageStep3LinkageLines stepAudit={marriageStepAudit} />
                </div>
                <p className="engine-marriage-step0 engine-marriage-step4">
                  <strong>Step 4 — Common planets (D1+D9):</strong>{" "}
                  {formatMarriageStep4CommonPlanets(marriageStepAudit)}
                </p>
                <div className="engine-marriage-step0 engine-marriage-step5">
                  <strong>Step 5 — Rank significators (weighted points):</strong>
                  <MarriageStep5RankedLines stepAudit={marriageStepAudit} />
                </div>
                <div className="engine-marriage-step0 engine-marriage-step6">
                  <strong>Step 6 — Final dasha (Guru/Shani match):</strong>
                  <MarriageStep6DashaLines
                    stepAudit={marriageStepAudit}
                    trace={marriageEngineTrace}
                  />
                </div>
                <div className="engine-marriage-step0 engine-marriage-step7">
                  <strong>Step 7 — Guru/Shani transit on 7H/7L:</strong>
                  <MarriageStep7TransitLines stepAudit={marriageStepAudit} />
                </div>
              </>
            ) : null}
            {!marriageM17 && dashaTrace &&
            (dashaTrace.current_lords ||
              dashaTrace.running_lords ||
              dashaTrace.next_career_ad) ? (
              <p>
                <strong>Dasha check:</strong> current{" "}
                {fmtCheckValue(dashaTrace.current_lords || dashaTrace.running_lords)}
                {(dashaTrace.current_start || dashaTrace.current_end ||
                  dashaTrace.running_start ||
                  dashaTrace.running_end) ? (
                  <>
                    {" "}
                    ({fmtCheckValue(
                      dashaTrace.current_start || dashaTrace.running_start,
                    )}{" "}
                    →{" "}
                    {fmtCheckValue(dashaTrace.current_end || dashaTrace.running_end)})
                  </>
                ) : null}
                {dashaTrace.next_career_ad ? (
                  <>
                    {" "}
                    · next career AD {fmtCheckValue(dashaTrace.next_career_ad)}
                    {dashaTrace.next_career_start || dashaTrace.next_career_end ? (
                      <>
                        {" "}
                        ({fmtCheckValue(dashaTrace.next_career_start)} →{" "}
                        {fmtCheckValue(dashaTrace.next_career_end)})
                      </>
                    ) : null}
                  </>
                ) : null}
              </p>
            ) : null}
            {!marriageM17 && (engineFacts.love_score != null || engineFacts.arrange_score != null) ? (
              <p>
                <strong>Scores:</strong> love={fmtCheckValue(engineFacts.love_score)}, arrange=
                {fmtCheckValue(engineFacts.arrange_score)}
                {engineFacts.confidence_ratio != null ? (
                  <> · ratio={fmtCheckValue(engineFacts.confidence_ratio)}</>
                ) : null}
              </p>
            ) : null}
            {summary && summary.length > 0 ? (
              <>
                <p>
                  <strong>{marriageM17 ? "Answer window:" : "Summary for narrator:"}</strong>
                </p>
                <ul className="llm-check-list">
                  {(marriageM17 ? summary.slice(0, 1) : summary).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {marriageM17 && evidence && evidence.length > 0 ? (
              <>
                <p>
                  <strong>Marriage timing evidence ({evidence.length}):</strong>
                </p>
                <ul className="llm-check-list">
                  {evidence.map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {marriageM17 && calculationSteps && calculationSteps.length > 0 ? (
              <>
                <p>
                  <strong>Calculation steps ({calculationSteps.length}):</strong>
                </p>
                <ul className="llm-check-list">
                  {calculationSteps.map((e) => (
                    <li key={`mcalc-${e}`}>{e}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {!marriageM17 && calculationSteps && calculationSteps.length > 0 ? (
              <>
                <p>
                  <strong>How timing was calculated ({calculationSteps.length}):</strong>
                </p>
                <ul className="llm-check-list">
                  {calculationSteps.map((e) => (
                    <li key={`calc-${e}`}>{e}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {!marriageM17 && hasSplitEvidence ? (
              <>
                <p>
                  <strong>Positive evidence ({evidencePositive.length}):</strong>
                </p>
                {evidencePositive.length > 0 ? (
                  <ul className="llm-check-list evidence-positive">
                    {evidencePositive.map((e) => (
                      <li key={`pos-${e}`}>{e}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-muted">— none (0)</p>
                )}
                <p>
                  <strong>Negative / affliction evidence ({evidenceNegative.length}):</strong>
                </p>
                {evidenceNegative.length > 0 ? (
                  <ul className="llm-check-list evidence-negative">
                    {evidenceNegative.map((e) => (
                      <li key={`neg-${e}`}>{e}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-muted">— none (0)</p>
                )}
                <p>
                  <strong>Neutral chart context ({evidenceNeutral.length}):</strong>
                </p>
                {evidenceNeutral.length > 0 ? (
                  <ul className="llm-check-list">
                    {evidenceNeutral.map((e) => (
                      <li key={`neu-${e}`}>{e}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="detail-muted">— none (0)</p>
                )}
              </>
            ) : marriageM17 && evidence && evidence.length > 0 ? null : !marriageM17 && evidence && evidence.length > 0 ? (
              <>
                <p>
                  <strong>
                    {ctx.is_timing || ctx.question_type === "TIMING"
                      ? `Timing evidence (${evidence.length})`
                      : `Chart / engine evidence (${evidence.length})`}
                    :
                  </strong>
                </p>
                <ul className="llm-check-list">
                  {evidence.map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        )}
      </div>
    </details>
  );
}
