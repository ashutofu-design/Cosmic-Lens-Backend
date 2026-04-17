const GOLD = "#f9d76b";
const GOLD_DIM = "#b8893a";
const BG = "#05070d";

const DIRS = [
  { idx: 0, short: "N",  deity: "KUBERA",  bright: true  },
  { idx: 1, short: "NE", deity: "ISHAAN",  bright: false },
  { idx: 2, short: "E",  deity: "SURYA",   bright: true  },
  { idx: 3, short: "SE", deity: "AGNI",    bright: false },
  { idx: 4, short: "S",  deity: "YAMA",    bright: true  },
  { idx: 5, short: "SW", deity: "NIRITI",  bright: false },
  { idx: 6, short: "W",  deity: "VARUNA",  bright: true  },
  { idx: 7, short: "NW", deity: "VAYU",    bright: false },
];

const SIZE = 340;
const CX = SIZE / 2, CY = SIZE / 2;
const R_OUT = SIZE * 0.48;
const R_INNER = SIZE * 0.17;
const R_LABEL = SIZE * 0.40;  // short code near outer edge
const R_DEITY = SIZE * 0.30;  // deity name in middle of sector ring, clear of center

// 8 vertices of an octagon (rotated so flat edges face N/S/E/W would be weird; use vertex-at-top)
function octagonPoints(r: number) {
  const pts: [number, number][] = [];
  for (let i = 0; i < 8; i++) {
    const a = (-Math.PI / 2) + (i * Math.PI * 2) / 8; // vertex at top (N)
    pts.push([CX + r * Math.cos(a), CY + r * Math.sin(a)]);
  }
  return pts;
}

// Wedge (triangular slice) from center-ring to outer octagon edge
function slicePath(idx: number, rOut: number, rIn: number) {
  const a0 = (-Math.PI / 2) + ((idx - 0.5) * Math.PI * 2) / 8;
  const a1 = (-Math.PI / 2) + ((idx + 0.5) * Math.PI * 2) / 8;
  const x1 = CX + rIn * Math.cos(a0), y1 = CY + rIn * Math.sin(a0);
  const x2 = CX + rOut * Math.cos(a0), y2 = CY + rOut * Math.sin(a0);
  const x3 = CX + rOut * Math.cos(a1), y3 = CY + rOut * Math.sin(a1);
  const x4 = CX + rIn * Math.cos(a1), y4 = CY + rIn * Math.sin(a1);
  return `M${x1},${y1} L${x2},${y2} L${x3},${y3} L${x4},${y4} Z`;
}

