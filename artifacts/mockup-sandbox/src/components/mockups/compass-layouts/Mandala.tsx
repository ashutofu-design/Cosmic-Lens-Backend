const GOLD = "#f9d76b";
const GOLD_DIM = "#b8893a";
const BG = "#05070d";

// Vastu Purusha Mandala — authentic 3x3 layout
// Position | Deity (English) | Meaning
const CELLS = [
  { row: 0, col: 0, label: "NW", deity: "VAYU",   meaning: "AIR",      bright: false },
  { row: 0, col: 1, label: "N",  deity: "KUBERA", meaning: "WEALTH",   bright: true  },
  { row: 0, col: 2, label: "NE", deity: "ISHAAN", meaning: "DIVINITY", bright: false },
  { row: 1, col: 0, label: "W",  deity: "VARUNA", meaning: "WATER",    bright: true  },
  { row: 1, col: 1, label: "C",  deity: "BRAHMA", meaning: "CENTER",   bright: true, center: true },
  { row: 1, col: 2, label: "E",  deity: "SURYA",  meaning: "ENERGY",   bright: true  },
  { row: 2, col: 0, label: "SW", deity: "NIRITI", meaning: "EARTH",    bright: false },
  { row: 2, col: 1, label: "S",  deity: "YAMA",   meaning: "HONOR",    bright: true  },
  { row: 2, col: 2, label: "SE", deity: "AGNI",   meaning: "FIRE",     bright: false },
];

export function Mandala() {
  const cellSize = 96;
  const gap = 4;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6" style={{ background: BG }}>
      <div className="text-center mb-5">
        <h2 className="text-[20px] font-bold" style={{ color: "#fff8dc", letterSpacing: 1 }}>VASTU MANDALA</h2>
        <p className="text-[11px] mt-1" style={{ color: GOLD_DIM, letterSpacing: 2 }}>AUTHENTIC · 9-GRID · SACRED</p>
      </div>

      {/* Outer gold frame */}
      <div
        className="p-4 relative"
        style={{
          background: `linear-gradient(135deg, ${GOLD}, #3a2404, ${GOLD})`,
          borderRadius: 8,
          boxShadow: "0 0 30px rgba(249,215,107,0.15)",
        }}
      >
        <div className="p-3" style={{ background: BG, borderRadius: 4 }}>
          {/* Cardinal direction labels outside grid */}
          <div
            className="grid relative"
            style={{
              gridTemplateColumns: `repeat(3, ${cellSize}px)`,
              gridTemplateRows: `repeat(3, ${cellSize}px)`,
              gap: `${gap}px`,
            }}
          >
            {CELLS.map((c) => (
              <div
                key={c.label}
                className="flex flex-col items-center justify-center relative"
                style={{
                  background: c.center
                    ? `radial-gradient(circle, ${GOLD}33 0%, ${BG} 75%)`
                    : c.bright
                    ? `linear-gradient(135deg, ${GOLD}20, ${BG})`
                    : `linear-gradient(135deg, ${GOLD_DIM}15, ${BG})`,
                  border: `1px solid ${c.center ? GOLD : c.bright ? GOLD + "aa" : GOLD_DIM + "77"}`,
                  borderRadius: 2,
                }}
              >
                {/* Corner accents */}
                <div className="absolute top-1 left-1 w-2 h-2 border-l border-t" style={{ borderColor: GOLD }} />
                <div className="absolute top-1 right-1 w-2 h-2 border-r border-t" style={{ borderColor: GOLD }} />
                <div className="absolute bottom-1 left-1 w-2 h-2 border-l border-b" style={{ borderColor: GOLD }} />
                <div className="absolute bottom-1 right-1 w-2 h-2 border-r border-b" style={{ borderColor: GOLD }} />

                {c.center ? (
                  <>
                    {/* Brahma sthan — center symbol */}
                    <svg width="50" height="50" viewBox="0 0 50 50">
                      {/* 8-point star */}
                      {Array.from({ length: 8 }).map((_, i) => {
                        const a = (i * Math.PI * 2) / 8;
                        return (
                          <line
                            key={i}
                            x1="25"
                            y1="25"
                            x2={25 + 18 * Math.cos(a)}
                            y2={25 + 18 * Math.sin(a)}
                            stroke={GOLD}
                            strokeWidth="0.8"
                            opacity="0.7"
                          />
                        );
                      })}
                      <polygon
                        points="25,10 38,32 12,32"
                        fill="none"
                        stroke={GOLD}
                        strokeWidth="0.9"
                        opacity="0.8"
                      />
                      <polygon
                        points="25,40 12,18 38,18"
                        fill="none"
                        stroke={GOLD}
                        strokeWidth="0.9"
                        opacity="0.8"
                      />
                      <circle cx="25" cy="25" r="3" fill="#fff8dc" />
                      <circle cx="25" cy="25" r="6" fill="none" stroke={GOLD} strokeWidth="0.6" />
                    </svg>
                    <div className="text-[9px] font-bold mt-1" style={{ color: GOLD, letterSpacing: 1.2 }}>
                      {c.deity}
                    </div>
                  </>
                ) : (
                  <>
                    <div
                      className="text-[22px] font-black"
                      style={{ color: c.bright ? "#fff8dc" : GOLD }}
                    >
                      {c.label}
                    </div>
                    <div
                      className="text-[9px] font-bold mt-0.5"
                      style={{ color: c.bright ? GOLD : GOLD_DIM, letterSpacing: 1 }}
                    >
                      {c.deity}
                    </div>
                    <div
                      className="text-[7px] mt-0.5"
                      style={{ color: c.bright ? GOLD_DIM : "#6b5a2e", letterSpacing: 1.5 }}
                    >
                      {c.meaning}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Corner ornament dots */}
        {[
          [8, 8],
          [8, "calc(100% - 12px)"],
          ["calc(100% - 12px)", 8],
          ["calc(100% - 12px)", "calc(100% - 12px)"],
        ].map(([t, l], i) => (
          <div
            key={i}
            className="absolute"
            style={{ top: t, left: l, width: 4, height: 4, background: "#fff8dc", borderRadius: "50%" }}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="mt-5 px-4 py-2 rounded-full border" style={{ background: "rgba(249,215,107,0.06)", borderColor: "rgba(249,215,107,0.3)" }}>
        <span className="text-[12px]" style={{ color: GOLD }}>✦ Center: Brahma Sthan</span>
      </div>
    </div>
  );
}
