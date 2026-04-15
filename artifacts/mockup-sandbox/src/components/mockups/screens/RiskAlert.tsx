import { useState } from "react";

const alerts = [
  {
    offset: 0, label: "Today", labelHi: "आज", emoji: "⚡", weekday: "Wednesday",
    date: "Apr 15", energy: "Challenging", energyColor: "#ef4444", score: 38,
    moonSign: "Scorpio", moonNakshatra: "Jyeshtha", moonHouse: 8,
    insightHi: "आज मंगल की दृष्टि तीव्र है। बड़े फैसले टालें।",
    insightEn: "Mars aspect is strong today. Avoid major decisions and financial risks.",
    tags: ["⚠ High Risk", "🚫 Avoid Travel", "📿 Pray Today"],
    saturnAspect: true, marsAspect: true, jupiterAspect: false,
    luckyColor: "#8b5cf6", luckyColorName: "Purple",
    luckyNumbers: [4, 13, 22],
    dasha: "Saturn Mahadasha · Mars Antardasha",
  },
  {
    offset: 1, label: "Tomorrow", labelHi: "कल", emoji: "🌤", weekday: "Thursday",
    date: "Apr 16", energy: "Neutral", energyColor: "#94a3b8", score: 61,
    moonSign: "Scorpio", moonNakshatra: "Mula", moonHouse: 9,
    insightHi: "गुरु की दृष्टि से दिन सामान्य रहेगा।",
    insightEn: "Jupiter's aspect brings stability. Moderate day for work.",
    tags: ["✅ Work OK", "🧘 Meditate"],
    saturnAspect: false, marsAspect: false, jupiterAspect: true,
    luckyColor: "#3b82f6", luckyColorName: "Blue",
    luckyNumbers: [3, 12, 21],
    dasha: "Saturn Mahadasha · Rahu Antardasha",
  },
  {
    offset: 2, label: "Day 3", labelHi: "+2", emoji: "✨", weekday: "Friday",
    date: "Apr 17", energy: "Good", energyColor: "#22c55e", score: 82,
    moonSign: "Sagittarius", moonNakshatra: "Mula", moonHouse: 9,
    insightHi: "शुक्र और गुरु की युति से शुभ दिन।",
    insightEn: "Venus–Jupiter conjunction brings prosperity and auspicious results.",
    tags: ["💰 Finance Good", "❤ Love Positive", "🎯 Focus"],
    saturnAspect: false, marsAspect: false, jupiterAspect: true,
    luckyColor: "#f59e0b", luckyColorName: "Gold",
    luckyNumbers: [6, 15, 24],
    dasha: "Saturn Mahadasha · Jupiter Antardasha",
  },
];

function ScoreBar({ score, color }: { score: number; color: string }) {
  return (
    <div className="h-1.5 rounded-full overflow-hidden mt-2" style={{ backgroundColor: "rgba(255,255,255,0.08)" }}>
      <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, backgroundColor: color }} />
    </div>
  );
}

