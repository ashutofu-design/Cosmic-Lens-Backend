import type { AskLlmContext, AskQuestionItem } from "./api";

function fmtCheckValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "yes" : "no";
  return String(v);
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

export function AskLlmContextPanel({ row }: { row: AskQuestionItem }) {
  const ctx = parseAskLlmContext(row);

  if (!ctx) {
    return (
      <details className="llm-context-panel llm-context-missing">
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
  const skipLlm = ctx.llm_called === false || sliceMeta.skip_llm === true || checks.skip_llm === true;
  const narratorMode = checks.narrator_mode ? String(checks.narrator_mode) : "";
  const chartChars = ctx.sizes?.chart_chars ?? ctx.chart_text?.length ?? 0;
  const rawOnly = typeof (ctx as { raw?: string }).raw === "string";
  const sliceLabel = rawOnly
    ? "raw JSON"
    : String(checks.slice_type || checks.archetype || archetype || "unknown");

  return (
    <details className="llm-context-panel" open>
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

            <div className="answer-path-banner">
              <strong>Intent:</strong>{" "}
              <code>{ctx.intent_source === "llm" ? "LLM" : "regex"}</code>
              {ctx.intent_source === "llm" && ctx.llm_intent ? (
                <>
                  {" · "}
                  <code>
                    {ctx.llm_intent.domain}
                    {ctx.llm_intent.mr_archetype ? ` → ${ctx.llm_intent.mr_archetype}` : ""}
                    {ctx.llm_intent.confidence != null
                      ? ` (${ctx.llm_intent.confidence})`
                      : ""}
                  </code>
                </>
              ) : null}
            </div>

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
                        <strong>Evidence ({evidence.length}):</strong>
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
