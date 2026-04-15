export function FloatingPill() {
  const tabs = [
    { icon: "⌂", label: "Home", active: true },
    { icon: "✦", label: "Kundli", active: false },
    { icon: "✉", label: "Ask", active: false },
    { icon: "↗", label: "Insights", active: false },
    { icon: "🔔", label: "Notice", active: false },
    { icon: "◉", label: "Profile", active: false },
  ];

  return (
    <div style={{ fontFamily: "system-ui, sans-serif" }}
      className="min-h-screen flex items-end justify-center bg-[#0B1220] pb-0">

      {/* Phone shell */}
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

        {/* Floating pill bar */}
        <div className="px-5 pb-4">
          <div
            className="flex items-center justify-around h-[60px] rounded-[30px] border border-[#1E293B]"
            style={{
              background: "linear-gradient(180deg, #1A2235 0%, #111827 100%)",
              boxShadow: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(245,158,11,0.08)",
            }}
          >
            {tabs.map((tab) => (
              <div key={tab.label} className="flex flex-col items-center justify-center flex-1 py-1">
                {tab.active ? (
                  <div
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[#F59E0B]"
                    style={{ background: "rgba(245,158,11,0.15)" }}
                  >
                    <span className="text-base leading-none">{tab.icon}</span>
                    <span className="text-[11px] font-bold leading-none">{tab.label}</span>
                  </div>
                ) : (
                  <span className="text-[18px] leading-none" style={{ color: "#475569" }}>{tab.icon}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
