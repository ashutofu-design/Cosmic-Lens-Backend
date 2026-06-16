import { AlertTriangle, Sparkles, TrendingUp } from "lucide-react";
import { CircularGauge } from "../components/Gauges";
import { GlassCard } from "../components/GlassCard";
import { MetricCard, ProgressRow } from "../components/MetricCard";
import { ReportHeader } from "../components/ReportHeader";
import { VerdictBadge } from "../components/VerdictBadge";
import type { LoveRealityReportData } from "../types";

function SectionLabel({ children }: { children: string }) {
  return (
    <h2 className="mb-1 text-[12px] font-bold uppercase tracking-[0.12em] text-cosmic-700">
      {children}
    </h2>
  );
}

const STRENGTH_ICONS = ["★", "♥", "✦"] as const;
const CHALLENGE_ICONS = ["⚠", "✗", "▼"] as const;

function buildInsightsNarrative(data: LoveRealityReportData): string {
  const parts = [data.snapshot.trim()];
  const ai = data.aiExplanation.trim();
  if (ai && ai !== parts[0] && !parts[0]?.includes(ai.slice(0, 40))) {
    parts.push(ai);
  }
  return parts.filter(Boolean).join(" ");
}

/** Page 1 executive summary content (no A4 frame — use A4PaginatedPreview wrapper). */
export function LoveRealityProDashboardContent({ data }: { data: LoveRealityReportData }) {
  const m = data.metrics;
  const narrative = buildInsightsNarrative(data);

  return (
    <div id="love-reality-pro-page" className="flex flex-col text-slate-800">
      <ReportHeader data={data} />

      {/* Hero — large gauge + badge + summary */}
      <section className="mt-2.5">
        <GlassCard accent className="flex flex-col items-center gap-2 p-3">
          <CircularGauge
            value={data.cosmicAlignmentScore}
            size={148}
            stroke={12}
            label="Cosmic Alignment Score"
          />
          <VerdictBadge score={data.cosmicAlignmentScore} />
          <div className="w-full border-t border-cosmic-200/80 pt-2.5">
            <SectionLabel>Relationship Summary</SectionLabel>
            <p className="text-[11.5px] leading-[1.45] text-slate-700">{data.relationshipSummary}</p>
          </div>
        </GlassCard>
      </section>

      {/* Core metrics */}
      <section className="mt-2.5">
        <SectionLabel>Core Metrics</SectionLabel>
        <div className="mt-1 grid grid-cols-4 gap-1.5">
          <MetricCard metric={m.loveCompatibility} />
          <MetricCard metric={m.breakupRisk} />
          <MetricCard metric={m.loyalty} />
          <MetricCard metric={m.reunionChance} />
        </div>
      </section>

      {/* Relationship insights */}
      <section className="mt-2.5">
        <GlassCard className="p-2.5">
          <SectionLabel>Relationship Insights</SectionLabel>
          <p className="text-[11.5px] leading-[1.45] text-slate-700">{narrative}</p>
          <ul className="mt-2 space-y-1">
            {data.keyInsights.slice(0, 4).map((item) => (
              <li key={item.text} className="flex gap-1.5 text-[11px] leading-snug text-slate-700">
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cosmic-500" strokeWidth={2.2} />
                <span>{item.text}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      </section>

      {/* Strengths / Challenges */}
      <section className="mt-2.5 grid grid-cols-2 gap-2">
        <GlassCard className="p-2.5">
          <div className="mb-1 flex items-center gap-1.5">
            <TrendingUp className="h-4 w-4 text-emerald-600" />
            <SectionLabel>Strengths in this Connection</SectionLabel>
          </div>
          <div className="space-y-1.5">
            {data.strengths.slice(0, 3).map((s, i) => (
              <ProgressRow
                key={s.label}
                label={s.label}
                value={s.value}
                tone="positive"
                icon={STRENGTH_ICONS[i % STRENGTH_ICONS.length]}
              />
            ))}
          </div>
        </GlassCard>
        <GlassCard className="p-2.5">
          <div className="mb-1 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <SectionLabel>Challenges in this Connection</SectionLabel>
          </div>
          <div className="space-y-1.5">
            {data.challenges.slice(0, 3).map((c, i) => (
              <ProgressRow
                key={c.label}
                label={c.label}
                value={c.value}
                tone="negative"
                icon={CHALLENGE_ICONS[i % CHALLENGE_ICONS.length]}
              />
            ))}
          </div>
        </GlassCard>
      </section>

      {/* Premium verdict */}
      <section className="mt-2.5">
        <GlassCard
          accent
          className="border-2 border-cosmic-400/40 p-3"
        >
          <p className="text-[13px] font-bold uppercase tracking-wide text-cosmic-700">
            ✦ Final Cosmic Verdict
          </p>
          <p className="mt-1.5 text-[12px] leading-[1.5] text-slate-800">{data.verdict}</p>
        </GlassCard>
      </section>

      {/* Recommendations */}
      <section className="mt-2">
        <GlassCard className="p-2.5">
          <SectionLabel>Recommendations</SectionLabel>
          <ul className="mt-1 space-y-1">
            {data.recommendations.slice(0, 5).map((r) => (
              <li key={r} className="flex gap-1.5 text-[11px] leading-snug text-slate-700">
                <span className="font-bold text-cosmic-500">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      </section>

      <p className="pt-2 text-center text-[9px] text-slate-400">
        Cosmic Lens · Confidential premium report
      </p>
    </div>
  );
}

/** @deprecated use LoveRealityProDashboardContent + A4PaginatedPreview */
export function LoveRealityProDashboard({ data }: { data: LoveRealityReportData }) {
  return <LoveRealityProDashboardContent data={data} />;
}
