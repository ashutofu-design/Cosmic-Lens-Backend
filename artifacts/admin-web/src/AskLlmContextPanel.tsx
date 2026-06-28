import type { AskLlmContext, AskQuestionItem } from "./api";

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
  const line = ctx.understanding_line?.trim();
  if (line && line.includes(" — ")) return line;
  const word = resolveQuestionUnderstoodWord(ctx);
  const detail = ctx.understanding_detail?.trim();
  if (word && detail) return `${word} — ${detail}`;
  if (line) return line;
  if (word) return word;
  return "";
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

export function parseAskLlmContext(row: AskQuestionItem): AskLlmContext | null {
  if (row.llm_context && typeof row.llm_context === "object") {
    return row.llm_context;
  }
  const raw = row.llm_context_json;
  if (!raw || !String(raw).trim()) return null;
  try {
    const parsed = JSON.parse(raw) as AskLlmContext;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return { raw: String(raw).slice(0, 8000) };
  }
}

export type AnswerPathCode = "engine_then_llm" | "engine_only" | "direct_llm" | "unknown";

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
  if (ef && (ef.verdict || (ef.evidence && ef.evidence.length > 0))) {
    return ef;
  }
  const sm = ctx.slice_meta || {};
  return {
    archetype: sm.archetype,
    verdict: sm.verdict,
    summary: (sm.summary as string[] | undefined) || [],
    evidence: (sm.evidence as string[] | undefined) || [],
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
    return `${name} · 7L ${fmtCheckValue(r?.seventh_lord)} · in 7H ${fmtCheckValue(r?.planets_in_7th_house)}`;
  }
  if (stepKey === "step3") {
    const top = Array.isArray(step.top_merged) ? step.top_merged : [];
    const names = top
      .slice(0, 3)
      .map((t) => (asRecord(t)?.name as string) || "")
      .filter(Boolean)
      .join(", ");
    return `${name} · merged ${fmtCheckValue(step.merged_count)}${names ? ` · top ${names}` : ""}`;
  }
  if (stepKey === "step4") {
    const summary = step.summary;
    const summaryText =
      typeof summary === "string"
        ? summary
        : summary && typeof summary === "object"
          ? JSON.stringify(summary)
          : fmtCheckValue(summary);
    return `${name} · ${summaryText || "KP validate"}`;
  }
  if (stepKey === "step5") {
    const ranked = Array.isArray(step.ranked_top) ? step.ranked_top : [];
    const names = ranked
      .slice(0, 3)
      .map((t) => (asRecord(t)?.name as string) || "")
      .filter(Boolean)
      .join(", ");
    return `${name} · targets ${fmtCheckValue(step.target_lords)}${names ? ` · top ${names}` : ""}`;
  }
  if (stepKey === "step6") {
    const wins = Array.isArray(step.selected_windows) ? step.selected_windows : [];
    const first = asRecord(wins[0]);
    const w = first?.window ? String(first.window) : "";
    return `${name} · ${wins.length} window(s)${w ? ` · lead ${w}` : ""}`;
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

export function EngineTracePanel({
  ctx,
  row,
}: {
  ctx: AskLlmContext;
  row: Pick<AskQuestionItem, "answer_text" | "answer_source" | "question_text">;
}) {
  const blocks = (ctx.blocks || {}) as Record<string, unknown>;
  const trace = (
    blocks.engine_trace ||
    blocks.marriage_engine_trace ||
    blocks.career_engine_trace
  ) as EngineTrace | undefined;
  const hasTrace = Boolean(trace && (trace.step_audit || trace.timing_audit));
  const stepOrder =
    trace?.step_order?.length
      ? trace.step_order.filter((k) => !k.startsWith("step0"))
      : ["step1", "step2", "step3", "step4", "step5", "step6"];
  const stepAudit = trace?.step_audit || {};
  const timingAudit = trace?.timing_audit;
  const engineId = String(trace?.engine || "");
  const dashaFirst = isDashaFirstTimingEngine(engineId);

  const pipelineChecksTitle =
    dashaFirst
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
      detail: String(
        trace?.engine ||
          (ctx.checks as Record<string, unknown> | undefined)?.slice_type ||
          "chart analysis",
      ),
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

  const pipeline = dashaFirst
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

  const stepCardsOrder = dashaFirst
    ? stepOrder.filter((k) => k !== "step1")
    : stepOrder;

  return (
    <details className="engine-trace-panel" open={hasTrace}>
      <summary>
        {dashaFirst
          ? "Timing pipeline — step 1 = running dasha"
          : "Engine pipeline — step by step"}
        {hasTrace ? "" : " (limited — re-ask after API deploy for full trace)"}
      </summary>
      <div className="engine-trace-body">
        <ol className="engine-pipeline-overview">
          {pipeline.map((p) => (
            <li key={p.n} className={p.hero ? "engine-pipeline-hero" : undefined}>
              <span className="engine-pipeline-num">{p.n}</span>
              <div>
                <strong>{p.title}</strong>
                <p className="detail-muted engine-pipeline-detail">{p.detail}</p>
              </div>
            </li>
          ))}
        </ol>

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
                const stepLabel = dashaFirst ? String(idx + 2) : key;
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
                              months: step.months,
                              by_month: step.by_month,
                              detail: formatStep7TransitDetail(step),
                            }
                          : step
                      }
                      label={key === "step7" ? "Transit by month" : "Step JSON"}
                    />
                  </details>
                );
              })}
            </div>

            {timingAudit ? (
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
        ) : (
          <p className="detail-muted">
            Structured step audit not saved for this row. Deploy latest API, restart server, then
            ask again. Until then use Checks / chart context below.
          </p>
        )}

        {typeof blocks.marriage_engine === "string" && blocks.marriage_engine.trim() ? (
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
        <summary>LLM context — not saved for this question</summary>
        <p className="detail-muted">
          Deploy latest API + admin-web, restart cosmic-api, run DB migration, then ask a
          new question. Rows before deploy will not have this data.
        </p>
      </details>
    );
  }

  const checks = (ctx.checks || {}) as Record<string, unknown>;
  const sliceMeta = (ctx.slice_meta || {}) as Record<string, unknown>;
  const flags = (sliceMeta.flags as string[] | undefined) || undefined;
  const answerPath = resolveAnswerPath(ctx, row);
  const engineFacts = engineFactsFromContext(ctx);
  const evidence =
    (engineFacts.evidence && engineFacts.evidence.length > 0
      ? engineFacts.evidence
      : (sliceMeta.evidence as string[] | undefined)) || undefined;
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
  const dashaTrace = (
    (engineFacts as Record<string, unknown>).dasha_trace ||
    sliceMeta.dasha_trace
  ) as Record<string, unknown> | undefined;
  const skipLlm = ctx.llm_called === false || sliceMeta.skip_llm === true || checks.skip_llm === true;
  const narratorMode = checks.narrator_mode ? String(checks.narrator_mode) : "";
  const chartChars = ctx.sizes?.chart_chars ?? ctx.chart_text?.length ?? 0;
  const rawOnly = typeof (ctx as { raw?: string }).raw === "string";
  const sliceLabel = rawOnly
    ? "raw JSON"
    : String(checks.slice_type || checks.archetype || archetype || "unknown");

  return (
    <details id={id} className="llm-context-panel" open={defaultOpen || undefined}>
      <summary>
        LLM context — {sliceLabel}
        {skipLlm ? " (LLM skipped)" : ""}
        {archetype ? ` · ${archetype}` : ""}
      </summary>
      <div className="llm-context-body">
        {rawOnly ? (
          <pre className="llm-context-pre">{(ctx as { raw: string }).raw}</pre>
        ) : (
          <>
            <EngineTracePanel ctx={ctx} row={row} />

            <div className={`answer-path-banner answer-path-${answerPath.code}`}>
              <strong>Answer path:</strong> {answerPath.label}
              {row.answer_source ? (
                <>
                  {" · "}
                  <code>source={row.answer_source}</code>
                </>
              ) : null}
              {narratorMode ? (
                <>
                  {" · "}
                  <code>narrator={narratorMode}</code>
                </>
              ) : null}
              {ctx.llm_called === false ? (
                <span className="answer-path-note"> — final text from engine template</span>
              ) : ctx.model ? (
                <span className="answer-path-note">
                  {" "}
                  — user-facing text written by <code>{ctx.model}</code>
                </span>
              ) : null}
            </div>

            {(ctx.intent_source === "llm" || ctx.intent_source === "llm_repaired") &&
            ctx.llm_intent ? (
              <div className="llm-understanding-box">
                <p>
                  <LlmUnderstoodOneLine ctx={ctx} />
                </p>
                <p>
                  <strong>Engine selected:</strong>{" "}
                  <code>
                    {ctx.llm_intent.mr_archetype
                      ? `${ctx.llm_intent.mr_archetype} (MR engine)`
                      : ctx.llm_intent.is_timing
                        ? "timing engine"
                        : `${ctx.llm_intent.domain || "general"} (chart → LLM)`}
                  </code>
                  {ctx.llm_intent.confidence != null ? (
                    <span className="answer-path-note">
                      {" "}
                      — domain={ctx.llm_intent.domain}, confidence=
                      {ctx.llm_intent.confidence}
                    </span>
                  ) : null}
                </p>
                <p className="detail-muted">
                  Flow: LLM reads question → picks engine → engine produces facts → LLM
                  writes the human answer.
                </p>
              </div>
            ) : (
              <div className="answer-path-banner">
                <strong>Intent:</strong> <code>regex</code>
                <span className="answer-path-note">
                  {" "}
                  — set ASK_LLM_INTENT=1 to route via LLM
                </span>
              </div>
            )}

            <details open className="engine-facts-panel">
              <summary>Facts sent to LLM (engine output)</summary>
              {!verdict && (!evidence || evidence.length === 0) ? (
                <p className="detail-muted">
                  No structured engine facts — LLM got chart slice / prompt only (direct LLM
                  path).
                </p>
              ) : (
                <div className="engine-facts-box">
                  {archetype ? (
                    <p>
                      <strong>Archetype:</strong> {archetype}
                    </p>
                  ) : null}
                  {verdict ? (
                    <p>
                      <strong>Verdict:</strong> {verdict}
                    </p>
                  ) : null}
                  {dashaTrace && (dashaTrace.current_lords || dashaTrace.next_career_ad) ? (
                    <p>
                      <strong>Dasha check:</strong> current{" "}
                      {fmtCheckValue(dashaTrace.current_lords)}
                      {dashaTrace.current_start || dashaTrace.current_end ? (
                        <>
                          {" "}
                          ({fmtCheckValue(dashaTrace.current_start)} →{" "}
                          {fmtCheckValue(dashaTrace.current_end)})
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
                  {engineFacts.love_score != null || engineFacts.arrange_score != null ? (
                    <p>
                      <strong>Scores:</strong> love={fmtCheckValue(engineFacts.love_score)}, arrange=
                      {fmtCheckValue(engineFacts.arrange_score)}
                      {engineFacts.confidence_ratio != null ? (
                        <>
                          {" "}
                          · ratio={fmtCheckValue(engineFacts.confidence_ratio)}
                        </>
                      ) : null}
                    </p>
                  ) : null}
                  {summary && summary.length > 0 ? (
                    <>
                      <p>
                        <strong>Summary for narrator:</strong>
                      </p>
                      <ul className="llm-check-list">
                        {summary.map((s) => (
                          <li key={s}>{s}</li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                  {evidence && evidence.length > 0 ? (
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
            </details>

            <div className="llm-context-grid">
              <span>
                <strong>Route</strong>
                <br />
                {ctx.route || "—"}
              </span>
              <span>
                <strong>Q type</strong>
                <br />
                {ctx.question_type || "—"}
              </span>
              <span>
                <strong>Model</strong>
                <br />
                {ctx.model || (skipLlm ? "template" : "—")}
              </span>
              <span>
                <strong>Max tokens</strong>
                <br />
                {ctx.max_tokens ?? "—"}
              </span>
            </div>

            {ctx.skip_reason ? (
              <p className="detail-muted">
                <strong>Skip reason:</strong> {ctx.skip_reason}
              </p>
            ) : null}

            {Object.keys(checks).length > 0 ? (
              <details>
                <summary>Checks / routing flags</summary>
                <ul className="llm-check-list">
                  {Object.entries(checks).map(([k, v]) => (
                    <li key={k}>
                      <code>{k}</code>: {fmtCheckValue(v)}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            {flags && flags.length > 0 ? (
              <details>
                <summary>Pre-calculated flags ({flags.length})</summary>
                <ul className="llm-check-list">
                  {flags.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </details>
            ) : null}

            {ctx.chart_text ? (
              <details>
                <summary>
                  Full chart context block ({chartChars.toLocaleString("en-IN")} chars)
                </summary>
                <pre className="llm-context-pre">{ctx.chart_text}</pre>
              </details>
            ) : null}

            {ctx.extra_rules ? (
              <details>
                <summary>Extra prompt rules ({ctx.sizes?.extra_rules_chars ?? 0} chars)</summary>
                <pre className="llm-context-pre">{ctx.extra_rules}</pre>
              </details>
            ) : null}

            {ctx.system_prompt ? (
              <details>
                <summary>
                  Full system prompt ({ctx.sizes?.system_prompt_chars ?? 0} chars)
                </summary>
                <pre className="llm-context-pre">{ctx.system_prompt}</pre>
              </details>
            ) : null}

            {ctx.user_payload ? (
              <details>
                <summary>User message payload</summary>
                <pre className="llm-context-pre">{ctx.user_payload}</pre>
              </details>
            ) : null}
          </>
        )}
      </div>
    </details>
  );
}
