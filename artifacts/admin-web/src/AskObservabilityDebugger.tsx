import type { ReactNode } from "react";
import type { AskQuestionItem, AskLlmContext } from "./api";
import { formatInr } from "./api";
import {
  OBS_DEBUGGER_VERSION,
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

function formatLagneshLine(lagnesh: Record<string, unknown> | null | undefined): string {
  if (!lagnesh || !lagnesh.lord) return "—";
  const shadbala = lagnesh.lord_shadbala as { strength_pct?: number } | null | undefined;
  const shadbalaText =
    shadbala?.strength_pct != null ? ` · Shadbala ${shadbala.strength_pct}%` : "";
  return `${lagnesh.lord} → H${lagnesh.lord_house || "?"} · ${lagnesh.lord_sign || "?"} · ${lagnesh.lord_dignity || "?"} · strength ${lagnesh.lord_strength_score ?? "?"}${shadbalaText}${lagnesh.lord_in_dusthana ? " · dusthana" : ""}${lagnesh.lord_retrograde ? " · retrograde" : ""}`;
}

function formatHealthChartFactsSteps(
  facts: import("./askObservability").ObservabilityHealthChartFacts | null | undefined,
  chartLabel: "D1" | "D9",
): { label: string; value: string }[] {
  if (!facts || facts.error) {
    return [{ label: `${chartLabel}`, value: facts?.error || "data missing" }];
  }

  const lagnaLine =
    chartLabel === "D1"
      ? `Lagna ${facts.ascendant || "?"} · Vitality ${facts.vitality_score ?? "?"}/100 (${facts.vitality_risk || "?"})\nLagnesh: ${formatLagneshLine(facts.lagnesh as Record<string, unknown>)}`
      : `Lagna ${facts.ascendant || "?"}\nLagnesh: ${formatLagneshLine(facts.lagnesh as Record<string, unknown>)}`;

  const planets = (facts.planets || []).map((p) => {
    const flags = [p.retrograde ? "R" : "", p.combust ? "combust" : ""].filter(Boolean);
    const strength =
      p.strength_score != null
        ? ` · str ${p.strength_score > 0 ? "+" : ""}${p.strength_score}`
        : "";
    const shadbala =
      p.shadbala?.strength_pct != null ? ` · Shadbala ${p.shadbala.strength_pct}%` : "";
    return `${p.name || "?"}: ${p.sign || "?"} · H${p.house || "?"} · ${p.dignity || "?"}${strength}${shadbala}${flags.length ? ` · ${flags.join(", ")}` : ""}`;
  });

  const healthHouses = (facts.health_houses || []).map((h) => {
    const lord = h.lord_state || {};
    const aspects = (h.aspects_received || [])
      .map((a) => `${a.planet || "?"} H${a.from_house || "?"}`)
      .join(", ");
    return `H${h.house || "?"} ${h.sign || "?"} · lord ${lord.lord || h.lord || "?"} → H${lord.lord_house || "?"}, ${lord.lord_dignity || "?"} · occupants ${(h.occupants || []).join(", ") || "none"}${aspects ? ` · aspects ${aspects}` : ""}`;
  });

  return [
    { label: `${chartLabel} · Lagna + Lagnesh`, value: lagnaLine },
    { label: `${chartLabel} · Planets (9)`, value: planets.join("\n") || "—" },
    { label: `${chartLabel} · Health Houses (6)`, value: healthHouses.join("\n\n") || "—" },
    { label: `${chartLabel} · Afflictions`, value: (facts.afflictions || []).join("\n") || "none" },
  ];
}

function formatHealthEngineExecutionSteps(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack?.schema_version && !pack?.d1) return [];

  const steps: { label: string; value: string }[] = [
    ...formatHealthChartFactsSteps(pack.d1, "D1"),
    ...formatHealthChartFactsSteps(pack.d9, "D9"),
  ];

  const vargottama = (pack.vargottama_details || []).map((row) => {
    const mark = row.vargottama ? "✅" : "—";
    return `${row.planet || "?"}: D1 ${row.d1_sign || "?"} H${row.d1_house || "?"} · D9 ${row.d9_sign || "?"} H${row.d9_house || "?"} ${mark}`;
  });
  steps.push({
    label: "Vargottama",
    value: vargottama.join("\n") || (pack.vargottama_planets || []).join(", ") || "none",
  });

  return steps;
}

function formatHealthD1Steps(
  facts: import("./askObservability").ObservabilityHealthD1Facts | null | undefined,
): { label: string; value: string }[] {
  return formatHealthChartFactsSteps(facts, "D1");
}

function buildEngineExecutionSteps(
  exec: ReturnType<typeof resolveAskObservability>["engine_execution"],
  row?: AskQuestionItem,
  ctx?: AskLlmContext | null,
): { label: string; value: string }[] {
  const healthSteps = formatHealthEngineExecutionSteps(exec?.health_engine_execution);
  if (healthSteps.length || exec?.display_mode === "health_charts" || (row && isHealthAskRow(row, ctx || null, exec))) {
    if (healthSteps.length) {
      return healthSteps;
    }
    return [{
      label: "Health Chart Pack",
      value: `D1 + D9 data abhi load nahi hua. Naya health question pucho ya admin/API deploy check karo (v${OBS_DEBUGGER_VERSION}+).`,
    }];
  }

  const modules = exec?.modules || [];
  const modLines =
    modules.length > 0
      ? modules.map((m) => `${m.loaded ? "✅" : "❌"} ${m.module}`).join("\n")
      : "—";

  const steps: { label: string; value: string }[] = [
    { label: "Modules Loaded", value: modLines },
    { label: "Rules Fired", value: formatRulesFired(exec?.fired || []) },
  ];
  steps.push(...formatHealthD1Steps(exec?.d1_health_facts));

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
  const ctx =
    row.llm_context && typeof row.llm_context === "object"
      ? row.llm_context
      : null;
  const exec = obs.engine_execution || {};
  const evidence = obs.planet_evidence || {};
  const perf = obs.performance || {};
  const trace = obs.final_trace || [];
  const hallSummary = obs.hallucination_summary;
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

      <Section title="2. Engine Execution" stars={5}>
        <p className="detail-muted obs-engine-name">
          {exec.display_mode === "health_charts" || exec.health_engine_execution ? (
            <>
              Health charts: <code>D1 + D9</code>
              {exec.health_engine_execution?.schema_version
                ? ` · ${exec.health_engine_execution.schema_version}`
                : null}
            </>
          ) : (
            <>
              Engine: <code>{exec.engine_name || "—"}</code>
              {exec.engine_version ? ` · v${exec.engine_version}` : null}
            </>
          )}
        </p>
        <PipelineList steps={buildEngineExecutionSteps(exec, row, ctx)} />
      </Section>

      <Section title="3. Rule Decision Table" stars={5}>
        <RuleDecisionTable rows={ruleDecisions} />
      </Section>

      <Section title="4. Planet Evidence" stars={5}>
        <div className="obs-evidence-cols">
          <EvidenceColumn title="Positive" items={evidence.positive || []} icon="✅" />
          <EvidenceColumn title="Negative" items={evidence.negative || []} icon="❌" />
        </div>
      </Section>

      <Section title="5. Hallucination Check" stars={5}>
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

      <Section title="6. Final Trace" stars={4} defaultOpen>
        <PipelineList steps={trace} />
      </Section>
    </div>
  );
}
