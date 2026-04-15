const koots = [
  { label: "Nadi",         score: 8,   max: 8,  bad: false, desc: "Same Kapha nadi — excellent harmony" },
  { label: "Bhakut",       score: 7,   max: 7,  bad: false, desc: "Libra–Aquarius — favourable" },
  { label: "Gana",         score: 6,   max: 6,  bad: false, desc: "Both Dev gana — naturally compatible" },
  { label: "Graha Maitri", score: 4,   max: 5,  bad: false, desc: "Mercury–Saturn — friendly lords" },
  { label: "Yoni",         score: 2,   max: 4,  bad: false, desc: "Cow–Buffalo — neutral yoni" },
  { label: "Tara",         score: 1.5, max: 3,  bad: false, desc: "Neutral tara position" },
  { label: "Vasya",        score: 2,   max: 2,  bad: false, desc: "Same elemental group" },
  { label: "Varna",        score: 0,   max: 1,  bad: true,  desc: "Vaishya–Brahmin mismatch" },
];

const TOTAL = koots.reduce((s, k) => s + k.score, 0);
const TOTAL_INT = Math.round(TOTAL);
const PCT = Math.round((TOTAL / 36) * 100);

function gradeInfo(t: number) {
  if (t >= 32) return { label: "Exceptional",  color: "#22c55e", tagline: "A rare and perfect union" };
  if (t >= 28) return { label: "Very Good",     color: "#22c55e", tagline: "Strong, lasting compatibility" };
  if (t >= 24) return { label: "Good Match",    color: "#fbbf24", tagline: "Compatible with mutual effort" };
  if (t >= 18) return { label: "Acceptable",    color: "#f97316", tagline: "Proceed with care & guidance" };
  return           { label: "Challenging",      color: "#ef4444", tagline: "Consult a Jyotishi first" };
}

export function KundliMilanRing() {
  const g = gradeInfo(TOTAL);
  // Ring geometry
  const R = 60, CX = 80, CY = 80, SW = 12;
  const circ = 2 * Math.PI * R;
  const filled = circ * (PCT / 100);
  const empty = circ - filled;

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
        {/* Compatibility ring card */}
        <div className="rounded-2xl bg-[#111827] border border-[#1E293B] p-4">
          <div className="flex items-center justify-between">
            {/* Person 1 */}
            <div className="flex flex-col items-center gap-1 w-24">
              <div className="w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl"
                style={{ backgroundColor: "rgba(99,102,241,0.15)", borderColor: "rgba(99,102,241,0.4)" }}>👨</div>
              <div className="text-[#E2E8F0] font-bold text-[11px] text-center leading-tight">Rahul Sharma</div>
              <div className="text-[9px] text-center" style={{ color: "#475569" }}>Scorpio · Jyeshtha</div>
            </div>

            {/* Ring */}
            <div className="relative flex items-center justify-center" style={{ width: 120, height: 120 }}>
              <svg width="120" height="120" viewBox="0 0 160 160">
                {/* Background track */}
                <circle cx="80" cy="80" r={R} fill="none" stroke="#1E293B" strokeWidth={SW} />
                {/* Progress arc */}
                <circle cx="80" cy="80" r={R} fill="none"
                  stroke={g.color} strokeWidth={SW}
                  strokeLinecap="round"
                  strokeDasharray={`${filled} ${empty}`}
                  transform="rotate(-90 80 80)"
                />
                {/* Gradient glow hint */}
                <circle cx="80" cy="80" r={R} fill="none"
                  stroke={g.color} strokeWidth={SW - 4}
                  strokeOpacity="0.15"
                  strokeLinecap="round"
                  strokeDasharray={`${filled} ${empty}`}
                  transform="rotate(-90 80 80)"
                />
              </svg>
              {/* Score inside ring */}
              <div className="absolute flex flex-col items-center">
                <div className="font-bold text-2xl leading-none" style={{ color: g.color }}>{TOTAL_INT}</div>
                <div className="text-[10px]" style={{ color: "#475569" }}>/36</div>
                <div className="text-[8px] font-bold mt-0.5 uppercase tracking-wide" style={{ color: g.color }}>{g.label}</div>
              </div>
            </div>

            {/* Person 2 */}
            <div className="flex flex-col items-center gap-1 w-24">
              <div className="w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl"
                style={{ backgroundColor: "rgba(236,72,153,0.15)", borderColor: "rgba(236,72,153,0.4)" }}>👩</div>
              <div className="text-[#E2E8F0] font-bold text-[11px] text-center leading-tight">Priya Gupta</div>
              <div className="text-[9px] text-center" style={{ color: "#475569" }}>Aquarius · Shatabhisha</div>
            </div>
          </div>

          {/* Tagline */}
          <div className="text-center mt-3 text-[12px] font-semibold" style={{ color: g.color }}>
            {g.tagline}
          </div>
        </div>

        {/* Koot list — linear style */}
        <div className="text-[9px] font-bold uppercase tracking-widest px-1" style={{ color: "#475569" }}>
          Guna Analysis (Ashtakoot)
        </div>
        <div className="flex flex-col gap-1.5">
          {koots.map((k, i) => {
            const c = k.bad ? "#ef4444" : k.score / k.max >= 0.9 ? "#22c55e" : k.score / k.max >= 0.5 ? "#fbbf24" : "#f97316";
            return (
              <div key={i} className="rounded-xl px-3 py-2.5 flex items-center gap-3 border"
                style={{ backgroundColor: "#111827", borderColor: k.bad ? "#ef444428" : "#1E293B" }}>
                {/* Colored dot */}
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: c }} />
                {/* Name + desc */}
                <div className="flex-1 min-w-0">
                  <div className="text-[#E2E8F0] font-bold text-[12px]">{k.label}</div>
                  <div className="text-[#475569] text-[10px]">{k.desc}</div>
                </div>
                {/* Score pill */}
                <div className="text-[11px] font-bold px-2 py-0.5 rounded-lg shrink-0"
                  style={{ backgroundColor: `${c}18`, color: c }}>{k.score}/{k.max}</div>
              </div>
            );
          })}
        </div>

        {/* Total footer */}
        <div className="rounded-xl p-3 flex items-center justify-between border"
          style={{ background: `linear-gradient(135deg, ${g.color}15, ${g.color}05)`, borderColor: `${g.color}30` }}>
          <div className="text-[#94A3B8] text-[12px]">Total Gunas</div>
          <div className="font-bold text-[16px]" style={{ color: g.color }}>{TOTAL_INT} / 36 · {g.label}</div>
        </div>

        <div className="rounded-xl px-3 py-2 border flex gap-2 items-start mb-4"
          style={{ backgroundColor: "#111827", borderColor: "#1E293B" }}>
          <span className="text-[#475569] text-xs mt-0.5">ℹ</span>
          <span className="text-[10px] leading-relaxed text-[#475569]">
            This is an estimate. Always consult a qualified Jyotishi before marriage.
          </span>
        </div>
      </div>
    </div>
  );
}
