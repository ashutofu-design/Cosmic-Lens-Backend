const DIRS = [
  { deg: 0,   short: "N",  deity: "KUBERA",  bright: true  },
  { deg: 45,  short: "NE", deity: "ISHAAN",  bright: false },
  { deg: 90,  short: "E",  deity: "SURYA",   bright: true  },
  { deg: 135, short: "SE", deity: "AGNI",    bright: false },
  { deg: 180, short: "S",  deity: "YAMA",    bright: true  },
  { deg: 225, short: "SW", deity: "NIRITI",  bright: false },
  { deg: 270, short: "W",  deity: "VARUNA",  bright: true  },
  { deg: 315, short: "NW", deity: "VAYU",    bright: false },
];

const GOLD = "#f9d76b";
const GOLD_DIM = "#b8893a";
const BG = "#05070d";

const SIZE = 320;
const CX = SIZE / 2, CY = SIZE / 2;
const R_BEZEL = SIZE * 0.49;
const R_INNER_BEZEL = SIZE * 0.46;
const R_SECTOR_OUT = SIZE * 0.435;
const R_SECTOR_IN = SIZE * 0.18;
const R_LABEL = SIZE * 0.37;
const R_DEITY = SIZE * 0.285;
const R_CENTER = SIZE * 0.15;

function toRad(b: number) { return ((b - 90) * Math.PI) / 180; }
function wedge(a0: number, a1: number, r1: number, r2: number) {
  const s0 = toRad(a0), s1 = toRad(a1);
  const x1 = CX + r1 * Math.cos(s0), y1 = CY + r1 * Math.sin(s0);
  const x2 = CX + r2 * Math.cos(s0), y2 = CY + r2 * Math.sin(s0);
  const x3 = CX + r2 * Math.cos(s1), y3 = CY + r2 * Math.sin(s1);
  const x4 = CX + r1 * Math.cos(s1), y4 = CY + r1 * Math.sin(s1);
  return `M${x1},${y1} L${x2},${y2} A${r2},${r2},0,0,1,${x3},${y3} L${x4},${y4} A${r1},${r1},0,0,0,${x1},${y1}Z`;
}

