import type { ReactNode } from "react";
import type { AskQuestionItem, AskLlmContext } from "./api";
import { formatInr } from "./api";
import {
  OBS_DEBUGGER_VERSION,
  resolveAskObservability,
  isHealthAskRow,
  type ObservabilityHealthSelectedBlocks,
  type ObservabilityRule,
} from "./askObservability";

function Section({
  title,
  stars,
  children,
  defaultOpen = true,
  className,
}: {
  title: string;
  stars?: number;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}) {
  return (
    <details className={`obs-section${className ? ` ${className}` : ""}`} open={defaultOpen}>
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

function DnaComplianceBox({
  steps,
  summary,
}: {
  steps: { label: string; value: string; followed?: boolean; follow_reason?: string }[];
  summary?: import("./askObservability").ObservabilityDnaFollowedSummary | null;
}) {
  const total = summary?.total ?? steps.length;
  const followed = summary?.followed_count ?? steps.filter((s) => s.followed === true).length;
  const pct = summary?.pct ?? (total ? Math.round((100 * followed) / total) : 0);
  const allOk = total > 0 && followed === total;

  return (
    <div className="obs-dna-box">
      <div className="obs-dna-box-header">
        <span className="obs-dna-box-title">Question DNA</span>
        <span className={`obs-dna-followed-badge ${allOk ? "obs-dna-followed-ok" : "obs-dna-followed-partial"}`}>
          Followed {followed}/{total} · {pct}%
        </span>
      </div>
      <table className="obs-dna-table">
        <tbody>
          {steps.map((step, i) => (
            <tr
              key={`${step.label}-${i}`}
              className={step.followed === false ? "obs-dna-row-fail" : undefined}
              title={step.follow_reason || undefined}
            >
              <th scope="row">
                <span className="obs-dna-tick" aria-hidden>
                  {step.followed === true ? "✅" : step.followed === false ? "❌" : "·"}
                </span>
                {step.label}
              </th>
              <td>{step.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
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

function formatHouseRows(
  rows: NonNullable<import("./askObservability").ObservabilityHealthChartFacts["health_houses"]>,
): string {
  return rows
    .map((h) => {
      const lord = h.lord_state || {};
      const aspects = (h.aspects_received || [])
        .map((a) => `${a.planet || "?"} H${a.from_house || "?"}`)
        .join(", ");
      return `H${h.house || "?"} ${h.sign || "?"} · lord ${lord.lord || h.lord || "?"} → H${lord.lord_house || "?"}, ${lord.lord_dignity || "?"} · occupants ${(h.occupants || []).join(", ") || "none"}${aspects ? ` · aspects ${aspects}` : ""}`;
    })
    .join("\n\n");
}

function formatHealthChartFactsSteps(
  facts: import("./askObservability").ObservabilityHealthChartFacts | null | undefined,
  chartLabel: "D1" | "D9",
  opts?: { domain?: "health" | "relationship" | "finance" | "travel" },
): { label: string; value: string }[] {
  if (!facts || facts.error) {
    return [{ label: `${chartLabel}`, value: facts?.error || "data missing" }];
  }

  const domain = opts?.domain || "health";
  const lagnaLine =
    chartLabel === "D1" && domain === "health"
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

  const anyFacts = facts as Record<string, unknown>;
  const houseRows =
    domain === "relationship"
      ? facts.relationship_houses || facts.health_houses || []
      : domain === "finance"
        ? facts.finance_houses || facts.health_houses || []
        : domain === "travel"
          ? (anyFacts.travel_houses as typeof facts.health_houses) || facts.health_houses || []
          : domain === "domain"
            ? (anyFacts.domain_houses as typeof facts.health_houses) || facts.health_houses || []
            : facts.health_houses || [];
  const houseLabel =
    domain === "relationship"
      ? `${chartLabel} · Relationship Houses`
      : domain === "finance"
        ? `${chartLabel} · Finance Houses`
        : domain === "travel"
          ? `${chartLabel} · Travel Houses (3/4/7/9/12)`
          : domain === "domain"
            ? `${chartLabel} · Focus Houses`
            : `${chartLabel} · Health Houses (6)`;

  return [
    { label: `${chartLabel} · Lagna + Lagnesh`, value: lagnaLine },
    { label: `${chartLabel} · Planets (9)`, value: planets.join("\n") || "—" },
    { label: houseLabel, value: formatHouseRows(houseRows) || "—" },
    { label: `${chartLabel} · Afflictions`, value: (facts.afflictions || []).join("\n") || "none" },
  ];
}

function formatDashaTimingCompactSteps(
  pack: import("./askObservability").ObservabilityHealthEngineExecution["dasha_timing_compact"] | null | undefined,
): { label: string; value: string }[] {
  if (!pack || pack.error) {
    return pack?.error
      ? [{ label: "Timing Dasha Compact", value: pack.error }]
      : [];
  }
  if (!pack.current && !(pack.top_windows || []).length) {
    return [];
  }
  const cur = pack.current;
  const currentLine = cur
    ? `MD ${cur.md || "?"} / AD ${cur.ad || "?"} / PD ${cur.pd || "?"}`
      + (cur.window ? `\n${cur.window}` : "")
      + (cur.why ? `\n${cur.why}` : "")
    : "—";
  const windows = (pack.top_windows || []).map((w, i) => {
    const score = w.score != null ? ` · score ${w.score}` : "";
    return `#${i + 1} ${w.role || "window"}: MD ${w.md || "?"} / AD ${w.ad || "?"} / PD ${w.pd || "?"}`
      + (w.window ? `\n${w.window}` : "")
      + score
      + (w.why ? `\n${w.why}` : "");
  });
  return [
    {
      label: "Timing Dasha Compact",
      value:
        `horizon ${pack.horizon_years ?? "?"}y · top ${pack.max_windows ?? (pack.top_windows || []).length}`
        + (pack.schema_version ? ` · ${pack.schema_version}` : ""),
    },
    { label: "Current MD/AD/PD", value: currentLine },
    { label: "Top Windows", value: windows.join("\n\n") || "—" },
  ];
}

function formatRelationshipPackExtras(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack) return [];
  const steps: { label: string; value: string }[] = [];
  const manglik = pack.manglik;
  if (manglik && typeof manglik === "object") {
    const yes = manglik.is_manglik === true ? "Yes" : manglik.is_manglik === false ? "No" : "?";
    steps.push({
      label: "Manglik",
      value:
        `${yes}`
        + (manglik.mars_house != null ? ` · Mars H${manglik.mars_house}` : "")
        + (Array.isArray(manglik.classic_houses)
          ? ` · classic houses ${(manglik.classic_houses as number[]).join(",")}`
          : ""),
    });
  }
  const signals = pack.relationship_signals;
  if (signals && typeof signals === "object" && !signals.error) {
    const flagKeys = [
      "venus_debil",
      "moon_debil",
      "seventh_lord_dusthana",
      "saturn_on_7th",
      "mars_on_7th",
      "rahu_on_7th_axis",
      "loyalty_risk_high",
      "separation_yoga",
      "reconnection_yoga",
      "third_person_risk",
    ];
    const on = flagKeys.filter((k) => signals[k] === true);
    const notes = Array.isArray(signals.notes)
      ? (signals.notes as unknown[]).slice(0, 6).map(String)
      : [];
    steps.push({
      label: "Relationship Signals",
      value:
        (on.length ? `ON: ${on.join(", ")}` : "no key risk flags ON")
        + (notes.length ? `\n${notes.join("\n")}` : ""),
    });
  } else if (signals && typeof signals === "object" && signals.error) {
    steps.push({ label: "Relationship Signals", value: String(signals.error) });
  }
  return steps;
}

function formatFinancePackExtras(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack) return [];
  const steps: { label: string; value: string }[] = [];
  const dims =
    pack.dimensions ||
    pack.d1?.dimensions ||
    null;
  if (dims && typeof dims === "object") {
    const lines = Object.entries(dims).map(([key, val]) => {
      const row = (val || {}) as {
        verdict?: string;
        reason?: string;
        tier?: string;
        score?: number;
      };
      const score = row.score != null ? ` · score ${row.score}` : "";
      const tier = row.tier ? ` · ${row.tier}` : "";
      const reason = row.reason ? `\n  ${row.reason}` : "";
      return `${key}: ${row.verdict || "?"}${tier}${score}${reason}`;
    });
    steps.push({
      label: "Dimensions",
      value: lines.join("\n") || "—",
    });
  }
  const yogas = pack.wealth_yogas || pack.d1?.wealth_yogas || [];
  if (yogas.length) {
    steps.push({ label: "Wealth Yogas", value: yogas.join(", ") });
  } else {
    steps.push({ label: "Wealth Yogas", value: "none" });
  }
  return steps;
}

function formatTravelPackExtras(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack) return [];
  const steps: { label: string; value: string }[] = [];
  const dims =
    pack.dimensions ||
    pack.d1?.dimensions ||
    null;
  if (dims && typeof dims === "object") {
    const lines = Object.entries(dims).map(([key, val]) => {
      const row = (val || {}) as {
        verdict?: string;
        reason?: string;
        tier?: string;
        score?: number;
      };
      const score = row.score != null ? ` · score ${row.score}` : "";
      const tier = row.tier ? ` · ${row.tier}` : "";
      const reason = row.reason ? `\n  ${row.reason}` : "";
      return `${key}: ${row.verdict || "?"}${tier}${score}${reason}`;
    });
    steps.push({
      label: "Dimensions",
      value: lines.join("\n") || "—",
    });
  }
  const anyPack = pack as Record<string, unknown>;
  const d1 = (pack.d1 || {}) as Record<string, unknown>;
  const yogas = (anyPack.travel_yogas as string[] | undefined)
    || (d1.travel_yogas as string[] | undefined)
    || [];
  steps.push({
    label: "Travel Yogas",
    value: yogas.length ? yogas.join(", ") : "none",
  });
  const score = anyPack.composite_score ?? d1.composite_score;
  const label = anyPack.strength_label ?? d1.strength_label;
  if (score != null || label) {
    steps.push({
      label: "Travel Strength",
      value: `${score != null ? `${score}/100` : "—"} — ${label || ""}`.trim(),
    });
  }
  return steps;
}

function formatDomainPackExtras(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack) return [];
  const steps: { label: string; value: string }[] = [];
  const dims = pack.dimensions || pack.d1?.dimensions || null;
  if (dims && typeof dims === "object") {
    const lines = Object.entries(dims).map(([key, val]) => {
      const row = (val || {}) as {
        verdict?: string;
        reason?: string;
        tier?: string;
        score?: number;
      };
      const score = row.score != null ? ` · score ${row.score}` : "";
      const tier = row.tier ? ` · ${row.tier}` : "";
      const reason = row.reason ? `\n  ${row.reason}` : "";
      return `${key}: ${row.verdict || "?"}${tier}${score}${reason}`;
    });
    steps.push({ label: "Dimensions", value: lines.join("\n") || "—" });
  }
  const anyPack = pack as Record<string, unknown>;
  const d1 = (pack.d1 || {}) as Record<string, unknown>;
  const yogas = (anyPack.yogas as string[] | undefined)
    || (d1.yogas as string[] | undefined)
    || [];
  steps.push({ label: "Yogas", value: yogas.length ? yogas.join(", ") : "none" });
  const score = anyPack.composite_score ?? d1.composite_score;
  const label = anyPack.strength_label ?? d1.strength_label;
  if (score != null || label) {
    steps.push({
      label: "Theme Strength",
      value: `${score != null ? `${score}/100` : "—"} — ${label || ""}`.trim(),
    });
  }
  return steps;
}

function formatModulesCheckedSteps(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
): { label: string; value: string }[] {
  if (!pack) return [];
  const rows = pack.modules_checked;
  const fmt = (r: import("./askObservability").ObservabilityModuleChecked) => {
    const mod = String(r.module || "?").toUpperCase();
    const used = r.llm_used ?? r.checked;
    const loaded = r.engine_loaded !== false;
    if (!loaded) return `${mod} ❌ not loaded — ${r.reason || "engine missing"}`;
    if (used) return `${mod} ✅ LLM used — ${r.reason || "cited in answer"}`;
    return `${mod} ❌ not in answer — ${r.reason || "engine loaded but LLM skipped"}`;
  };
  if (Array.isArray(rows) && rows.length) {
    return [{
      label: "Chart modules (LLM used)",
      value: rows.map(fmt).join("\n"),
    }];
  }
  const d1Loaded = pack.d1_engine_loaded ?? Boolean(pack.d1 && !pack.d1.error);
  const d9Loaded = pack.d9_engine_loaded ?? Boolean(pack.d9 && !pack.d9.error);
  const d1Ok = pack.d1_checked === true;
  const d9Ok = pack.d9_checked === true;
  return [{
    label: "Chart modules (LLM used)",
    value: [
      `D1 ${d1Ok ? "✅ LLM used" : "❌ not in answer"}${d1Loaded ? "" : " (not loaded)"}`,
      `D9 ${d9Ok ? "✅ LLM used" : "❌ not in answer"}${d9Loaded ? "" : " (not loaded)"}`,
    ].join("\n"),
  }];
}

function resolveActiveEnginePack(
  exec: ReturnType<typeof resolveAskObservability>["engine_execution"],
): import("./askObservability").ObservabilityHealthEngineExecution | null | undefined {
  return (
    exec?.health_engine_execution
    || exec?.relationship_engine_execution
    || exec?.finance_engine_execution
    || exec?.travel_engine_execution
    || (exec as { general_chart_engine_execution?: import("./askObservability").ObservabilityHealthEngineExecution | null })
      .general_chart_engine_execution
    || exec?.domain_engine_execution
    || null
  );
}

function EngineModuleBadges({
  pack,
}: {
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined;
}) {
  if (!pack) return null;
  const rows = pack.modules_checked;
  const badges =
    Array.isArray(rows) && rows.length
      ? rows
      : [
          {
            module: "D1",
            llm_used: pack.d1_checked,
            engine_loaded: pack.d1_engine_loaded ?? Boolean(pack.d1 && !pack.d1.error),
            reason: "D1",
          },
          {
            module: "D9",
            llm_used: pack.d9_checked,
            engine_loaded: pack.d9_engine_loaded ?? Boolean(pack.d9 && !pack.d9.error),
            reason: "D9",
          },
        ];
  return (
    <span className="obs-module-badges">
      {badges.map((r) => {
        const used = r.llm_used ?? r.checked;
        const loaded = r.engine_loaded !== false;
        const title = r.reason || (used ? "LLM used in answer" : loaded ? "Loaded but not cited" : "Not loaded");
        return (
          <span
            key={String(r.module || "?")}
            title={title}
            className={
              used
                ? "obs-module-badge obs-module-ok"
                : loaded
                  ? "obs-module-badge obs-module-skip"
                  : "obs-module-badge obs-module-miss"
            }
          >
            {String(r.module || "?").toUpperCase()} {used ? "✅" : "❌"}
          </span>
        );
      })}
    </span>
  );
}

function formatHealthEngineExecutionSteps(
  pack: import("./askObservability").ObservabilityHealthEngineExecution | null | undefined,
  opts?: { domain?: "health" | "relationship" | "finance" | "travel" | "domain" },
): { label: string; value: string }[] {
  if (!pack?.schema_version && !pack?.d1) return [];
  const domain = opts?.domain || "health";

  const steps: { label: string; value: string }[] = [
    ...formatModulesCheckedSteps(pack),
    ...formatHealthChartFactsSteps(pack.d1, "D1", { domain }),
    ...formatHealthChartFactsSteps(pack.d9, "D9", { domain }),
  ];

  const vargottama = (pack.vargottama_details || []).map((row) => {
    const mark = row.vargottama ? "✅" : "—";
    return `${row.planet || "?"}: D1 ${row.d1_sign || "?"} H${row.d1_house || "?"} · D9 ${row.d9_sign || "?"} H${row.d9_house || "?"} ${mark}`;
  });
  steps.push({
    label: "Vargottama",
    value: vargottama.join("\n") || (pack.vargottama_planets || []).join(", ") || "none",
  });
  if (domain === "relationship") {
    steps.push(...formatRelationshipPackExtras(pack));
  }
  if (domain === "finance") {
    steps.push(...formatFinancePackExtras(pack));
  }
  if (domain === "travel") {
    steps.push(...formatTravelPackExtras(pack));
  }
  if (domain === "domain") {
    steps.push(...formatDomainPackExtras(pack));
  }
  steps.push(...formatDashaTimingCompactSteps(pack.dasha_timing_compact));

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

  const relationshipSteps = formatHealthEngineExecutionSteps(exec?.relationship_engine_execution, {
    domain: "relationship",
  });
  if (
    relationshipSteps.length ||
    exec?.display_mode === "relationship_charts" ||
    exec?.relationship_engine_execution
  ) {
    if (relationshipSteps.length) {
      return relationshipSteps;
    }
    return [{
      label: "Relationship Chart Pack",
      value: `D1 + D9 data abhi load nahi hua. Naya relationship question pucho ya admin/API deploy check karo (v${OBS_DEBUGGER_VERSION}+).`,
    }];
  }

  const financeSteps = formatHealthEngineExecutionSteps(exec?.finance_engine_execution, {
    domain: "finance",
  });
  if (
    financeSteps.length ||
    exec?.display_mode === "finance_charts" ||
    exec?.finance_engine_execution
  ) {
    if (financeSteps.length) {
      return financeSteps;
    }
    return [{
      label: "Finance Chart Pack",
      value: `D1 + D9 data abhi load nahi hua. Naya finance question pucho ya admin/API deploy check karo (v${OBS_DEBUGGER_VERSION}+).`,
    }];
  }

  const travelSteps = formatHealthEngineExecutionSteps(exec?.travel_engine_execution, {
    domain: "travel",
  });
  if (
    travelSteps.length ||
    exec?.display_mode === "travel_charts" ||
    exec?.travel_engine_execution
  ) {
    if (travelSteps.length) {
      return travelSteps;
    }
    return [{
      label: "Travel Chart Pack",
      value: `D1 + D9 data abhi load nahi hua. Naya travel question pucho ya admin/API deploy check karo (v${OBS_DEBUGGER_VERSION}+).`,
    }];
  }

  const generalSteps = formatHealthEngineExecutionSteps(
    (exec as { general_chart_engine_execution?: import("./askObservability").ObservabilityHealthEngineExecution | null })
      ?.general_chart_engine_execution,
    { domain: "domain" },
  );
  if (
    generalSteps.length ||
    exec?.display_mode === "general_charts" ||
    (exec as { general_chart_engine_execution?: unknown })?.general_chart_engine_execution
  ) {
    if (generalSteps.length) {
      return generalSteps;
    }
    return [{
      label: "General Chart Pack",
      value: `D1 + D9 + DASHA pack load nahi hua. Naya general question pucho after API deploy (v${OBS_DEBUGGER_VERSION}+).`,
    }];
  }

  const domainPack = (exec as { domain_engine_execution?: import("./askObservability").ObservabilityHealthEngineExecution | null })
    ?.domain_engine_execution;
  const domainSteps = formatHealthEngineExecutionSteps(domainPack, { domain: "domain" });
  if (domainSteps.length || exec?.display_mode === "domain_charts" || domainPack) {
    if (domainSteps.length) {
      return domainSteps;
    }
    return [{
      label: "Domain Chart Pack",
      value: `D1 + D9 unified pack load nahi hua. Naya question pucho after API deploy (v${OBS_DEBUGGER_VERSION}+).`,
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

function HealthSelectedBlocksPanel({
  audit,
  domainLabel = "health",
}: {
  audit: ObservabilityHealthSelectedBlocks | undefined;
  domainLabel?: string;
}) {
  if (!audit?.applies) {
    return (
      <p className="detail-muted">
        LLM Selected JSON Blocks: health, relationship, finance, travel, general chart, plus
        Unified+Gap (anger, career, charity, children, dreams, education, enemies, fame,
        litigation, luck, network, parents, personality, pets, property, remedy, settlement,
        siblings, spiritual, vastu, vehicle, wellness). Re-ask after API+admin deploy ({domainLabel}).
      </p>
    );
  }

  if (audit.error) {
    return <p className="detail-muted">Selected blocks error: {audit.error}</p>;
  }

  const expected = audit.available_blocks || audit.expected_blocks || [];
  const used = audit.used_in_answer?.blocks || [];

  return (
    <div className="obs-validator">
      <p className="detail-muted" style={{ marginBottom: 10 }}>
        Focus: <strong>{audit.focus_label || audit.focus || "Engine Execution"}</strong>
        {" — "}
        Engine Execution se <em>sirf question-relevant</em> blocks (poora EE dump nahi). LLM full
        D1/D9 padhta hai; yahan specific check set dikhta hai.
      </p>

      <p className="detail-muted" style={{ margin: "8px 0 4px" }}>
        <strong>Question-relevant from Engine Execution</strong> (ranked: weak / high priority first —
        dignity + strength included)
      </p>
      {expected.length === 0 ? (
        <p className="detail-muted">— (Engine Execution empty / missing)</p>
      ) : (
        <div className="obs-rule-decisions">
          {expected.map((b) => (
            <div key={b.id || b.label} className="obs-rule-decision-row">
              <div className="obs-rule-decision-head">
                <span>
                  <code>{b.id}</code> — {b.label}
                </span>
              </div>
              {b.detail ? <p className="detail-muted obs-rule-reason">{b.detail}</p> : null}
              {b.role || b.rank != null ? (
                <p className="detail-muted obs-rule-reason">
                  {b.rank != null ? `Rank #${b.rank}` : null}
                  {b.rank != null && b.role ? " · " : null}
                  {b.role ? `role=${b.role}` : null}
                  {b.priority != null ? ` · priority=${b.priority}` : null}
                </p>
              ) : null}
              {b.why ? <p className="detail-muted obs-rule-reason">{b.why}</p> : null}
            </div>
          ))}
        </div>
      )}

      <p className="detail-muted" style={{ margin: "12px 0 4px" }}>
        <strong>Matched in answer from Engine Execution</strong>
      </p>
      {used.length === 0 ? (
        <p className="detail-muted">—</p>
      ) : (
        <div className="obs-rule-decisions">
          {used.map((b) => (
            <div key={b.id || b.label} className="obs-rule-decision-row">
              <div className="obs-rule-decision-head">
                <span>{b.label || b.id}</span>
              </div>
              {b.detail ? <p className="detail-muted obs-rule-reason">{b.detail}</p> : null}
            </div>
          ))}
        </div>
      )}

      {(audit.overlap_notes || []).length > 0 ? (
        <p className="detail-muted" style={{ marginTop: 10 }}>
          {(audit.overlap_notes || []).join(" · ")}
        </p>
      ) : null}
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
  const perf = obs.performance || {};
  const selectedBlocksCandidates = [
    obs.health_selected_blocks,
    obs.relationship_selected_blocks,
    obs.finance_selected_blocks,
    obs.travel_selected_blocks,
    obs.general_selected_blocks,
    obs.unified_selected_blocks,
  ];
  const selectedBlocks = selectedBlocksCandidates.find((b) => b?.applies === true);
  const activeEnginePack = resolveActiveEnginePack(exec);
  const domainLabel =
    exec.unified_domain ||
    row.topic ||
    (exec.health_engine_execution ? "health" : exec.relationship_engine_execution ? "relationship" : "engine");

  return (
    <div className="obs-debugger">
      <div className="obs-debugger-header">
        <div className="obs-debugger-title-row">
          <h3>Developer debugger</h3>
          <span className="obs-version-badge">v{OBS_DEBUGGER_VERSION}</span>
        </div>
        <p className="detail-muted">
          Question → DNA → Routing → Engine → Evidence → Score → Verdict → Answer
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

      <Section title="1. Question DNA" stars={1} className="obs-section-dna">
        <DnaComplianceBox
          steps={obs.question_dna_pipeline || []}
          summary={obs.question_dna_followed_summary}
        />
      </Section>

      <Section title="2. Engine Execution" stars={5}>
        <p className="detail-muted obs-engine-name">
          {exec.display_mode === "health_charts" || exec.health_engine_execution ? (
            <>
              Health charts: <code>D1 + D9</code>
              <EngineModuleBadges pack={activeEnginePack} />
              {exec.health_engine_execution?.schema_version
                ? ` · ${exec.health_engine_execution.schema_version}`
                : null}
            </>
          ) : exec.display_mode === "relationship_charts" ||
            exec.relationship_engine_execution ? (
            <>
              Relationship charts: <code>D1 + D9</code>
              <EngineModuleBadges pack={activeEnginePack} />
              {exec.relationship_engine_execution?.schema_version
                ? ` · ${exec.relationship_engine_execution.schema_version}`
                : null}
            </>
          ) : exec.display_mode === "finance_charts" || exec.finance_engine_execution ? (
            <>
              Finance charts: <code>D1 + D9</code>
              <EngineModuleBadges pack={activeEnginePack} />
              {exec.finance_engine_execution?.schema_version
                ? ` · ${exec.finance_engine_execution.schema_version}`
                : null}
            </>
          ) : exec.display_mode === "travel_charts" || exec.travel_engine_execution ? (
            <>
              Travel charts: <code>D1 + D9</code>
              <EngineModuleBadges pack={activeEnginePack} />
              {exec.travel_engine_execution?.schema_version
                ? ` · ${exec.travel_engine_execution.schema_version}`
                : null}
            </>
          ) : exec.display_mode === "general_charts" ||
            (exec as { general_chart_engine_execution?: { schema_version?: string } | null })
              .general_chart_engine_execution ? (
            <>
              General charts: <code>D1 + D9 + DASHA</code>
              <EngineModuleBadges pack={activeEnginePack} />
              {(exec as { general_chart_engine_execution?: { schema_version?: string } | null })
                .general_chart_engine_execution?.schema_version
                ? ` · ${(exec as { general_chart_engine_execution?: { schema_version?: string } }).general_chart_engine_execution?.schema_version}`
                : null}
            </>
          ) : exec.display_mode === "domain_charts" || exec.domain_engine_execution ? (
            <>
              {(() => {
                const dom = String(
                  (exec as { unified_domain?: string | null }).unified_domain || "",
                ).trim();
                const label = dom
                  ? dom.charAt(0).toUpperCase() + dom.slice(1)
                  : "Domain";
                return <>{label} charts: <code>D1 + D9</code></>;
              })()}
              <EngineModuleBadges pack={activeEnginePack} />
              {exec.domain_engine_execution?.schema_version
                ? ` · ${exec.domain_engine_execution.schema_version}`
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

      <Section title="3. LLM Selected JSON Blocks" stars={5}>
        <HealthSelectedBlocksPanel audit={selectedBlocks} domainLabel={String(domainLabel)} />
      </Section>
    </div>
  );
}
