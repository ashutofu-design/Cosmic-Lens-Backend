import { cn, scoreColor } from "../lib/utils";

export function CircularGauge({
  value,
  size = 120,
  stroke = 10,
  label,
  sublabel,
  invert = false,
}: {
  value: number;
  size?: number;
  stroke?: number;
  label: string;
  sublabel?: string;
  invert?: boolean;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const offset = c - (pct / 100) * c;
  const color = scoreColor(pct, invert);

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgb(139 92 246 / 0.12)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div
        className="absolute flex flex-col items-center justify-center text-center"
        style={{ width: size, height: size }}
      >
        <span className="font-display text-2xl font-bold leading-none text-cosmic-800">{pct}</span>
        <span className="mt-0.5 text-[9px] font-medium uppercase tracking-wider text-cosmic-600/80">
          / 100
        </span>
      </div>
      <p className={cn("mt-1 text-center text-[10px] font-semibold text-cosmic-800")}>{label}</p>
      {sublabel ? (
        <p className="mt-0.5 max-w-[110px] text-center text-[8px] leading-tight text-slate-500">
          {sublabel}
        </p>
      ) : null}
    </div>
  );
}

export function MiniRing({
  score,
  size = 36,
}: {
  score: number;
  size?: number;
}) {
  const stroke = 4;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score));
  const offset = c - (pct / 100) * c;
  const color = scoreColor(pct);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgb(139 92 246 / 0.15)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-cosmic-800"
      >
        {pct}
      </span>
    </div>
  );
}
