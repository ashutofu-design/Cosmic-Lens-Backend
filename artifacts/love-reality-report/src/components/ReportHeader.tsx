import { Sparkles } from "lucide-react";
import { formatReportDate } from "../lib/utils";
import type { LoveRealityReportData } from "../types";

export function ReportHeader({ data }: { data: LoveRealityReportData }) {
  return (
    <header className="flex items-start justify-between gap-2 border-b border-cosmic-300/25 pb-1.5">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 shrink-0 text-gold" strokeWidth={2.2} />
          <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-cosmic-700">
            Cosmic Lens
          </span>
          <span className="rounded-full bg-gradient-to-r from-cosmic-600 to-cosmic-800 px-2 py-0.5 text-[7px] font-bold uppercase tracking-wider text-white shadow-sm">
            Premium
          </span>
        </div>
        <h1 className="font-display mt-1 text-[17px] font-bold leading-tight text-cosmic-900">
          Love Reality Pro
        </h1>
        <p className="mt-0.5 text-[10px] font-semibold text-slate-700">
          {data.p1Name} <span className="text-cosmic-400">·</span> {data.p2Name}
        </p>
      </div>
      <div className="shrink-0 text-right text-[8px] leading-snug text-slate-500">
        <div>
          ID <span className="font-mono font-semibold text-cosmic-800">{data.reportId}</span>
        </div>
        <div className="mt-0.5 max-w-[120px]">{formatReportDate(data.generatedAt)}</div>
      </div>
    </header>
  );
}
