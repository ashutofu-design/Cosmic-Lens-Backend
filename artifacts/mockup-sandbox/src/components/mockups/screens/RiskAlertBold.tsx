import { useState } from "react";

const days = [
  { day: "Wed", date: "15", energy: "Challenging", color: "#ef4444", score: 38,  emoji: "⚡", labelHi: "कठिन दिन",  insightHi: "मंगल की दृष्टि तीव्र है।", insightEn: "Avoid major decisions. Mars aspect is strong.", lucky: "#8b5cf6", luckyName: "Purple", nums: [4,13,22], saturn: true,  mars: true,  jupiter: false },
  { day: "Thu", date: "16", energy: "Neutral",     color: "#94a3b8", score: 61,  emoji: "🌤", labelHi: "सामान्य",    insightHi: "गुरु की दृष्टि स्थिरता देती है।", insightEn: "Stable day. Good for routine work.",    lucky: "#3b82f6", luckyName: "Blue",   nums: [3,12,21], saturn: false, mars: false, jupiter: true  },
  { day: "Fri", date: "17", energy: "Good",        color: "#22c55e", score: 82,  emoji: "✨", labelHi: "शुभ दिन",    insightHi: "शुक्र–गुरु युति शुभ है।",        insightEn: "Auspicious day. Finance and love positive.", lucky: "#f59e0b", luckyName: "Gold",   nums: [6,15,24], saturn: false, mars: false, jupiter: true  },
  { day: "Sat", date: "18", energy: "Challenging", color: "#f97316", score: 45,  emoji: "⚠", labelHi: "सतर्क रहें",  insightHi: "शनि वक्री है। सावधान रहें।",    insightEn: "Saturn retrograde. Be cautious in work.",   lucky: "#475569", luckyName: "Grey",   nums: [8,17,26], saturn: true,  mars: false, jupiter: false },
  { day: "Sun", date: "19", energy: "Good",        color: "#22c55e", score: 78,  emoji: "🌞", labelHi: "अच्छा दिन",  insightHi: "रवि की शक्ति से सफलता।",         insightEn: "Sun's power brings success and recognition.", lucky: "#f59e0b", luckyName: "Gold",   nums: [1,10,19], saturn: false, mars: false, jupiter: true  },
];

