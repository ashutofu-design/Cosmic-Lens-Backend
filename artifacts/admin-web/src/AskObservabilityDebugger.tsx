import type { ReactNode } from "react";
import type { AskQuestionItem } from "./api";
import { formatInr } from "./api";
import {
  ASTRO_MODULE_LABELS,
  orderScorecardEntries,
  resolveAskObservability,
  type ObservabilityEvidence,
} from "./askObservability";

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

function AstroChecks({ checks }: { checks: Record<string, string[]> }) {
  const preferredOrder = ["d1", "d9", "dasha", "transit", "kp", "ashtakavarga", "jaimini", "bcp"];
  const entries = Object.entries(checks || {}).filter(([, lines]) => lines.length > 0);
  entries.sort(([a], [b]) => {
    const ai = preferredOrder.indexOf(a.toLowerCase());
    const bi = preferredOrder.indexOf(b.toLowerCase());
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

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
          <strong>{ASTRO_MODULE_LABELS[mod.toLowerCase()] || `${mod.toUpperCase()} — what was checked`}</strong>
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

function EvidenceColumn({
  title,
  items,
  icon,
}: {
  title: string;
  items: ObservabilityEvidence[];
  icon: string;
}) {
  return (
    <div>
      <strong>{title}</strong>
      {items.length === 0 ? (
        <p className="detail-muted">—</p>
      ) : (
        <ul className="obs-evidence-list">
          {items.map((e, i) => (
            <li key={`${title}-${i}`}>
              <span>
                {icon} {e.label}
              </span>
              {e.weight !== 0 ? <span className="obs-weight">{e.weight > 0 ? `+${e.weight}` : e.weight}</span> : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatFactorList(items: (string | ObservabilityEvidence)[] | undefined): string[] {
  if (!items?.length) return [];
  return items.map((item) => {
    if (typeof item === "string") return item;
    return item.label || "—";
  });
}

function formatMs(ms: number | null | undefined): string {
  if (ms == null) return "—";
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`;
}

export function AskObservabilityDebugger({ row }: { row: AskQuestionItem }) {
  const obs = resolveAskObservability(row);
  const exec = obs.engine_execution || {};
  const evidence = obs.planet_evidence || {};
  const conflict = obs.conflict_resolution || {};
  const scorecard = obs.scorecard || {};
  const scoreEntries = orderScorecardEntries(scorecard);
  const routing = obs.routing_decision || {};
  const engineVerdict = obs.engine_verdict || {};
  const astro = obs.astrology_checks || {};
  const perf = obs.performance || {};
  const trace = obs.final_trace || [];
  const hallSummary = obs.hallucination_summary;
  const modulesSkipped = exec.modules_skipped || (exec.modules || []).filter((m) => !m.loaded).map((m) => m.module);

  return (
    <div className="obs-debugger">
      <div className="obs-debugger-header">
        <h3>Answer Details</h3>
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
          <strong>Why this engine was selected</strong>
        </p>
        <p>
          <code>{routing.selected_engine || "—"}</code>
        </p>
        <p className="detail-muted">{routing.why_selected || "—"}</p>
        <div className="obs-subblock">
          <strong>Why other engines were rejected</strong>
          {(routing.rejected_engines || []).length > 0 ? (
            <ul className="obs-rules-list">
              {(routing.rejected_engines || []).map((r, i) => (
                <li key={`rej-${i}`}>{r}</li>
              ))}
            </ul>
          ) : (
            <p className="detail-muted">No explicit rejections logged.</p>
          )}
        </div>
      </Section>

      <Section title="4. Engine Execution" stars={1}>
        <p>
          <strong>Engine Name:</strong> {exec.engine_name || routing.selected_engine || "—"}
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
        <div className="obs-subblock">
          <strong>Modules skipped</strong>
          {modulesSkipped.length > 0 ? (
            <ul className="obs-checklist">
              {modulesSkipped.map((mod) => (
                <li key={mod}>⏭ {mod}</li>
              ))}
            </ul>
          ) : (
            <p className="detail-muted">None — all catalog modules ran or N/A.</p>
          )}
        </div>
        <p>
          <strong>Execution time:</strong> {formatMs(exec.execution_time_ms ?? perf.response_time_ms)}
        </p>
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
            <strong>Skip reason</strong>
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
        <div className="obs-evidence-cols obs-evidence-cols-3">
          <EvidenceColumn title="Positive" items={evidence.positive || []} icon="✅" />
          <EvidenceColumn title="Negative" items={evidence.negative || []} icon="❌" />
          <EvidenceColumn title="Neutral" items={evidence.neutral || []} icon="○" />
        </div>
      </Section>

      <Section title="8. Conflict Resolution" stars={3}>
        <div className="obs-conflict-pairs">
          <div>
            <span className="detail-muted">D1 vs D9</span>
            <div>{conflict.d1_vs_d9 || "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Dasha vs Transit</span>
            <div>{conflict.dasha_vs_transit || "—"}</div>
          </div>
        </div>
        <p className="obs-conflict-final">
          <strong>Final conflict result:</strong> {conflict.final_result || conflict.conflict || "—"}
        </p>
        {conflict.reason && conflict.reason !== "—" ? (
          <p className="detail-muted">{conflict.reason}</p>
        ) : null}
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
            <span className="detail-muted">Confidence</span>
            <div className="obs-big-value">{engineVerdict.confidence ?? exec.final_score ?? "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Timing</span>
            <div className="obs-big-value obs-big-value-sm">{engineVerdict.timing || "—"}</div>
          </div>
        </div>
        <div className="obs-subblock">
          <strong>Strongest factors</strong>
          <ul className="obs-rules-list">
            {formatFactorList(engineVerdict.strongest).map((f, i) => (
              <li key={`str-${i}`}>✅ {f}</li>
            ))}
            {formatFactorList(engineVerdict.strongest).length === 0 ? (
              <li className="detail-muted">—</li>
            ) : null}
          </ul>
        </div>
        <div className="obs-subblock">
          <strong>Weakest factors</strong>
          <ul className="obs-rules-list">
            {formatFactorList(engineVerdict.weakest).map((f, i) => (
              <li key={`weak-${i}`}>❌ {f}</li>
            ))}
            {formatFactorList(engineVerdict.weakest).length === 0 ? (
              <li className="detail-muted">—</li>
            ) : null}
          </ul>
        </div>
        {(engineVerdict.warnings || []).length > 0 ? (
          <div className="obs-subblock">
            <strong>Warnings</strong>
            <ul className="obs-rules-list">
              {(engineVerdict.warnings || []).map((w, i) => (
                <li key={`warn-${i}`}>⚠ {w}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      <Section title="11. Narrator Input (LLM JSON)" stars={5}>
        {obs.narrator_input ? (
          <pre className="obs-json">{JSON.stringify(obs.narrator_input, null, 2)}</pre>
        ) : (
          <p className="detail-muted">Not saved — re-ask after deploy to capture exact ENGINE_JSON sent to LLM.</p>
        )}
      </Section>

      <Section title="12. Narrator Output" stars={4}>
        <pre className="obs-answer-preview">{obs.narrator_output || row.answer_text || "—"}</pre>
      </Section>

      <Section title="13. Hallucination Check" stars={5}>
        {hallSummary ? (
          <ul className="obs-hallucination-summary">
            <li className={hallSummary.engine_facts_used?.ok ? "obs-ok" : "obs-bad"}>
              Engine facts used {hallSummary.engine_facts_used?.ok ? "✅" : "❌"}
              {hallSummary.engine_facts_used?.detail ? (
                <span className="detail-muted"> — {hallSummary.engine_facts_used.detail}</span>
              ) : null}
            </li>
            <li className={hallSummary.extra_llm_assumptions?.ok ? "obs-ok" : "obs-bad"}>
              Extra LLM assumptions {hallSummary.extra_llm_assumptions?.ok ? "✅" : "❌"}
              {(hallSummary.extra_llm_assumptions?.items || []).map((item) => (
                <span key={item} className="obs-hallucination-chip">
                  {item}
                </span>
              ))}
            </li>
            <li className={hallSummary.missing_engine_evidence?.ok ? "obs-ok" : "obs-bad"}>
              Missing engine evidence {hallSummary.missing_engine_evidence?.ok ? "✅" : "❌"}
              {(hallSummary.missing_engine_evidence?.items || []).map((item) => (
                <span key={item} className="obs-hallucination-chip">
                  {item}
                </span>
              ))}
            </li>
          </ul>
        ) : null}
        {(obs.hallucination_checks || []).length === 0 ? (
          <p className="detail-muted">No field-level mismatches detected (or insufficient engine data).</p>
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
            {
              label: "Tokens",
              value:
                perf.total_tokens != null || row.total_tokens != null
                  ? `${(perf.prompt_tokens ?? row.prompt_tokens ?? 0).toLocaleString("en-IN")} in · ${(perf.completion_tokens ?? row.completion_tokens ?? 0).toLocaleString("en-IN")} out${(perf.cached_tokens ?? row.cached_tokens) ? ` · ${perf.cached_tokens ?? row.cached_tokens} cached` : ""}`
                  : "—",
            },
            {
              label: "Cost",
              value:
                perf.cost_inr != null || row.cost_inr != null
                  ? `${formatInr(perf.cost_inr ?? row.cost_inr ?? 0)}${perf.cost_usd != null || row.cost_usd != null ? ` ($${(perf.cost_usd ?? row.cost_usd ?? 0).toFixed(4)})` : ""}`
                  : "—",
            },
            {
              label: "Response time",
              value: formatMs(perf.response_time_ms ?? exec.execution_time_ms),
            },
            {
              label: "Cache",
              value:
                perf.cache_hit === true || (perf.cached_tokens ?? row.cached_tokens)
                  ? "Hit"
                  : perf.cache_hit === false || perf.total_tokens || row.total_tokens
                    ? "Miss"
                    : "—",
            },
            { label: "Model", value: String(perf.model || row.llm_model || "—") },
            { label: "LLM called", value: perf.llm_called === false ? "no" : "yes" },
          ]}
        />
      </Section>

      <Section title="15. Final Trace" stars={4} defaultOpen={false}>
        <PipelineList steps={trace} />
      </Section>
    </div>
  );
}
