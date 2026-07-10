import type { ReactNode } from "react";
import type { AskQuestionItem } from "./api";
import { resolveAskObservability } from "./askObservability";

function Section({
  title,
  stars,
  children,
  defaultOpen = true,
}: {
  title: string;
  stars?: number;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="obs-section" open={defaultOpen}>
      <summary>
        <span className="obs-section-title">
          {title}
          {stars ? <span className="obs-stars">{"★".repeat(stars)}</span> : null}
        </span>
      </summary>
      <div className="obs-section-body">{children}</div>
    </details>
  );
}

function PipelineList({ steps }: { steps: { label: string; value: string }[] }) {
  return (
    <ol className="obs-pipeline">
      {steps.map((step, i) => (
        <li key={`${step.label}-${i}`}>
          <span className="obs-pipeline-label">{step.label}</span>
          <span className="obs-pipeline-value">{step.value}</span>
          {i < steps.length - 1 ? <span className="obs-pipeline-arrow">↓</span> : null}
        </li>
      ))}
    </ol>
  );
}

function AstroChecks({
  checks,
}: {
  checks: Record<string, string[]>;
}) {
  const entries = Object.entries(checks || {}).filter(([, lines]) => lines.length > 0);
  if (entries.length === 0) {
    return (
      <p className="detail-muted">
        No per-module checks saved — re-ask after API deploy for full astrology audit.
      </p>
    );
  }
  return (
    <div className="obs-astro-checks">
      {entries.map(([mod, lines]) => (
        <div key={mod} className="obs-subblock">
          <strong>{mod.toUpperCase()}</strong>
          <ul className="obs-rules-list">
            {lines.map((line, i) => (
              <li key={`${mod}-${i}`}>{line}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function AskObservabilityDebugger({ row }: { row: AskQuestionItem }) {
  const obs = resolveAskObservability(row);
  const exec = obs.engine_execution || {};
  const evidence = obs.planet_evidence || {};
  const conflict = obs.conflict_resolution || {};
  const scorecard = obs.scorecard || {};
  const scoreEntries = Object.entries(scorecard);
  const routing = obs.routing_decision || {};
  const engineVerdict = obs.engine_verdict || {};
  const astro = obs.astrology_checks || {};
  const perf = obs.performance || {};
  const trace = obs.final_trace || [];

  return (
    <div className="obs-debugger">
      <div className="obs-debugger-header">
        <h3>Answer Details — Developer debugger</h3>
        <p className="detail-muted">
          Production pipeline: Question → DNA → Routing → Engine → Rules → Evidence → Narrator → Answer
        </p>
      </div>

      {obs.routing_warning || routing.routing_warning ? (
        <div className="obs-routing-warning">
          {obs.routing_warning || routing.routing_warning}
        </div>
      ) : null}

      <Section title="1. User Question">
        <PipelineList steps={obs.user_question || []} />
      </Section>

      <Section title="2. Question DNA" stars={1}>
        <PipelineList steps={obs.question_dna_pipeline || []} />
      </Section>

      <Section title="3. Routing Decision">
        <p>
          <strong>Selected:</strong> {routing.selected_engine || "—"}
        </p>
        <p className="detail-muted">{routing.why_selected || "—"}</p>
        {(routing.rejected_engines || []).length > 0 ? (
          <div className="obs-subblock">
            <strong>Rejected / overridden</strong>
            <ul className="obs-rules-list">
              {(routing.rejected_engines || []).map((r, i) => (
                <li key={`rej-${i}`}>{r}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section title="4. Engine Execution" stars={1}>
        <p>
          <strong>Engine:</strong> {exec.engine_name || routing.selected_engine || "—"}
          {exec.engine_version ? (
            <span className="detail-muted"> · v{exec.engine_version}</span>
          ) : null}
        </p>
        <div className="obs-subblock">
          <strong>Modules loaded</strong>
          <ul className="obs-checklist">
            {(exec.modules || []).map((m) => (
              <li key={m.module}>
                {m.loaded ? "✅" : "❌"} {m.module}
              </li>
            ))}
          </ul>
        </div>
      </Section>

      <Section title="5. Astrology Checks" stars={3}>
        <AstroChecks checks={astro} />
      </Section>

      <Section title="6. Rules Fired" stars={5}>
        {(exec.fired || []).length === 0 ? (
          <p className="detail-muted">No v2 rules saved for this row.</p>
        ) : (
          <ul className="obs-rules-list">
            {(exec.fired || []).map((r, i) => (
              <li key={`${r.rule_id}-${i}`}>
                <code>{r.rule_id}</code>{" "}
                {r.polarity === "negative" ? "❌" : "✅"}{" "}
                {r.note || r.module}
                {r.weight != null ? ` (${r.weight > 0 ? "+" : ""}${r.weight})` : ""}
              </li>
            ))}
          </ul>
        )}
        {(exec.ignored || []).length > 0 ? (
          <div className="obs-subblock">
            <strong>Rules skipped</strong>
            <ul className="obs-rules-list">
              {(exec.ignored || []).map((r, i) => (
                <li key={`${r.rule_id}-${i}`}>
                  <code>{r.rule_id}</code>
                  {r.reason ? <span className="detail-muted"> — {r.reason}</span> : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section title="7. Planet Evidence" stars={5}>
        <div className="obs-evidence-cols">
          <div>
            <strong>Positive</strong>
            <ul className="obs-evidence-list">
              {(evidence.positive || []).map((e, i) => (
                <li key={`p-${i}`}>
                  ✅ {e.label}
                  <span className="obs-weight">{e.weight > 0 ? `+${e.weight}` : e.weight}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <strong>Negative</strong>
            <ul className="obs-evidence-list">
              {(evidence.negative || []).map((e, i) => (
                <li key={`n-${i}`}>
                  ❌ {e.label}
                  <span className="obs-weight">{e.weight}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Section>

      <Section title="8. Conflict Resolution" stars={3}>
        <ul className="obs-conflict-modules">
          {(conflict.modules || []).map((m) => (
            <li key={m.module}>
              <strong>{m.module}</strong> — {m.polarity}
            </li>
          ))}
        </ul>
        <p>
          <strong>Conflict:</strong> {conflict.conflict || "None"}
        </p>
        <p className="detail-muted">{conflict.reason || "—"}</p>
      </Section>

      <Section title="9. Scorecard" stars={5}>
        {scoreEntries.length === 0 ? (
          <p className="detail-muted">No scorecard saved.</p>
        ) : (
          <div className="obs-scorecard-grid">
            {scoreEntries.map(([k, v]) => (
              <div key={k} className="obs-scorecard-item">
                <span className="detail-muted">{k}</span>
                <span className="obs-scorecard-value">{v}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="10. Final Engine Verdict" stars={4}>
        <div className="obs-score-verdict">
          <div>
            <span className="detail-muted">Verdict</span>
            <div className="obs-big-value">{engineVerdict.verdict || exec.verdict || "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Level</span>
            <div className="obs-big-value">{engineVerdict.level || exec.verdict_level || "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Confidence</span>
            <div className="obs-big-value">{engineVerdict.confidence ?? exec.final_score ?? "—"}</div>
          </div>
        </div>
      </Section>

      <Section title="11. Narrator Input (LLM JSON)" stars={5}>
        {obs.narrator_input ? (
          <pre className="obs-json">{JSON.stringify(obs.narrator_input, null, 2)}</pre>
        ) : (
          <p className="detail-muted">Not saved — commitment questions after deploy show ENGINE_JSON.</p>
        )}
      </Section>

      <Section title="12. Narrator Output" stars={4}>
        <pre className="obs-answer-preview">{obs.narrator_output || "—"}</pre>
      </Section>

      <Section title="13. Hallucination Check" stars={5}>
        {(obs.hallucination_checks || []).length === 0 ? (
          <p className="detail-muted">No mismatches detected (or insufficient engine data).</p>
        ) : (
          <table className="obs-hallucination-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Engine</th>
                <th>Narrator</th>
                <th>OK?</th>
              </tr>
            </thead>
            <tbody>
              {(obs.hallucination_checks || []).map((h) => (
                <tr key={h.field} className={h.ok ? "obs-ok" : "obs-bad"}>
                  <td>{h.field}</td>
                  <td>{h.engine}</td>
                  <td>{h.narrator}</td>
                  <td>{h.ok ? "✅" : "❌"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      <Section title="14. Performance" stars={2} defaultOpen={false}>
        <PipelineList
          steps={[
            { label: "Model", value: String(perf.model || row.llm_model || "—") },
            { label: "Max tokens", value: String(perf.max_tokens ?? "—") },
            { label: "LLM called", value: perf.llm_called === false ? "no" : "yes" },
            { label: "Prompt chars", value: String(perf.system_prompt_chars ?? "—") },
            { label: "Tokens (row)", value: row.total_tokens != null ? String(row.total_tokens) : "—" },
            { label: "Cost INR", value: row.cost_inr != null ? String(row.cost_inr) : "—" },
          ]}
        />
      </Section>

      <Section title="15. Final Trace" stars={4} defaultOpen={false}>
        <PipelineList steps={trace} />
      </Section>
    </div>
  );
}
