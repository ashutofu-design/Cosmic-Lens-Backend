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

export function AskObservabilityDebugger({ row }: { row: AskQuestionItem }) {
  const obs = resolveAskObservability(row);
  const exec = obs.engine_execution || {};
  const evidence = obs.planet_evidence || {};
  const conflict = obs.conflict_resolution || {};
  const scorecard = obs.scorecard || {};
  const scoreEntries = Object.entries(scorecard);

  return (
    <div className="obs-debugger">
      <div className="obs-debugger-header">
        <h3>Developer debugger</h3>
        <p className="detail-muted">
          Full Ask pipeline — DNA → engine → rules → evidence → narrator → answer.
        </p>
      </div>

      {obs.routing_warning ? (
        <div className="obs-routing-warning">{obs.routing_warning}</div>
      ) : null}

      <Section title="1. Question DNA" stars={1}>
        <PipelineList steps={obs.question_dna_pipeline || []} />
      </Section>

      <Section title="2. Engine Execution" stars={5}>
        <div className="obs-subblock">
          <strong>Modules loaded</strong>
          <ul className="obs-checklist">
            {(exec.modules || []).map((m) => (
              <li key={m.module}>
                {m.loaded ? "✅" : "❌"} {m.module}
                {!m.loaded && m.module === "KP" ? " unavailable" : ""}
              </li>
            ))}
          </ul>
        </div>

        <div className="obs-subblock">
          <strong>Rules fired</strong>
          {(exec.fired || []).length === 0 ? (
            <p className="detail-muted">
              No v2 rules saved for this row — re-ask after API deploy for full rule trace.
            </p>
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
        </div>

        {(exec.ignored || []).length > 0 ? (
          <div className="obs-subblock">
            <strong>Rules ignored</strong>
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

        <div className="obs-score-verdict">
          <div>
            <span className="detail-muted">Final score</span>
            <div className="obs-big-value">{exec.final_score ?? "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Verdict</span>
            <div className="obs-big-value">{exec.verdict_level || exec.verdict || "—"}</div>
          </div>
        </div>
      </Section>

      <Section title="3. Planet Evidence" stars={5}>
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

      <Section title="4. Conflict Resolution" stars={3}>
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

      <Section title="5. Scorecard" stars={5}>
        {scoreEntries.length === 0 ? (
          <p className="detail-muted">No scorecard saved for this row.</p>
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

      <Section title="6. Narrator Input (LLM JSON)" stars={5}>
        {obs.narrator_input ? (
          <pre className="obs-json">{JSON.stringify(obs.narrator_input, null, 2)}</pre>
        ) : (
          <p className="detail-muted">
            Not saved — commitment questions asked after API deploy will show ENGINE_JSON here.
          </p>
        )}
      </Section>

      <Section title="7. Narrator Output" stars={4}>
        <pre className="obs-answer-preview">{obs.narrator_output || "—"}</pre>
      </Section>

      <Section title="8. Hallucination Check" stars={5}>
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
                  <td>{h.ok ? "✅" : "❌ Hallucination?"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      <Section title="9. Final Trace" stars={4} defaultOpen={false}>
        <ol className="obs-trace">
          {(obs.final_trace || []).map((step, i) => (
            <li key={step}>
              {step}
              {i < (obs.final_trace || []).length - 1 ? (
                <span className="obs-pipeline-arrow"> ↓</span>
              ) : null}
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}
