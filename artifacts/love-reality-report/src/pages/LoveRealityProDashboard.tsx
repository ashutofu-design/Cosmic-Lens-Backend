import { AlertTriangle, Sparkles, TrendingUp } from "lucide-react";
import { CircularGauge, MiniRing } from "../components/Gauges";
import { GlassCard } from "../components/GlassCard";
import { MetricCard, ProgressRow } from "../components/MetricCard";
import { ReportFooter } from "../components/ReportFooter";
import { ReportHeader } from "../components/ReportHeader";
import type { AnalysisBlock, LoveRealityReportData } from "../types";

function SectionLabel({ children }: { children: string }) {
  return (
    <h2 className="mb-0.5 text-[8px] font-bold uppercase tracking-[0.16em] text-cosmic-600/90">
      {children}
    </h2>
  );
}

function AnalysisCard({ block }: { block: AnalysisBlock }) {
  return (
    <GlassCard className="flex items-start gap-1.5 p-1.5">
      <MiniRing score={block.score} size={28} />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-1">
          <h3 className="text-[8px] font-bold text-cosmic-900">{block.title}</h3>
          <span className="shrink-0 text-[7px] font-semibold text-cosmic-600">{block.score}/100</span>
        </div>
        <p className="mt-0.5 line-clamp-2 text-[7px] leading-[1.35] text-slate-600">{block.explanation}</p>
      </div>
    </GlassCard>
  );
}

function buildInsightsNarrative(data: LoveRealityReportData): string {
  const parts = [data.snapshot.trim()];
  const ai = data.aiExplanation.trim();
  if (ai && ai !== parts[0] && !parts[0]?.includes(ai.slice(0, 40))) {
    parts.push(ai);
  }
  return parts.filter(Boolean).join(" ");
}

export function LoveRealityProDashboard({ data }: { data: LoveRealityReportData }) {
  const m = data.metrics;
  const narrative = buildInsightsNarrative(data);

  return (
    <article
      id="love-reality-pro-page"
      className="a4-page cosmic-bg flex flex-col px-[9mm] py-[7mm] text-slate-800"
    >
      <ReportHeader data={data} />

      {/* Hero */}
      <section className="mt-1.5 grid grid-cols-[28%_1fr] gap-1.5">
        <GlassCard accent className="relative flex items-center justify-center py-1.5">
          <CircularGauge
            value={data.cosmicAlignmentScore}
            size={96}
            stroke={8}
            label="Cosmic Alignment"
            sublabel="Composite score"
          />
        </GlassCard>
        <GlassCard className="p-2">
          <SectionLabel>Relationship Summary</SectionLabel>
          <p className="text-[8.5px] font-semibold leading-snug text-cosmic-900">
            {data.p1Name} & {data.p2Name}
          </p>
          <p className="mt-0.5 line-clamp-4 text-[7.5px] leading-snug text-slate-700">
            {data.relationshipSummary}
          </p>
        </GlassCard>
      </section>

      {/* Core metrics */}
      <section className="mt-1.5">
        <SectionLabel>Core Metrics</SectionLabel>
        <div className="grid grid-cols-4 gap-1">
          <MetricCard metric={m.loveCompatibility} />
          <MetricCard metric={m.breakupRisk} />
          <MetricCard metric={m.loyalty} />
          <MetricCard metric={m.reunionChance} />
        </div>
      </section>

      {/* Relationship Insights — snapshot + key insights (+ merged AI text) */}
      <section className="mt-1.5">
        <GlassCard className="p-2">
          <SectionLabel>Relationship Insights</SectionLabel>
          <p className="line-clamp-3 text-[7.5px] leading-snug text-slate-700">{narrative}</p>
          <ul className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5">
            {data.keyInsights.slice(0, 4).map((item) => (
              <li
                key={item.text}
                className="flex gap-1 text-[7px] leading-snug text-slate-700"
              >
                <Sparkles className="mt-0.5 h-2.5 w-2.5 shrink-0 text-cosmic-500" strokeWidth={2.2} />
                <span>{item.text}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      </section>

      {/* Strengths / Challenges — progress bars only */}
      <section className="mt-1.5 grid grid-cols-2 gap-1">
        <GlassCard className="p-1.5">
          <div className="mb-0.5 flex items-center gap-1">
            <TrendingUp className="h-2.5 w-2.5 text-emerald-600" />
            <SectionLabel>Strengths in this Connection</SectionLabel>
          </div>
          <div className="space-y-0.5">
            {data.strengths.slice(0, 4).map((s) => (
              <ProgressRow key={s.label} label={s.label} value={s.value} tone="positive" />
            ))}
          </div>
        </GlassCard>
        <GlassCard className="p-1.5">
          <div className="mb-0.5 flex items-center gap-1">
            <AlertTriangle className="h-2.5 w-2.5 text-amber-600" />
            <SectionLabel>Challenges in this Connection</SectionLabel>
          </div>
          <div className="space-y-0.5">
            {data.challenges.slice(0, 4).map((c) => (
              <ProgressRow key={c.label} label={c.label} value={c.value} tone="negative" />
            ))}
          </div>
        </GlassCard>
      </section>

      {/* Deep analysis — compact */}
      <section className="mt-1.5">
        <SectionLabel>Deep Analysis</SectionLabel>
        <div className="grid grid-cols-2 gap-1">
          <AnalysisCard block={data.analysis.emotional} />
          <AnalysisCard block={data.analysis.communication} />
          <AnalysisCard block={data.analysis.trust} />
          <AnalysisCard block={data.analysis.longTerm} />
        </div>
      </section>

      <div className="mt-auto pt-1.5">
        <ReportFooter
          verdict={data.verdict}
          recommendations={data.recommendations}
          qrUrl={data.qrUrl}
        />
      </div>

      <p className="mt-0.5 text-center text-[5.5px] text-slate-400">
        Cosmic Lens · Confidential premium report
      </p>
    </article>
  );
}
