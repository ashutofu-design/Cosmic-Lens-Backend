type VerdictTone = "strong" | "mixed" | "caution";

function toneForScore(score: number): VerdictTone {
  if (score >= 70) return "strong";
  if (score >= 50) return "mixed";
  return "caution";
}

const TONE_STYLES: Record<VerdictTone, string> = {
  strong: "bg-emerald-50 text-emerald-800 border-emerald-200",
  mixed: "bg-amber-50 text-amber-900 border-amber-200",
  caution: "bg-rose-50 text-rose-800 border-rose-200",
};

const TONE_LABEL: Record<VerdictTone, string> = {
  strong: "Strong cosmic alignment",
  mixed: "Mixed — conscious effort needed",
  caution: "High friction window",
};

export function VerdictBadge({ score }: { score: number }) {
  const tone = toneForScore(score);
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold tracking-wide ${TONE_STYLES[tone]}`}
    >
      {TONE_LABEL[tone]} · {score}/100
    </span>
  );
}
