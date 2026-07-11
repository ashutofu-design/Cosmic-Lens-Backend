import type { ReactNode } from "react";
import type { AskQuestionItem } from "./api";
import { formatInr } from "./api";
import {
  OBS_DEBUGGER_VERSION,
  orderScorecardEntries,
  resolveAskObservability,
  type ObservabilityEvidence,
  type ObservabilityRule,
  type ObservabilityRuleDecision,
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
          <span className="obs-pipeline-value obs-pipeline-pre">{step.value}</span>
          {i < steps.length - 1 ? <span className="obs-pipeline-arrow">↓</span> : null}
        </li>
      ))}
    </ol>
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
              {e.weight !== 0 ? (
                <span className="obs-weight">{e.weight > 0 ? `+${e.weight}` : e.weight}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatRulesFired(fired: ObservabilityRule[]): string {
  if (!fired.length) {
    return "— (re-open after API deploy + re-ask for COM rules)";
  }
  return fired
    .map((r) => {
      const mark = r.polarity === "negative" ? "❌" : "✅";
      const extra = r.note || r.module || "";
      const weight =
        r.weight != null ? ` (${r.weight > 0 ? "+" : ""}${r.weight})` : "";
      return `${r.rule_id || "?"} ${mark}${extra ? ` — ${extra}` : ""}${weight}`;
    })
    .join("\n");
}

function formatRulesIgnored(ignored: ObservabilityRule[]): string {
  if (!ignored.length) return "";
  return ignored
    .map((r) => `${r.rule_id || "?"}\nReason: ${r.reason || "not applicable"}`)
    .join("\n\n");
}

function buildEngineExecutionSteps(
  exec: ReturnType<typeof resolveAskObservability>["engine_execution"],
): { label: string; value: string }[] {
  const modules = exec?.modules || [];
  const modLines =
    modules.length > 0
      ? modules.map((m) => `${m.loaded ? "✅" : "❌"} ${m.module}`).join("\n")
      : "—";

  const steps: { label: string; value: string }[] = [
    { label: "Modules Loaded", value: modLines },
    { label: "Rules Fired", value: formatRulesFired(exec?.fired || []) },
  ];

  const ignoredText = formatRulesIgnored(exec?.ignored || []);
  if (ignoredText) {
    steps.push({ label: "Rules Ignored", value: ignoredText });
  }

  steps.push(
    { label: "Final Score", value: String(exec?.final_score ?? "—") },
    { label: "Verdict", value: String(exec?.verdict || exec?.verdict_level || "—") },
  );

  return steps;
}

function buildConflictSteps(
  conflict: ReturnType<typeof resolveAskObservability>["conflict_resolution"],
): { label: string; value: string }[] {
  const modules = conflict?.modules || [];
  const steps: { label: string; value: string }[] = [];

  if (modules.length) {
    steps.push({
      label: "Module polarity",
      value: modules.map((m) => `${m.module}\n${m.polarity}`).join("\n\n"),
    });
  } else {
    steps.push({ label: "Module polarity", value: "—" });
  }

  steps.push(
    { label: "Conflict", value: conflict?.conflict || conflict?.final_result || "None" },
    { label: "Reason", value: conflict?.reason || "—" },
  );

  return steps;
}

function RuleDecisionTable({ rows }: { rows: ObservabilityRuleDecision[] }) {
  if (!rows.length) {
    return <p className="detail-muted">No rule decision table — re-ask after API deploy.</p>;
  }
  return (
    <div className="obs-rule-decisions">
      {rows.map((row, i) => (
        <div key={`${row.rule_id}-${i}`} className="obs-rule-decision-row">
          <div className="obs-rule-decision-head">
            <code>{row.rule_id}</code>
            <span
              className={
                row.status === "PASS"
                  ? "obs-rule-pass"
                  : row.status === "FAIL"
                    ? "obs-rule-fail"
                    : "obs-rule-skip"
              }
            >
              {row.status}
              {row.weight != null && row.status !== "SKIP" ? ` ${row.weight > 0 ? "+" : ""}${row.weight}` : ""}
            </span>
          </div>
          <p className="detail-muted obs-rule-reason">{row.reason || "—"}</p>
        </div>
      ))}
    </div>
  );
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
  const perf = obs.performance || {};
  const trace = obs.final_trace || [];
  const hallSummary = obs.hallucination_summary;
  const health = obs.engine_health || {};
  const ruleDecisions = obs.rule_decisions || [];

  return (
    <div className="obs-debugger">
      <div className="obs-debugger-header">
        <div className="obs-debugger-title-row">
          <h3>Developer debugger</h3>
          <span className="obs-version-badge">v{OBS_DEBUGGER_VERSION}</span>
        </div>
        <p className="detail-muted">
          Question → DNA → Routing → Modules → Rules → Evidence → Score → Verdict → Narrator → Answer
        </p>
        <p className="obs-telemetry detail-muted">
          {perf.model || row.llm_model ? `Model ${perf.model || row.llm_model}` : null}
          {row.total_tokens != null
            ? ` · ${(perf.prompt_tokens ?? row.prompt_tokens ?? 0).toLocaleString("en-IN")} in / ${(perf.completion_tokens ?? row.completion_tokens ?? 0).toLocaleString("en-IN")} out`
            : null}
          {row.cost_inr != null ? ` · ${formatInr(row.cost_inr)}` : null}
          {perf.response_time_ms != null || exec.execution_time_ms != null
            ? ` · ${formatMs(perf.response_time_ms ?? exec.execution_time_ms)}`
            : null}
        </p>
      </div>

      {obs.routing_warning ? (
        <div className="obs-routing-warning">{obs.routing_warning}</div>
      ) : null}

      {!obs.has_v2_rules && !obs.has_step_audit ? (
        <div className="obs-routing-warning obs-legacy-hint">
          Limited audit on this row. Open detail after deploy — admin re-runs engine from kundli when
          chart is available. For full COM rules, re-ask the question in app.
        </div>
      ) : null}

      <Section title="1. Question DNA" stars={1}>
        <p className="detail-muted" style={{ marginBottom: 8 }}>
          Same classifier fields as mobile DNA Check (Normalized → Bucket Match).
        </p>
        <PipelineList steps={obs.question_dna_pipeline || []} />
      </Section>

      <Section title="2. Engine Health" stars={5}>
        <div className="obs-health-grid">
          <div>
            <span className="detail-muted">Modules loaded</span>
            <div className="obs-big-value obs-big-value-sm">{health.modules_loaded || "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Rules evaluated</span>
            <div className="obs-big-value obs-big-value-sm">{health.rules_evaluated ?? "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Rules fired</span>
            <div className="obs-big-value obs-big-value-sm">{health.rules_fired ?? "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Skipped</span>
            <div className="obs-big-value obs-big-value-sm">{health.rules_skipped ?? "—"}</div>
          </div>
          <div>
            <span className="detail-muted">Confidence</span>
            <div className="obs-big-value obs-big-value-sm">
              {health.confidence_pct != null ? `${health.confidence_pct}%` : "—"}
            </div>
          </div>
          <div>
            <span className="detail-muted">Execution</span>
            <div className="obs-big-value obs-big-value-sm">
              {formatMs(health.execution_ms ?? exec.execution_time_ms)}
            </div>
          </div>
        </div>
      </Section>

      <Section title="3. Engine Execution" stars={5}>
        <p className="detail-muted obs-engine-name">
          Engine: <code>{exec.engine_name || "—"}</code>
          {exec.engine_version ? ` · v${exec.engine_version}` : null}
        </p>
        <PipelineList steps={buildEngineExecutionSteps(exec)} />
      </Section>

      <Section title="4. Rule Decision Table" stars={5}>
        <RuleDecisionTable rows={ruleDecisions} />
      </Section>

      <Section title="5. Planet Evidence" stars={5}>
        <div className="obs-evidence-cols">
          <EvidenceColumn title="Positive" items={evidence.positive || []} icon="✅" />
          <EvidenceColumn title="Negative" items={evidence.negative || []} icon="❌" />
        </div>
      </Section>

      <Section title="6. Conflict Resolution" stars={3}>
        <PipelineList steps={buildConflictSteps(conflict)} />
      </Section>

      <Section title="7. Scorecard" stars={5}>
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

      <Section title="8. Narrator Input" stars={5}>
        {obs.narrator_input ? (
          <pre className="obs-json">{JSON.stringify(obs.narrator_input, null, 2)}</pre>
        ) : (
          <p className="detail-muted">Not saved — exact JSON sent to LLM missing.</p>
        )}
      </Section>

      <Section title="9. Narrator Output">
        <pre className="obs-answer-preview">{obs.narrator_output || row.answer_text || "—"}</pre>
      </Section>

      <Section title="10. Hallucination Check" stars={5}>
        {hallSummary ? (
          <ul className="obs-hallucination-summary">
            <li className={hallSummary.engine_facts_used?.ok ? "obs-ok" : "obs-bad"}>
              Engine facts used {hallSummary.engine_facts_used?.ok ? "✅" : "❌"}
              {hallSummary.engine_facts_used?.detail ? (
                <span className="detail-muted"> — {hallSummary.engine_facts_used.detail}</span>
              ) : null}
            </li>
            <li className={hallSummary.unused_engine_evidence?.ok ? "obs-ok" : "obs-bad"}>
              Unused engine evidence {hallSummary.unused_engine_evidence?.ok ? "✅" : "❌"}
              {(hallSummary.unused_engine_evidence?.items || []).map((item) => (
                <span key={item} className="obs-hallucination-chip">
                  {item}
                </span>
              ))}
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
          <p className="detail-muted">No field-level mismatches detected.</p>
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
                  <td>{h.ok ? "✅" : "❌ Hallucination"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      <Section title="11. Final Trace" stars={4} defaultOpen>
        <PipelineList steps={trace} />
      </Section>
    </div>
  );
}
