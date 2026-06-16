import type { LucideIcon } from "lucide-react";
import { Heart, RefreshCw, Shield, Zap } from "lucide-react";
import { cn, scoreColor } from "../lib/utils";
import type { MetricBlock } from "../types";
import { GlassCard } from "./GlassCard";

const ICONS: Record<string, LucideIcon> = {
  love: Heart,
  breakup: Zap,
  loyalty: Shield,
  reunion: RefreshCw,
};

function metricIcon(label: string): LucideIcon {
  const l = label.toLowerCase();
  if (l.includes("breakup")) return ICONS.breakup;
  if (l.includes("loyal")) return ICONS.loyalty;
  if (l.includes("reunion") || l.includes("return")) return ICONS.reunion;
  return ICONS.love;
}

export function MetricCard({ metric }: { metric: MetricBlock }) {
  const Icon = metricIcon(metric.label);
  const barColor = scoreColor(metric.value, metric.invert);

  return (
    <GlassCard className="flex h-full flex-col p-2">
      <div className="mb-1 flex items-center justify-between gap-1">
        <div className="flex items-center gap-1.5">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-cosmic-600/10 text-cosmic-700">
            <Icon className="h-3.5 w-3.5" strokeWidth={2.2} />
          </span>
          <span className="text-[10px] font-semibold leading-tight text-cosmic-900">{metric.label}</span>
        </div>
        <span className="font-display text-lg font-bold leading-none text-cosmic-800">{metric.value}%</span>
      </div>
      <div className="mb-1 h-1.5 overflow-hidden rounded-full bg-cosmic-200/60">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${metric.value}%`, backgroundColor: barColor }}
        />
      </div>
      <p className="mt-auto text-[9px] leading-snug text-slate-600 line-clamp-2">{metric.interpretation}</p>
    </GlassCard>
  );
}

export function ProgressRow({
  label,
  value,
  tone = "positive",
  icon,
}: {
  label: string;
  value: number;
  tone?: "positive" | "negative";
  icon?: string;
}) {
  const color = tone === "negative" ? "#dc2626" : scoreColor(value);

  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between gap-2 text-[10.5px]">
        <span className="flex items-center gap-1 font-medium text-slate-700">
          {icon ? <span style={{ color }} className="text-[11px] font-bold">{icon}</span> : null}
          {label}
        </span>
        <span className={cn("font-bold", tone === "negative" ? "text-red-600" : "text-cosmic-700")}>
          {value}%
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200/80">
        <div className="h-full rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}
