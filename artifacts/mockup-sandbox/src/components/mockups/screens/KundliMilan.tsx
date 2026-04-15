const koots = [
  { key: "nadi",    label: "Nadi",         score: 8, max: 8,  bad: false, detail: "Kapha – Kapha" },
  { key: "bhakut",  label: "Bhakut",       score: 7, max: 7,  bad: false, detail: "Libra – Aquarius" },
  { key: "gana",    label: "Gana",         score: 6, max: 6,  bad: false, detail: "Dev – Dev" },
  { key: "maitri",  label: "Graha Maitri", score: 4, max: 5,  bad: false, detail: "Mercury – Saturn" },
  { key: "yoni",    label: "Yoni",         score: 2, max: 4,  bad: false, detail: "Cow – Buffalo" },
  { key: "tara",    label: "Tara",         score: 1.5, max: 3, bad: false, detail: "Janma tara neutral" },
  { key: "vasya",   label: "Vasya",        score: 2, max: 2,  bad: false, detail: "Same group" },
  { key: "varna",   label: "Varna",        score: 0, max: 1,  bad: true,  detail: "Vaishya – Brahmin" },
];

const TOTAL = koots.reduce((s, k) => s + k.score, 0);

function kootColor(score: number, max: number, bad: boolean) {
  if (bad) return "#ef4444";
  const pct = score / max;
  if (pct >= 0.9) return "#22c55e";
  if (pct >= 0.6) return "#fbbf24";
  return "#f97316";
}

function grade(total: number) {
  if (total >= 32) return { label: "Excellent", color: "#22c55e", emoji: "💍", desc: "Perfect match!" };
  if (total >= 28) return { label: "Very Good",  color: "#22c55e", emoji: "💚", desc: "Strong compatibility" };
  if (total >= 24) return { label: "Good",        color: "#fbbf24", emoji: "💛", desc: "Compatible pair" };
  if (total >= 18) return { label: "Acceptable",  color: "#f97316", emoji: "🟠", desc: "Can proceed with care" };
  return { label: "Challenging", color: "#ef4444", emoji: "⚠", desc: "Careful consideration" };
}

export function KundliMilan() {
  const g = grade(TOTAL);
  const pct = Math.round((TOTAL / 36) * 100);

  return (
    <div className="min-h-screen bg-[#0B1220] font-sans overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-[#1E293B]">
        <button className="w-8 h-8 rounded-full bg-[#111827] border border-[#1E293B] flex items-center justify-center text-[#64748B] text-sm">←</button>
        <div className="flex-1">
          <div className="text-[#E2E8F0] font-bold text-[17px]">Kundli Milan</div>
          <div className="text-[#475569] text-[10px]">अष्टकूट मिलान</div>
        </div>
      </div>

      <div className="px-4 pt-4 flex flex-col gap-3">
        {/* Couple display */}
        <div className="rounded-2xl bg-[#111827] border border-[#1E293B] p-4">
          <div className="flex items-center justify-between">
            {/* Person 1 */}
            <div className="flex flex-col items-center gap-1.5 w-28">
              <div className="w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl"
                style={{ backgroundColor: "rgba(99,102,241,0.15)", borderColor: "rgba(99,102,241,0.5)" }}>👨</div>
              <div className="text-[#E2E8F0] font-bold text-[12px] text-center">Rahul Sharma</div>
              <div className="text-[#475569] text-[9px] text-center">Scorpio · Jyeshtha</div>
            </div>

            {/* Score center */}
            <div className="flex flex-col items-center gap-1">
              <div className="text-2xl">{g.emoji}</div>
              <div className="flex items-baseline gap-1">
                <span className="font-bold text-3xl" style={{ color: g.color }}>{TOTAL}</span>
                <span className="text-[#475569] text-sm">/36</span>
              </div>
              <div className="text-[11px] font-bold" style={{ color: g.color }}>{g.label}</div>
              <div className="text-[9px] text-center" style={{ color: "#64748B" }}>{g.desc}</div>
            </div>

            {/* Person 2 */}
            <div className="flex flex-col items-center gap-1.5 w-28">
              <div className="w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl"
                style={{ backgroundColor: "rgba(236,72,153,0.15)", borderColor: "rgba(236,72,153,0.5)" }}>👩</div>
              <div className="text-[#E2E8F0] font-bold text-[12px] text-center">Priya Gupta</div>
              <div className="text-[#475569] text-[9px] text-center">Aquarius · Shatabhisha</div>
            </div>
          </div>

          {/* Score bar */}
          <div className="mt-4 h-2 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${g.color}88, ${g.color})` }} />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[9px]" style={{ color: "#475569" }}>0</span>
            <span className="text-[9px]" style={{ color: "#475569" }}>18 min</span>
            <span className="text-[9px]" style={{ color: "#475569" }}>36 max</span>
          </div>
        </div>

        {/* Ashtakoot breakdown */}
        <div className="text-[9px] font-bold uppercase tracking-widest px-1" style={{ color: "#475569" }}>
          Ashtakoot Breakdown
        </div>
        <div className="grid grid-cols-2 gap-2">
          {koots.map((k) => {
            const c = kootColor(k.score, k.max, k.bad);
            const kpct = Math.round((k.score / k.max) * 100);
            return (
              <div key={k.key} className="rounded-xl p-3 border"
                style={{ backgroundColor: "#111827", borderColor: k.bad ? "#ef444430" : "#1E293B" }}>
                <div className="flex justify-between items-start mb-1">
                  <div className="text-[#E2E8F0] font-bold text-[11px]">{k.label}</div>
                  <div className="text-[10px] font-bold px-1.5 py-0.5 rounded-md"
                    style={{ backgroundColor: `${c}18`, color: c }}>{k.score}/{k.max}</div>
                </div>
                <div className="text-[9px] mb-1.5" style={{ color: "#64748B" }}>{k.detail}</div>
                <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}>
                  <div className="h-full rounded-full" style={{ width: `${kpct}%`, backgroundColor: c }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Disclaimer */}
        <div className="rounded-xl px-3 py-2 border flex gap-2 items-start mb-4"
          style={{ backgroundColor: "#111827", borderColor: "#1E293B" }}>
          <span className="text-[#475569] text-xs mt-0.5">ℹ</span>
          <span className="text-[10px] leading-relaxed" style={{ color: "#475569" }}>
            This is an Ashtakoot estimate. Always consult a qualified Jyotishi for a complete analysis before marriage.
          </span>
        </div>
      </div>
    </div>
  );
}