export function RiskAlertBold() {
  const [sel, setSel] = useState(0);
  const d = days[sel];

  return (
    <div className="min-h-screen bg-[#0B1220] font-sans flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-[#1E293B]">
        <button className="w-8 h-8 rounded-full bg-[#111827] border border-[#1E293B] flex items-center justify-center text-[#64748B] text-sm">←</button>
        <div className="flex-1">
          <div className="text-[#E2E8F0] font-bold text-[17px]">7-Day Risk Alerts</div>
          <div className="text-[#475569] text-[10px]">ग्रह आधारित सतर्कता</div>
        </div>
      </div>

      {/* Bold energy hero banner */}
      <div className="mx-4 mt-3 rounded-2xl overflow-hidden relative"
        style={{ background: `linear-gradient(135deg, ${d.color}30 0%, ${d.color}12 100%)`, border: `1px solid ${d.color}45` }}>
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-3xl">{d.emoji}</span>
                <div>
                  <div className="text-[#E2E8F0] font-bold text-[18px] leading-tight">{d.energy}</div>
                  <div className="text-[11px]" style={{ color: d.color }}>{d.labelHi}</div>
                </div>
              </div>
              <div className="text-[#475569] text-[12px]">Apr {d.date} · {d.day}nesday</div>
            </div>
            {/* Big score */}
            <div className="flex flex-col items-center">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center border"
                style={{ background: `${d.color}18`, borderColor: `${d.color}40` }}>
                <span className="font-bold text-xl" style={{ color: d.color }}>{d.score}</span>
              </div>
              <div className="text-[9px] mt-1 uppercase tracking-wide" style={{ color: "#475569" }}>Energy</div>
            </div>
          </div>

          {/* Score bar */}
          <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}>
            <div className="h-full rounded-full" style={{ width: `${d.score}%`, backgroundColor: d.color }} />
          </div>
        </div>

        {/* Planet aspects row */}
        <div className="flex gap-2 px-4 pb-3">
          {d.saturn    && <div className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] border" style={{ backgroundColor: "rgba(239,68,68,0.15)", borderColor: "rgba(239,68,68,0.3)", color: "#ef4444" }}>⚠ Shani</div>}
          {d.mars      && <div className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] border" style={{ backgroundColor: "rgba(249,115,22,0.15)", borderColor: "rgba(249,115,22,0.3)", color: "#f97316" }}>⚠ Mangal</div>}
          {d.jupiter   && <div className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] border" style={{ backgroundColor: "rgba(34,197,94,0.15)",  borderColor: "rgba(34,197,94,0.3)",  color: "#22c55e" }}>✓ Guru</div>}
          {!d.saturn && !d.mars && !d.jupiter && <div className="text-[10px]" style={{ color: "#475569" }}>No major aspects</div>}
        </div>
      </div>

      {/* Day selector strip */}
      <div className="flex gap-1.5 px-4 mt-3 overflow-x-auto pb-1">
        {days.map((a, i) => (
          <button key={i} onClick={() => setSel(i)}
            className="flex flex-col items-center py-2 px-2.5 rounded-xl shrink-0 border transition-all"
            style={{
              backgroundColor: sel === i ? `${a.color}20` : "#111827",
              borderColor: sel === i ? `${a.color}50` : "#1E293B",
            }}>
            <div className="w-2 h-2 rounded-full mb-1" style={{ backgroundColor: a.color }} />
            <div className="text-[10px] font-bold" style={{ color: sel === i ? a.color : "#64748B" }}>{a.day}</div>
            <div className="text-[9px]" style={{ color: "#475569" }}>{a.date}</div>
          </button>
        ))}
      </div>

      {/* Insight */}
      <div className="mx-4 mt-3 rounded-xl bg-[#111827] border border-[#1E293B] px-4 py-3">
        <div className="text-[13px] font-bold text-[#E2E8F0] mb-1 leading-snug">{d.insightHi}</div>
        <div className="text-[11px] text-[#94A3B8] leading-relaxed">{d.insightEn}</div>
      </div>

      {/* Lucky + Numbers side by side */}
      <div className="flex gap-2 mx-4 mt-2">
        <div className="flex-1 rounded-xl bg-[#111827] border border-[#1E293B] p-3 flex items-center gap-2">
          <div className="w-8 h-8 rounded-full shrink-0 border-2 border-[#1E293B]" style={{ backgroundColor: d.lucky }} />
          <div>
            <div className="text-[9px] uppercase tracking-wide mb-0.5" style={{ color: "#475569" }}>Lucky Color</div>
            <div className="text-[13px] font-bold text-[#E2E8F0]">{d.luckyName}</div>
          </div>
        </div>
        <div className="flex-1 rounded-xl bg-[#111827] border border-[#1E293B] p-3 flex items-center gap-2">
          <span className="text-xl">🔢</span>
          <div>
            <div className="text-[9px] uppercase tracking-wide mb-0.5" style={{ color: "#475569" }}>Lucky Nos</div>
            <div className="text-[13px] font-bold text-[#E2E8F0]">{d.nums.join(" · ")}</div>
          </div>
        </div>
      </div>

      {/* Dasha note */}
      <div className="mx-4 mt-2 mb-4 rounded-xl px-3 py-2.5 border flex gap-2 items-center"
        style={{ backgroundColor: "rgba(245,158,11,0.06)", borderColor: "rgba(245,158,11,0.18)" }}>
        <span className="text-base">🪐</span>
        <span className="text-[11px] leading-relaxed text-[#94A3B8]">Saturn Mahadasha · Mars Antardasha active</span>
      </div>
    </div>
  );
}
