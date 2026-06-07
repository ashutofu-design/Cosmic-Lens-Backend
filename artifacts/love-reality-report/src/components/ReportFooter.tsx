import { QrCode } from "lucide-react";
import { GlassCard } from "./GlassCard";

export function ReportFooter({
  verdict,
  recommendations,
  qrUrl,
}: {
  verdict: string;
  recommendations: string[];
  qrUrl?: string;
}) {
  return (
    <footer className="grid grid-cols-[1fr_1fr_44px] gap-1.5">
      <GlassCard accent className="p-2">
        <h3 className="mb-0.5 text-[8px] font-bold uppercase tracking-wide text-cosmic-700">
          Final Cosmic Verdict
        </h3>
        <p className="line-clamp-3 text-[7.5px] leading-snug text-slate-700">{verdict}</p>
      </GlassCard>
      <GlassCard className="p-2">
        <h3 className="mb-0.5 text-[8px] font-bold uppercase tracking-wide text-cosmic-700">
          Recommendations
        </h3>
        <ul className="space-y-0.5">
          {recommendations.slice(0, 3).map((r) => (
            <li key={r} className="flex gap-1 text-[7px] leading-snug text-slate-600">
              <span className="text-cosmic-500">▸</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </GlassCard>
      <GlassCard className="flex flex-col items-center justify-center p-1">
        {qrUrl ? (
          <>
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(qrUrl)}`}
              alt="QR"
              width={36}
              height={36}
              className="rounded"
            />
            <span className="mt-0.5 text-[6px] text-slate-500">Scan</span>
          </>
        ) : (
          <QrCode className="h-8 w-8 text-cosmic-300" />
        )}
      </GlassCard>
    </footer>
  );
}