export function Octagon() {
  const outerPts = octagonPoints(R_OUT);
  const innerPts = octagonPoints(R_OUT * 0.96);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6" style={{ background: BG }}>
      <div className="text-center mb-5">
        <h2 className="text-[20px] font-bold" style={{ color: "#fff8dc", letterSpacing: 1 }}>OCTAGON DIAL</h2>
        <p className="text-[11px] mt-1" style={{ color: GOLD_DIM, letterSpacing: 2 }}>GEOMETRIC · FACETED · MODERN</p>
      </div>

      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        <defs>
          <linearGradient id="oct-gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#fff2b8" />
            <stop offset="0.5" stopColor={GOLD} />
            <stop offset="1" stopColor="#3a2404" />
          </linearGradient>
          {DIRS.map(d => (
            <linearGradient key={`og-${d.short}`} id={`og-${d.short}`} x1="0.5" y1="0" x2="0.5" y2="1">
              <stop offset="0" stopColor={d.bright ? GOLD : GOLD_DIM} stopOpacity={d.bright ? "0.22" : "0.10"} />
              <stop offset="1" stopColor={BG} stopOpacity="1" />
            </linearGradient>
          ))}
          <radialGradient id="oct-center" cx="50%" cy="50%" r="60%">
            <stop offset="0" stopColor="#0a0f1a" />
            <stop offset="1" stopColor="#000" />
          </radialGradient>
        </defs>

        {/* Outer octagon gold frame */}
        <polygon
          points={outerPts.map(p => p.join(",")).join(" ")}
          fill="url(#oct-gold)"
        />
        {/* Inner octagon (background) */}
        <polygon
          points={innerPts.map(p => p.join(",")).join(" ")}
          fill={BG}
          stroke={GOLD}
          strokeWidth="0.6"
          opacity="0.8"
        />

        {/* 8 triangular sector slices */}
        {DIRS.map(d => (
          <g key={`s-${d.short}`}>
            <path d={slicePath(d.idx, R_OUT * 0.94, R_INNER)} fill={`url(#og-${d.short})`} />
            {/* divider line */}
            {(() => {
              const a = (-Math.PI / 2) + ((d.idx - 0.5) * Math.PI * 2) / 8;
              const x1 = CX + R_INNER * Math.cos(a), y1 = CY + R_INNER * Math.sin(a);
              const x2 = CX + R_OUT * 0.94 * Math.cos(a), y2 = CY + R_OUT * 0.94 * Math.sin(a);
              return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={GOLD} strokeWidth="0.7" opacity="0.5" />;
            })()}
          </g>
        ))}

        {/* Vertex rivets on inner octagon */}
        {innerPts.map((p, i) => (
          <g key={`rv-${i}`}>
            <circle cx={p[0]} cy={p[1]} r="3.2" fill="#3a2404" />
            <circle cx={p[0]} cy={p[1]} r="2" fill={GOLD} />
            <circle cx={p[0] - 0.6} cy={p[1] - 0.6} r="0.8" fill="#fff8dc" />
          </g>
        ))}

        {/* Direction labels */}
        {DIRS.map(d => {
          const a = (-Math.PI / 2) + (d.idx * Math.PI * 2) / 8;
          const lx = CX + R_LABEL * Math.cos(a), ly = CY + R_LABEL * Math.sin(a);
          const dx = CX + R_DEITY * Math.cos(a), dy = CY + R_DEITY * Math.sin(a);
          const isCard = d.idx % 2 === 0;
          return (
            <g key={`l-${d.short}`}>
              <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
                fill={isCard ? "#fff8dc" : GOLD} fontSize={isCard ? 20 : 14} fontWeight="900">
                {d.short}
              </text>
              <text x={dx} y={dy + (isCard ? 12 : 10)} textAnchor="middle" dominantBaseline="middle"
                fill={d.bright ? GOLD : GOLD_DIM} fontSize={8} fontWeight="700" letterSpacing="1.3">
                {d.deity}
              </text>
            </g>
          );
        })}

        {/* Center octagon yantra */}
        <polygon
          points={octagonPoints(R_INNER).map(p => p.join(",")).join(" ")}
          fill="url(#oct-center)"
          stroke={GOLD}
          strokeWidth="1.4"
        />
        {/* Inner lines from center to each vertex */}
        {octagonPoints(R_INNER - 4).map((p, i) => (
          <line key={`cl-${i}`} x1={CX} y1={CY} x2={p[0]} y2={p[1]} stroke={GOLD} strokeWidth="0.4" opacity="0.5" />
        ))}
        {/* Shatkona triangles */}
        <polygon points={`${CX},${CY - R_INNER + 8} ${CX - (R_INNER - 8) * 0.87},${CY + (R_INNER - 8) * 0.5} ${CX + (R_INNER - 8) * 0.87},${CY + (R_INNER - 8) * 0.5}`}
          fill="none" stroke={GOLD} strokeWidth="0.9" opacity="0.8" />
        <polygon points={`${CX},${CY + R_INNER - 8} ${CX - (R_INNER - 8) * 0.87},${CY - (R_INNER - 8) * 0.5} ${CX + (R_INNER - 8) * 0.87},${CY - (R_INNER - 8) * 0.5}`}
          fill="none" stroke={GOLD} strokeWidth="0.9" opacity="0.8" />
        <circle cx={CX} cy={CY} r="6" fill="#fff8dc" />
        <circle cx={CX} cy={CY} r="11" fill="none" stroke={GOLD} strokeWidth="0.8" opacity="0.7" />

        {/* North vertex pointer */}
        <polygon
          points={`${CX},${CY - R_OUT - 2} ${CX - 7},${CY - R_OUT + 10} ${CX + 7},${CY - R_OUT + 10}`}
          fill={GOLD} stroke="#3a2404" strokeWidth="0.8"
        />
      </svg>

      <div className="mt-5 px-4 py-2 rounded-full border" style={{ background: "rgba(249,215,107,0.06)", borderColor: "rgba(249,215,107,0.3)" }}>
        <span className="text-[12px]" style={{ color: GOLD }}>✦ Ideal Direction: North-East</span>
      </div>
    </div>
  );
}