export function RiskAlert() {
  const [selected, setSelected] = useState(0);
  const item = alerts[selected];

  return (
    <div className="min-h-screen bg-[#0B1220] font-sans flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-[#1E293B]">
        <button className="w-8 h-8 rounded-full bg-[#111827] border border-[#1E293B] flex items-center justify-center text-[#64748B] text-sm">←</button>
        <div className="flex-1">
          <div className="text-[#E2E8F0] font-bold text-[17px]">7-Day Risk Alerts</div>
          <div className="text-[#475569] text-[10px]">ग्रह आधारित सतर्कता</div>
        </div>
      </div>

      {/* Day selector strip */}
      <div className="flex gap-2 px-4 pt-3 overflow-x-auto pb-1">
        {alerts.map((a, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className="flex flex-col items-center px-3 py-2 rounded-xl shrink-0 transition-all border"
            style={{
              backgroundColor: selected === i ? `${a.energyColor}18` : "#111827",
              borderColor: selected === i ? `${a.energyColor}55` : "#1E293B",
            }}
          >
            <span className="text-base">{a.emoji}</span>
            <span className="text-[10px] font-bold mt-0.5" style={{ color: selected === i ? a.energyColor : "#94A3B8" }}>{a.label}</span>
            <span className="text-[9px]" style={{ color: "#475569" }}>{a.date}</span>
          </button>
        ))}
      </div>

      {/* Main card */}
      <div className="mx-4 mt-3 rounded-2xl overflow-hidden border"
        style={{ backgroundColor: "#111827", borderColor: `${item.energyColor}30` }}>
        {/* Top energy strip */}
        <div className="px-4 pt-4 pb-3" style={{ borderBottom: `1px solid ${item.energyColor}20` }}>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{item.emoji}</span>
                <div>
                  <div className="text-[#E2E8F0] font-bold text-[15px]">{item.weekday}, {item.date}</div>
                  <div className="text-[#475569] text-[10px]">{item.labelHi}</div>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[11px]" style={{ color: "#475569" }}>Energy Score</div>
              <div className="text-xl font-bold" style={{ color: item.energyColor }}>{item.score}</div>
            </div>
          </div>
          <ScoreBar score={item.score} color={item.energyColor} />
          <div className="flex gap-1 items-center mt-2">
            <div className="px-2 py-0.5 rounded-full text-[10px] font-bold border"
              style={{ backgroundColor: `${item.energyColor}18`, borderColor: `${item.energyColor}44`, color: item.energyColor }}>
              {item.energy}
            </div>
            {item.saturnAspect && <div className="text-[10px] text-[#ef4444]">⚠ Shani</div>}
            {item.marsAspect && <div className="text-[10px] text-[#f97316]">⚠ Mangal</div>}
            {item.jupiterAspect && <div className="text-[10px] text-[#22c55e]">✓ Guru</div>}
          </div>
        </div>

        {/* Moon info */}
        <div className="mx-3 mt-3 px-3 py-2 rounded-xl border flex items-center gap-2"
          style={{ backgroundColor: "rgba(0,0,0,0.25)", borderColor: "#1E293B" }}>
          <span className="text-sm">🌙</span>
          <span className="text-[11px]" style={{ color: "#94A3B8" }}>
            Moon in <span style={{ color: "#E2E8F0", fontWeight: 700 }}>{item.moonSign}</span>
            {" · "}<span style={{ color: "#E2E8F0" }}>{item.moonNakshatra}</span>
            {" · "}<span style={{ color: "#64748B" }}>House {item.moonHouse}</span>
          </span>
        </div>

        {/* Insights */}
        <div className="px-4 pt-3">
          <div className="text-[13px] font-semibold leading-snug mb-1" style={{ color: "#E2E8F0" }}>{item.insightHi}</div>
          <div className="text-[11px] leading-relaxed" style={{ color: "#94A3B8" }}>{item.insightEn}</div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 px-4 py-3">
          {item.tags.map((t, i) => (
            <div key={i} className="px-2 py-1 rounded-full border text-[10px]"
              style={{ backgroundColor: "#0B1220", borderColor: "#1E293B", color: "#94A3B8" }}>{t}</div>
          ))}
        </div>

        {/* Lucky strip */}
        <div className="flex gap-2 px-3 pb-3">
          <div className="flex-1 rounded-xl p-2 border" style={{ backgroundColor: "#0B1220", borderColor: "#1E293B" }}>
            <div className="text-[9px] uppercase tracking-wide mb-1" style={{ color: "#475569" }}>Lucky Color</div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.luckyColor }} />
              <span className="text-[12px] font-bold" style={{ color: "#E2E8F0" }}>{item.luckyColorName}</span>
            </div>
          </div>
          <div className="flex-1 rounded-xl p-2 border" style={{ backgroundColor: "#0B1220", borderColor: "#1E293B" }}>
            <div className="text-[9px] uppercase tracking-wide mb-1" style={{ color: "#475569" }}>Lucky Numbers</div>
            <span className="text-[12px] font-bold" style={{ color: "#E2E8F0" }}>{item.luckyNumbers.join(" · ")}</span>
          </div>
        </div>

        {/* Dasha note */}
        <div className="mx-3 mb-3 px-3 py-2 rounded-xl border flex gap-2"
          style={{ backgroundColor: "rgba(245,158,11,0.06)", borderColor: "rgba(245,158,11,0.18)" }}>
          <span className="text-sm">🪐</span>
          <span className="text-[11px] leading-relaxed" style={{ color: "#94A3B8" }}>{item.dasha}</span>
        </div>
      </div>
    </div>
  );
}
