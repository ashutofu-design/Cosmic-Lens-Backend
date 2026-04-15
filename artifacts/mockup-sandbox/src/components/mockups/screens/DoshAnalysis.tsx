import { useState } from "react";

const doshas = [
  {
    icon: "🔴", name: "Manglik Dosh", hindi: "मांगलिक दोष",
    sev: "present", sevLabel: "Present", color: "#f97316", bg: "rgba(249,115,22,0.12)",
    headline: "Mars in 4th House — Manglik Dosh Active",
    desc: "Mars in houses 1, 4, 7, 8, or 12 creates Manglik Dosh, which can affect marriage and relationships.",
    remedies: [
      "Perform Kumbh Vivah before marriage to neutralize",
      "Offer sindoor to Hanuman ji on Tuesdays",
      "Wear or keep a Mangal Yantra at home",
    ],
    planetNote: "Mars: House 4",
  },
  {
    icon: "🐍", name: "Kalsarp Dosh", hindi: "कालसर्प दोष",
    sev: "mild", sevLabel: "Mild", color: "#fbbf24", bg: "rgba(251,191,36,0.1)",
    headline: "Partial Kalsarp — Some Planets on Rahu–Ketu Axis",
    desc: "Partial Kalsarp forms when some (not all) planets fall between the Rahu–Ketu axis. Minor delays possible.",
    remedies: [
      "Offer milk to a serpent idol on Nagpanchami",
      "Chant Mahamrityunjay mantra 108 times daily",
    ],
    planetNote: "Rahu: House 11 | Ketu: House 5",
  },
  {
    icon: "👣", name: "Pitra Dosh", hindi: "पितृ दोष",
    sev: "absent", sevLabel: "Not Present", color: "#22c55e", bg: "rgba(34,197,94,0.1)",
    headline: "Sun & Rahu not conjunct — No Pitra Dosh",
    desc: "No Pitra Dosh found. Ancestors are at peace in your chart.",
    remedies: [],
    planetNote: "Sun: House 11",
  },
  {
    icon: "😶‍🌫️", name: "Shani Dosh", hindi: "शनि दोष",
    sev: "absent", sevLabel: "Not Present", color: "#22c55e", bg: "rgba(34,197,94,0.1)",
    headline: "Saturn is well-placed — No Shani Dosh",
    desc: "Saturn is not adversely placed. No Sade Sati or Shani Dosh at this time.",
    remedies: [],
    planetNote: "Saturn: House 7",
  },
];

export function DoshAnalysis() {
  const [expanded, setExpanded] = useState<number | null>(0);

  const presentCount = doshas.filter(d => d.sev !== "absent").length;
  const clearCount = doshas.filter(d => d.sev === "absent").length;

  return (
    <div className="min-h-screen bg-[#0B1220] font-sans overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-3 border-b border-[#1E293B]">
        <button className="w-8 h-8 rounded-full bg-[#111827] border border-[#1E293B] flex items-center justify-center text-[#64748B] text-sm">←</button>
        <div className="flex-1">
          <div className="text-[#E2E8F0] font-bold text-[17px] leading-tight">Dosh Analysis</div>
          <div className="text-[#475569] text-[10px]">दोष विश्लेषण</div>
        </div>
        <div className="text-[10px] text-[#64748B] bg-[#111827] border border-[#1E293B] px-2 py-1 rounded-full">Demo Mode</div>
      </div>

      <div className="px-4 pt-4 flex flex-col gap-3">
        {/* Summary row */}
        <div className="flex gap-2">
          <div className="flex-1 rounded-xl bg-[#111827] border border-[#1E293B] p-3 text-center">
            <div className="text-[#F97316] font-bold text-xl">{presentCount}</div>
            <div className="text-[#475569] text-[9px] mt-0.5 uppercase tracking-wide">Found</div>
          </div>
          <div className="flex-1 rounded-xl bg-[#111827] border border-[#1E293B] p-3 text-center">
            <div className="text-[#EF4444] font-bold text-xl">1</div>
            <div className="text-[#475569] text-[9px] mt-0.5 uppercase tracking-wide">Strong</div>
          </div>
          <div className="flex-1 rounded-xl bg-[#111827] border border-[#1E293B] p-3 text-center">
            <div className="text-[#22C55E] font-bold text-xl">{clearCount}</div>
            <div className="text-[#475569] text-[9px] mt-0.5 uppercase tracking-wide">Clear</div>
          </div>
        </div>

        {/* Dosh cards */}
        {doshas.map((dosh, i) => (
          <div
            key={i}
            className="rounded-2xl bg-[#111827] overflow-hidden cursor-pointer"
            style={{ border: `1px solid ${dosh.color}30`, borderLeftWidth: 3, borderLeftColor: dosh.color }}
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            <div className="flex items-center gap-3 px-4 pt-3 pb-1">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-base"
                style={{ backgroundColor: dosh.bg }}>
                {dosh.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[#E2E8F0] font-bold text-[13px]">{dosh.name}</div>
                <div className="text-[#475569] text-[10px]">{dosh.hindi}</div>
              </div>
              <div className="text-[10px] font-bold px-2 py-1 rounded-full shrink-0"
                style={{ backgroundColor: dosh.bg, color: dosh.color }}>
                {dosh.sevLabel}
              </div>
              <span className="text-[#475569] text-[10px]">{expanded === i ? "▲" : "▼"}</span>
            </div>

            <div className="px-4 pb-2 text-[11px] font-semibold" style={{ color: dosh.color }}>
              {dosh.headline}
            </div>

            {expanded === i && (
              <div className="mx-3 mb-3 rounded-xl p-3" style={{ backgroundColor: "rgba(0,0,0,0.3)", border: `1px solid ${dosh.color}20` }}>
                <p className="text-[#94A3B8] text-[11px] leading-relaxed mb-2">{dosh.desc}</p>
                {dosh.remedies.length > 0 && (
                  <>
                    <div className="text-[9px] font-bold uppercase tracking-widest mb-2" style={{ color: dosh.color }}>
                      Upay (Remedies)
                    </div>
                    {dosh.remedies.map((r, j) => (
                      <div key={j} className="flex gap-2 mb-2">
                        <div className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0"
                          style={{ backgroundColor: dosh.bg, color: dosh.color }}>{j + 1}</div>
                        <div className="text-[#94A3B8] text-[10px] leading-relaxed">{r}</div>
                      </div>
                    ))}
                  </>
                )}
                <div className="flex gap-1 items-center mt-2 text-[#475569] text-[10px]">
                  <span>ℹ</span><span>{dosh.planetNote}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
