import type { AskLlmContext } from "./api";

function fmtCheckValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "yes" : "no";
  return String(v);
}

export function AskLlmContextPanel({
  ctx,
}: {
  ctx: AskLlmContext | null | undefined;
}) {
  if (!ctx) {
    return <p className="detail-muted">LLM context not logged (old row or no LLM).</p>;
  }

  const checks = ctx.checks || {};
  const flags = (ctx.slice_meta as { flags?: string[] } | undefined)?.flags;
  const chartChars = ctx.sizes?.chart_chars ?? ctx.chart_text?.length ?? 0;

  return (
    <details className="llm-context-panel">
      <summary>
        LLM context — slice: {String(checks.slice_type || "unknown")}
        {ctx.llm_called === false ? " (LLM skipped)" : ""}
      </summary>
      <div className="llm-context-body">
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
            {ctx.model || "—"}
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

        {flags && flags.length > 0 ? (
          <details open>
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
            <summary>Chart context sent to LLM ({chartChars.toLocaleString("en-IN")} chars)</summary>
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
      </div>
    </details>
  );
}
