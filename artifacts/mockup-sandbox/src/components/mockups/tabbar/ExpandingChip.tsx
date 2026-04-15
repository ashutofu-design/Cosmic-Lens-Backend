import { useState } from "react";

export function ExpandingChip() {
  const [active, setActive] = useState(0);

  const tabs = [
    { icon: "⌂", label: "Home"     },
    { icon: "✦", label: "Kundli"   },
    { icon: "✉", label: "Ask"      },
    { icon: "↗", label: "Insights" },
    { icon: "🔔", label: "Notice"   },
    { icon: "◉", label: "Profile"  },
  ];

  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}
      className="min-h-screen flex items-end justify-center bg-[#0B1220]">

      <div className="relative w-[390px] h-[220px] bg-[#0B1220] overflow-hidden flex flex-col">

        {/* Content placeholder */}
        <div className="flex-1 flex flex-col gap-2 px-4 pt-4">
          <div className="h-8 w-48 rounded-lg bg-[#1E293B] opacity-60" />
          <div className="h-20 rounded-2xl bg-[#111827] border border-[#1E293B] flex items-center px-4 gap-3">
            <div className="w-10 h-10 rounded-full bg-[#F59E0B22] border border-[#F59E0B44] flex items-center justify-center text-[#F59E0B] text-lg">✦</div>
            <div className="flex flex-col gap-1">
              <div className="h-3 w-32 rounded bg-[#1E293B]" />
              <div className="h-2 w-24 rounded bg-[#1E293B] opacity-50" />
            </div>
          </div>
        </div>

        {/* Expanding chip bar */}
        <div
          className="flex items-center border-t border-[#1E293B]"
          style={{ height: 72, background: "#111827", paddingBottom: 6 }}
        >
          {tabs.map((tab, i) => {
            const isActive = i === active;
            return (
              <button
                key={tab.label}
                onClick={() => setActive(i)}
                className="flex items-center justify-center transition-all duration-200 h-full"
                style={{
                  flex: isActive ? 2.6 : 1,
                  border: "none",
                  background: "transparent",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                {isActive ? (
                  /* Active: horizontal chip with icon + label */
                  <div
                    className="flex items-center gap-1.5 px-3 py-2 rounded-2xl"
                    style={{
                      background: "rgba(245,158,11,0.15)",
                      border: "1px solid rgba(245,158,11,0.25)",
                    }}
                  >
                    <span className="text-base leading-none" style={{ color: "#F59E0B" }}>{tab.icon}</span>
                    <span className="text-[11px] font-bold leading-none" style={{ color: "#F59E0B" }}>{tab.label}</span>
                  </div>
                ) : (
                  /* Inactive: icon stacked above small muted label */
                  <div className="flex flex-col items-center justify-center gap-[3px]">
                    <span className="text-[17px] leading-none" style={{ color: "#94A3B8" }}>{tab.icon}</span>
                    <span className="text-[9px] leading-none" style={{ color: "#94A3B8" }}>{tab.label}</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
