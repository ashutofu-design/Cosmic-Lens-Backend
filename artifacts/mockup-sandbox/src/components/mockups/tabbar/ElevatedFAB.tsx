export function ElevatedFAB() {
  const leftTabs  = [
    { icon: "⌂", label: "Home",     active: true  },
    { icon: "✉", label: "Ask",      active: false },
  ];
  const rightTabs = [
    { icon: "↗", label: "Insights", active: false },
    { icon: "◉", label: "Profile",  active: false },
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

        {/* Tab bar with notch */}
        <div className="relative" style={{ height: 76 }}>
          {/* SVG curved notch background */}
          <svg
            viewBox="0 0 390 76"
            width="390"
            height="76"
            className="absolute inset-0"
            preserveAspectRatio="none"
          >
            <path
              d="M0,1 L155,1 Q175,1 182,8 Q190,24 195,28 Q200,24 208,8 Q215,1 235,1 L390,1 L390,76 L0,76 Z"
              fill="#111827"
              stroke="#1E293B"
              strokeWidth="1"
            />
          </svg>

          {/* Left tabs */}
          <div className="absolute left-0 bottom-0 flex" style={{ width: 155, height: 68 }}>
            {leftTabs.map(tab => (
              <div key={tab.label} className="flex-1 flex flex-col items-center justify-center gap-1 pb-2">
                <span className="text-lg leading-none" style={{ color: tab.active ? "#F59E0B" : "#475569" }}>{tab.icon}</span>
                <span className="text-[10px] leading-none font-semibold" style={{ color: tab.active ? "#F59E0B" : "#475569" }}>{tab.label}</span>
                {tab.active && <div className="absolute top-0 w-8 h-[2px] rounded-full bg-[#F59E0B]" />}
              </div>
            ))}
          </div>

          {/* Right tabs */}
          <div className="absolute right-0 bottom-0 flex" style={{ width: 155, height: 68 }}>
            {rightTabs.map(tab => (
              <div key={tab.label} className="flex-1 flex flex-col items-center justify-center gap-1 pb-2">
                <span className="text-lg leading-none" style={{ color: "#475569" }}>{tab.icon}</span>
                <span className="text-[10px] leading-none" style={{ color: "#475569" }}>{tab.label}</span>
              </div>
            ))}
          </div>

          {/* Center elevated FAB — Kundli */}
          <div className="absolute left-1/2 -translate-x-1/2" style={{ bottom: 20 }}>
            <div
              className="w-14 h-14 rounded-full flex flex-col items-center justify-center gap-0.5 border-2 border-[#F59E0B44]"
              style={{
                background: "linear-gradient(135deg, #F59E0B, #EA580C)",
                boxShadow: "0 0 20px rgba(245,158,11,0.5), 0 4px 16px rgba(0,0,0,0.5)",
              }}
            >
              <span className="text-xl leading-none text-white">✦</span>
              <span className="text-[9px] text-white font-bold leading-none">Kundli</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
