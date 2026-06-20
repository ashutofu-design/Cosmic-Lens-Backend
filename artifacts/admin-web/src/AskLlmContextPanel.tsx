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
  const evidence = (sliceMeta.evidence as string[] | undefined) || undefined;
  const summary = (sliceMeta.summary as string[] | undefined) || undefined;
  const verdict = sliceMeta.verdict ? String(sliceMeta.verdict) : "";
  const archetype = sliceMeta.archetype ? String(sliceMeta.archetype) : "";
  const skipLlm = sliceMeta.skip_llm === true || checks.skip_llm === true;
  const chartChars = ctx.sizes?.chart_chars ?? ctx.chart_text?.length ?? 0;
  const rawOnly = typeof (ctx as { raw?: string }).raw === "string";
  const sliceLabel = rawOnly
    ? "raw JSON"
    : String(checks.slice_type || checks.archetype || archetype || "unknown");

  return (
    <details className="llm-context-panel" open>
      <summary>
        LLM context — {sliceLabel}
        {ctx.llm_called === false ? " (LLM skipped)" : ""}
        {archetype ? ` · ${archetype}` : ""}
      </summary>
      <div className="llm-context-body">
        {rawOnly ? (
          <pre className="llm-context-pre">{(ctx as { raw: string }).raw}</pre>
        ) : (
          <>
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

            {verdict ? (
              <p className="detail-muted">
                <strong>Engine verdict:</strong> {verdict}
              </p>
            ) : null}

            {ctx.skip_reason ? (
              <p className="detail-muted">
                <strong>Skip reason:</strong> {ctx.skip_reason}
              </p>
            ) : null}

            {Object.keys(checks).length > 0 ? (
              <details open>
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

            {summary && summary.length > 0 ? (
              <details open>
                <summary>Engine summary ({summary.length})</summary>
                <ul className="llm-check-list">
                  {summary.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </details>
            ) : null}

            {evidence && evidence.length > 0 ? (
              <details open>
                <summary>Engine evidence ({evidence.length})</summary>
                <ul className="llm-check-list">
                  {evidence.map((e) => (
                    <li key={e}>{e}</li>
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
              <details open>
                <summary>
                  Chart context sent to LLM ({chartChars.toLocaleString("en-IN")} chars)
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