export function Classic() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6" style={{ background: BG }}>
      <div className="text-center mb-5">
        <h2 className="text-[20px] font-bold" style={{ color: "#fff8dc", letterSpacing: 1 }}>CLASSIC CIRCLE</h2>
        <p className="text-[11px] mt-1" style={{ color: GOLD_DIM, letterSpacing: 2 }}>TRADITIONAL · BEZEL · RINGS</p>
      </div>

      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        <defs>
          <radialGradient id="bezel-grad" cx="35%" cy="25%" r="90%">
            <stop offset="0" stopColor="#fff2b8" />
            <stop offset="0.5" stopColor={GOLD} />
            <stop offset="1" stopColor="#3a2404" />
          </radialGradient>
          <radialGradient id="center-grad" cx="50%" cy="50%" r="65%">
            <stop offset="0" stopColor="#0a0f1a" />
            <stop offset="1" stopColor="#000000" />
          </radialGradient>
          {DIRS.map(d => (
            <radialGradient key={`sg-${d.short}`} id={`sg-${d.short}`} cx="50%" cy="50%" r="75%">
              <stop offset="0" stopColor={d.bright ? GOLD : GOLD_DIM} stopOpacity={d.bright ? "0.22" : "0.10"} />
              <stop offset="1" stopColor={BG} stopOpacity="1" />
            </radialGradient>
          ))}
        </defs>

        {/* Outer bezel */}
        <circle cx={CX} cy={CY} r={R_BEZEL} fill="url(#bezel-grad)" />
        <circle cx={CX} cy={CY} r={R_INNER_BEZEL} fill={BG} />

        {/* 72 tick marks */}
        {Array.from({ length: 72 }).map((_, i) => {
          const ang = toRad(i * 5);
          const r1 = R_INNER_BEZEL - 2;
          const r2 = i % 9 === 0 ? R_INNER_BEZEL - 12 : R_INNER_BEZEL - 6;
          return (
            <line key={i}
              x1={CX + r1 * Math.cos(ang)} y1={CY + r1 * Math.sin(ang)}
              x2={CX + r2 * Math.cos(ang)} y2={CY + r2 * Math.sin(ang)}
              stroke={GOLD} strokeWidth={i % 9 === 0 ? 1.3 : 0.5} opacity={i % 9 === 0 ? 0.9 : 0.4} />
          );
        })}

        {/* Sectors */}
        {DIRS.map(d => (
          <g key={d.short}>
            <path d={wedge(d.deg - 22.5, d.deg + 22.5, R_SECTOR_IN, R_SECTOR_OUT)} fill={`url(#sg-${d.short})`} />
            <line
              x1={CX + R_SECTOR_IN * Math.cos(toRad(d.deg - 22.5))}
              y1={CY + R_SECTOR_IN * Math.sin(toRad(d.deg - 22.5))}
              x2={CX + R_SECTOR_OUT * Math.cos(toRad(d.deg - 22.5))}
              y2={CY + R_SECTOR_OUT * Math.sin(toRad(d.deg - 22.5))}
              stroke={GOLD} strokeWidth={0.6} opacity={0.5} />
          </g>
        ))}

        {/* Divider rings */}
        <circle cx={CX} cy={CY} r={R_SECTOR_OUT} fill="none" stroke={GOLD} strokeWidth={1} opacity={0.6} />
        <circle cx={CX} cy={CY} r={R_SECTOR_IN} fill="none" stroke={GOLD} strokeWidth={1.2} opacity={0.7} />

        {/* Labels */}
        {DIRS.map(d => {
          const a = toRad(d.deg);
          const lx = CX + R_LABEL * Math.cos(a), ly = CY + R_LABEL * Math.sin(a);
          const dx = CX + R_DEITY * Math.cos(a), dy = CY + R_DEITY * Math.sin(a);
          const isCard = d.deg % 90 === 0;
          return (
            <g key={`l-${d.short}`}>
              <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
                fill={isCard ? "#fff8dc" : GOLD} fontSize={isCard ? 20 : 14} fontWeight="900">
                {d.short}
              </text>
              <text x={dx} y={dy} textAnchor="middle" dominantBaseline="middle"
                fill={d.bright ? GOLD : GOLD_DIM} fontSize={9} fontWeight="700" letterSpacing="1.5">
                {d.deity}
              </text>
            </g>
          );
        })}

        {/* North arrow */}
        <polygon points={`${CX},${CY - R_SECTOR_OUT - 6} ${CX - 8},${CY - R_SECTOR_OUT + 6} ${CX + 8},${CY - R_SECTOR_OUT + 6}`}
          fill={GOLD} stroke="#3a2404" strokeWidth={0.8} />

        {/* Center yantra */}
        <circle cx={CX} cy={CY} r={R_CENTER} fill="url(#center-grad)" stroke={GOLD} strokeWidth={1.5} />
        {/* 8-point star */}
        <g opacity={0.8}>
          {Array.from({ length: 8 }).map((_, i) => {
            const a = toRad(i * 45);
            const x = CX + (R_CENTER - 4) * Math.cos(a), y = CY + (R_CENTER - 4) * Math.sin(a);
            return <line key={i} x1={CX} y1={CY} x2={x} y2={y} stroke={GOLD} strokeWidth={0.4} opacity={0.5} />;
          })}
        </g>
        {/* Two triangles shatkona */}
        <polygon points={`${CX},${CY - R_CENTER + 8} ${CX - (R_CENTER - 8) * 0.87},${CY + (R_CENTER - 8) * 0.5} ${CX + (R_CENTER - 8) * 0.87},${CY + (R_CENTER - 8) * 0.5}`}
          fill="none" stroke={GOLD} strokeWidth={0.8} opacity={0.75} />
        <polygon points={`${CX},${CY + R_CENTER - 8} ${CX - (R_CENTER - 8) * 0.87},${CY - (R_CENTER - 8) * 0.5} ${CX + (R_CENTER - 8) * 0.87},${CY - (R_CENTER - 8) * 0.5}`}
          fill="none" stroke={GOLD} strokeWidth={0.8} opacity={0.75} />
        {/* Center dot */}
        <circle cx={CX} cy={CY} r={6} fill="#fff8dc" />
        <circle cx={CX} cy={CY} r={10} fill="none" stroke={GOLD} strokeWidth={0.8} opacity={0.7} />
      </svg>

      <div className="mt-5 px-4 py-2 rounded-full border" style={{ background: "rgba(249,215,107,0.06)", borderColor: "rgba(249,215,107,0.3)" }}>
        <span className="text-[12px]" style={{ color: GOLD }}>✦ Ideal Direction: North-East</span>
      </div>
    </div>
  );
}
