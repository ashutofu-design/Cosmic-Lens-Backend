const doshas = [
  { icon: "🔴", name: "Manglik", hindi: "मांगलिक", sev: 3, maxSev: 4, color: "#ef4444", label: "Strong", planetNote: "Mars → House 4" },
  { icon: "🐍", name: "Kalsarp", hindi: "कालसर्प", sev: 2, maxSev: 4, color: "#fbbf24", label: "Mild",   planetNote: "Rahu–Ketu axis" },
  { icon: "👣", name: "Pitra",   hindi: "पितृ",    sev: 0, maxSev: 4, color: "#22c55e", label: "Clear",  planetNote: "Sun safe" },
  { icon: "😶‍🌫️", name: "Shani", hindi: "शनि",    sev: 0, maxSev: 4, color: "#22c55e", label: "Clear",  planetNote: "Saturn → House 7" },
  { icon: "🌑", name: "Gandmool", hindi: "गंडमूल",  sev: 1, maxSev: 4, color: "#f97316", label: "Mild",  planetNote: "Moon nakshatra" },
  { icon: "🌊", name: "Chandra", hindi: "चंद्र",   sev: 0, maxSev: 4, color: "#22c55e", label: "Clear",  planetNote: "Moon → House 9" },
];

export function DoshDashboard() {
  const presentCount = doshas.filter(d => d.sev > 0).length;
  const overallScore = Math.round((1 - doshas.reduce((s, d) => s + d.sev, 0) / (doshas.length * 4)) * 100);
  const scoreColor = overallScore >= 75 ? "#22c55e" : overallScore >= 50 ? "#fbbf24" : "#ef4444";
  const circumference = 2 * Math.PI * 44;
  const dashOffset = circumference * (1 - overallScore / 100);

  return (
    <div className="min-h-screen bg-[#0B1220] font-sans overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-[#1E293B]">
        <button className="w-8 h-8 rounded-full bg-[#111827] border border-[#1E293B] flex items-center justify-center text-[#64748B] text-sm">←</button>
        <div className="flex-1">
          <div className="text-[#E2E8F0] font-bold text-[17px]">Dosh Analysis</div>
          <div className="text-[#475569] text-[10px]">दोष विश्लेषण</div>
        </div>
      </div>

      <div className="px-4 pt-4 flex flex-col gap-4">
        {/* Central score ring + stats */}
        <div className="rounded-2xl bg-[#111827] border border-[#1E293B] p-4 flex items-center gap-4">
          {/* SVG Ring */}
          <div className="relative shrink-0" style={{ width: 100, height: 100 }}>
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="44" fill="none" stroke="#1E293B" strokeWidth="8" />
              <circle cx="50" cy="50" r="44" fill="none"
                stroke={scoreColor} strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                transform="rotate(-90 50 50)"
                style={{ transition: "stroke-dashoffset 1s ease" }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="font-bold text-xl leading-none" style={{ color: scoreColor }}>{overallScore}</div>
              <div className="text-[9px] mt-0.5" style={{ color: "#475569" }}>score</div>
            </div>
          </div>

          {/* Stats */}
          <div className="flex-1 flex flex-col gap-2">
            <div className="text-[#E2E8F0] font-bold text-[15px]">Overall Dosh Status</div>
            <div className="flex gap-3">
              <div className="text-center">
                <div className="text-[#EF4444] font-bold text-lg leading-none">{presentCount}</div>
                <div className="text-[9px] text-[#475569] uppercase tracking-wide">Found</div>
              </div>
              <div className="w-px bg-[#1E293B]" />
              <div className="text-center">
                <div className="text-[#22C55E] font-bold text-lg leading-none">{doshas.length - presentCount}</div>
                <div className="text-[9px] text-[#475569] uppercase tracking-wide">Clear</div>
              </div>
              <div className="w-px bg-[#1E293B]" />
              <div className="text-center">
                <div className="text-[#F97316] font-bold text-lg leading-none">1</div>
                <div className="text-[9px] text-[#475569] uppercase tracking-wide">Urgent</div>
              </div>
            </div>
            <div className="text-[10px] leading-relaxed" style={{ color: "#64748B" }}>
              {presentCount} doshas need attention. Remedies available.
            </div>
          </div>
        </div>

        {/* Dosh rows — dashboard style */}
        <div className="flex flex-col gap-2">
          {doshas.map((d, i) => (
            <div key={i} className="rounded-xl bg-[#111827] border border-[#1E293B] px-3 py-3 flex items-center gap-3">
              {/* Icon */}
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-base"
                style={{ backgroundColor: `${d.color}15` }}>
                {d.icon}
              </div>

              {/* Name + planet note */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-[#E2E8F0] font-bold text-[13px]">{d.name}</span>
                  <span className="text-[#475569] text-[10px]">{d.hindi}</span>
                </div>
                <div className="text-[9px] mt-0.5" style={{ color: "#475569" }}>{d.planetNote}</div>
              </div>

              {/* Severity dots */}
              <div className="flex gap-1 shrink-0">
                {Array.from({ length: d.maxSev }).map((_, j) => (
                  <div key={j} className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: j < d.sev ? d.color : "#1E293B" }} />
                ))}
              </div>

              {/* Label */}
              <div className="text-[10px] font-bold w-12 text-right shrink-0" style={{ color: d.color }}>
                {d.label}
              </div>
            </div>
          ))}
        </div>

        {/* Remedy CTA */}
        <div className="rounded-2xl p-4 flex items-center gap-3 border"
          style={{ background: "linear-gradient(135deg, rgba(249,115,22,0.12), rgba(239,68,68,0.08))", borderColor: "rgba(249,115,22,0.25)" }}>
          <span className="text-2xl">🙏</span>
          <div className="flex-1">
            <div className="text-[#E2E8F0] font-bold text-[13px]">View Remedies (Upay)</div>
            <div className="text-[#64748B] text-[10px] mt-0.5">2 doshas have recommended remedies</div>
          </div>
          <span className="text-[#F97316] text-sm">→</span>
        </div>
      </div>
    </div>
  );
}
