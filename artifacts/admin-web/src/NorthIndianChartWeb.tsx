/** North / South Indian kundli charts — admin web (reference-app style). */

const VB = 400;
const CX = 200;
const CY = 200;

export const SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
] as const;

const SIGN_ALIASES: Record<string, number> = {
  mesh: 0,
  aries: 0,
  vrishabh: 1,
  vrishabha: 1,
  taurus: 1,
  mithun: 2,
  mithuna: 2,
  gemini: 2,
  kark: 3,
  karka: 3,
  cancer: 3,
  singh: 4,
  simha: 4,
  leo: 4,
  kanya: 5,
  virgo: 5,
  tula: 6,
  libra: 6,
  vrischik: 7,
  vrishchik: 7,
  scorpio: 7,
  dhanu: 8,
  dhanus: 8,
  sagittarius: 8,
  makar: 9,
  makara: 9,
  capricorn: 9,
  kumbh: 10,
  kumbha: 10,
  aquarius: 10,
  meen: 11,
  meena: 11,
  pisces: 11,
};

export const PLANET_SHORT: Record<string, string> = {
  Sun: "Su",
  Moon: "Mo",
  Mars: "Ma",
  Mercury: "Me",
  Jupiter: "Ju",
  Venus: "Ve",
  Saturn: "Sa",
  Rahu: "Ra",
  Ketu: "Ke",
  Ascendant: "Asc",
  Lagna: "Asc",
  Uranus: "Ur",
  Neptune: "Ne",
  Pluto: "Pl",
};

/** Colors close to popular kundli apps (screenshots). */
export const PLANET_CLR: Record<string, string> = {
  Sun: "#e67e22",
  Moon: "#1f2937",
  Mars: "#dc2626",
  Mercury: "#16a34a",
  Jupiter: "#ca8a04",
  Venus: "#a855f7",
  Saturn: "#0f766e",
  Rahu: "#111827",
  Ketu: "#c2410c",
  Ascendant: "#64748b",
  Lagna: "#64748b",
  Uranus: "#ca8a04",
  Neptune: "#2563eb",
  Pluto: "#111827",
};

/** Sign lord for KP-style tables. */
export const SIGN_LORDS = [
  "Mars",
  "Venus",
  "Mercury",
  "Moon",
  "Sun",
  "Mercury",
  "Venus",
  "Mars",
  "Jupiter",
  "Saturn",
  "Saturn",
  "Jupiter",
] as const;

const HOUSE_CENTERS: Record<number, { x: number; y: number }> = {
  1: { x: 200, y: 105 },
  2: { x: 105, y: 48 },
  3: { x: 48, y: 105 },
  4: { x: 105, y: 200 },
  5: { x: 48, y: 295 },
  6: { x: 105, y: 352 },
  7: { x: 200, y: 295 },
  8: { x: 295, y: 352 },
  9: { x: 352, y: 295 },
  10: { x: 295, y: 200 },
  11: { x: 352, y: 105 },
  12: { x: 295, y: 48 },
};

/** South Indian fixed sign cells (sign index 0=Aries …). */
const SOUTH_CELLS: { signIdx: number; x: number; y: number; w: number; h: number }[] = [
  { signIdx: 11, x: 0, y: 0, w: 100, h: 100 },
  { signIdx: 0, x: 100, y: 0, w: 100, h: 100 },
  { signIdx: 1, x: 200, y: 0, w: 100, h: 100 },
  { signIdx: 2, x: 300, y: 0, w: 100, h: 100 },
  { signIdx: 10, x: 0, y: 100, w: 100, h: 100 },
  { signIdx: 3, x: 300, y: 100, w: 100, h: 100 },
  { signIdx: 9, x: 0, y: 200, w: 100, h: 100 },
  { signIdx: 4, x: 300, y: 200, w: 100, h: 100 },
  { signIdx: 8, x: 0, y: 300, w: 100, h: 100 },
  { signIdx: 7, x: 100, y: 300, w: 100, h: 100 },
  { signIdx: 6, x: 200, y: 300, w: 100, h: 100 },
  { signIdx: 5, x: 300, y: 300, w: 100, h: 100 },
];

export type ChartPlanet = {
  name?: string;
  house?: number;
  sign?: string;
  rashi?: string;
  retrograde?: boolean;
  degrees?: string;
  degree?: number | string;
};

export type ChartStyle = "north" | "south";

export function resolveSignIndex(raw?: string | null): number {
  if (raw == null || String(raw).trim() === "") return 0;
  const s = String(raw).trim();
  if (/^\d+$/.test(s)) {
    const n = Number(s);
    if (n >= 1 && n <= 12) return n - 1;
    if (n >= 0 && n <= 11) return n;
  }
  const lower = s.toLowerCase();
  if (lower in SIGN_ALIASES) return SIGN_ALIASES[lower];
  const full = SIGNS.findIndex((x) => x.toLowerCase() === lower || lower.startsWith(x.toLowerCase()));
  if (full >= 0) return full;
  const first = lower.split(/[\s(/·-]+/)[0];
  if (first in SIGN_ALIASES) return SIGN_ALIASES[first];
  const partial = SIGNS.findIndex((x) => x.toLowerCase().startsWith(first.slice(0, 3)));
  return partial >= 0 ? partial : 0;
}

export function houseFromSign(signIdx: number, lagnaIdx: number): number {
  return ((signIdx - lagnaIdx + 12) % 12) + 1;
}

export function shortPlanet(name?: string): string {
  const n = (name || "?").trim();
  return PLANET_SHORT[n] || n.slice(0, 2);
}

function formatDeg(p: ChartPlanet): string {
  if (typeof p.degrees === "string" && p.degrees.trim()) {
    const m = p.degrees.match(/[\d.]+/);
    return m ? `${Number(m[0]).toFixed(2)}°` : "";
  }
  if (p.degree != null && String(p.degree).trim() !== "") {
    const n = Number(p.degree);
    return Number.isFinite(n) ? `${n.toFixed(2)}°` : "";
  }
  return "";
}

function planetLabel(p: ChartPlanet, withDeg: boolean): string {
  const short = shortPlanet(p.name);
  const ret = p.retrograde ? "®" : "";
  if (!withDeg) return `${short}${ret}`;
  const deg = formatDeg(p);
  return deg ? `${short}${ret}-${deg}` : `${short}${ret}`;
}

function normalizePlanets(
  planets: ChartPlanet[],
  lagnaIdx: number,
): { byHouse: Record<number, ChartPlanet[]>; bySign: Record<number, ChartPlanet[]> } {
  const byHouse: Record<number, ChartPlanet[]> = {};
  const bySign: Record<number, ChartPlanet[]> = {};
  for (let i = 0; i < 12; i++) {
    byHouse[i + 1] = [];
    bySign[i] = [];
  }
  for (const p of planets) {
    if (!p?.name) continue;
    const signIdx = resolveSignIndex(p.sign || p.rashi);
    let house = typeof p.house === "number" && p.house >= 1 && p.house <= 12 ? p.house : 0;
    if (!house) house = houseFromSign(signIdx, lagnaIdx);
    byHouse[house].push(p);
    bySign[signIdx >= 0 ? signIdx : (lagnaIdx + house - 1) % 12].push(p);
  }
  return { byHouse, bySign };
}

type Props = {
  title?: string;
  caption?: string;
  lagnaSign: string | null | undefined;
  planets: ChartPlanet[];
  style?: ChartStyle;
  showDegrees?: boolean;
  showAsc?: boolean;
  size?: number;
};

export function NorthIndianChartWeb({
  title,
  caption,
  lagnaSign,
  planets,
  style = "north",
  showDegrees = false,
  showAsc = true,
  size = 340,
}: Props) {
  const lagnaIdx = resolveSignIndex(lagnaSign);
  const { byHouse, bySign } = normalizePlanets(planets, lagnaIdx);

  const stroke = "#2f6f6a";
  const bg = "#ffffff";
  const signNumFill = "#111827";
  const sw = 1.6;
  const wrapBg = "#f7f4ef";

  return (
    <div style={{ width: "100%", maxWidth: size, margin: "0 auto" }}>
      {title ? (
        <div style={{ fontWeight: 700, fontSize: 14, color: "#1f2937", marginBottom: 8 }}>{title}</div>
      ) : null}
      <div
        style={{
          width: "100%",
          aspectRatio: "1 / 1",
          background: wrapBg,
          borderRadius: 4,
          padding: 4,
        }}
      >
        <svg width="100%" height="100%" viewBox={`0 0 ${VB} ${VB}`} preserveAspectRatio="xMidYMid meet">
          {style === "north" ? (
            <>
              <rect x={0} y={0} width={VB} height={VB} fill={bg} />
              <rect x={0} y={0} width={VB} height={VB} fill="none" stroke={stroke} strokeWidth={sw} />
              <line x1={0} y1={0} x2={VB} y2={VB} stroke={stroke} strokeWidth={sw} />
              <line x1={VB} y1={0} x2={0} y2={VB} stroke={stroke} strokeWidth={sw} />
              <line x1={CX} y1={0} x2={VB} y2={CY} stroke={stroke} strokeWidth={sw} />
              <line x1={VB} y1={CY} x2={CX} y2={VB} stroke={stroke} strokeWidth={sw} />
              <line x1={CX} y1={VB} x2={0} y2={CY} stroke={stroke} strokeWidth={sw} />
              <line x1={0} y1={CY} x2={CX} y2={0} stroke={stroke} strokeWidth={sw} />

              {Object.entries(HOUSE_CENTERS).map(([hStr, { x, y }]) => {
                const house = Number(hStr);
                const signIdx = (lagnaIdx + house - 1) % 12;
                const list = byHouse[house] || [];
                const isLagna = house === 1;
                const startY = y - (list.length > 2 ? 6 : 2);
                return (
                  <g key={house}>
                    <text x={x} y={y - 22} textAnchor="middle" fontSize={11} fontWeight={600} fill={signNumFill}>
                      {signIdx + 1}
                    </text>
                    {list.map((p, i) => (
                      <text
                        key={`${house}-${p.name}-${i}`}
                        x={x}
                        y={startY + i * 12}
                        textAnchor="middle"
                        fontSize={11}
                        fontWeight={700}
                        fill={PLANET_CLR[p.name || ""] || "#111"}
                      >
                        {planetLabel(p, showDegrees)}
                      </text>
                    ))}
                    {isLagna && showAsc ? (
                      <text
                        x={x}
                        y={startY + list.length * 12 + 2}
                        textAnchor="middle"
                        fontSize={10}
                        fontWeight={600}
                        fill="#64748b"
                      >
                        Asc
                      </text>
                    ) : null}
                  </g>
                );
              })}
            </>
          ) : (
            <>
              <rect x={0} y={0} width={VB} height={VB} fill={bg} stroke={stroke} strokeWidth={sw} />
              {[100, 200, 300].map((v) => (
                <g key={v}>
                  <line x1={v} y1={0} x2={v} y2={VB} stroke={stroke} strokeWidth={sw} />
                  <line x1={0} y1={v} x2={VB} y2={v} stroke={stroke} strokeWidth={sw} />
                </g>
              ))}
              <rect x={100} y={100} width={200} height={200} fill={wrapBg} stroke={stroke} strokeWidth={sw} />
              {SOUTH_CELLS.map((cell) => {
                const list = bySign[cell.signIdx] || [];
                const isLagna = cell.signIdx === lagnaIdx;
                const cx = cell.x + cell.w / 2;
                const cy = cell.y + 22;
                return (
                  <g key={cell.signIdx}>
                    <text
                      x={cell.x + 8}
                      y={cell.y + 14}
                      fontSize={10}
                      fontWeight={600}
                      fill={signNumFill}
                    >
                      {cell.signIdx + 1}
                    </text>
                    {list.map((p, i) => (
                      <text
                        key={`${cell.signIdx}-${p.name}-${i}`}
                        x={cx}
                        y={cy + i * 12}
                        textAnchor="middle"
                        fontSize={11}
                        fontWeight={700}
                        fill={PLANET_CLR[p.name || ""] || "#111"}
                      >
                        {planetLabel(p, showDegrees)}
                      </text>
                    ))}
                    {isLagna && showAsc ? (
                      <text
                        x={cx}
                        y={cy + list.length * 12 + 2}
                        textAnchor="middle"
                        fontSize={10}
                        fontWeight={600}
                        fill="#64748b"
                      >
                        Asc
                      </text>
                    ) : null}
                  </g>
                );
              })}
            </>
          )}
        </svg>
      </div>
      {caption ? (
        <div
          style={{
            textAlign: "center",
            marginTop: 10,
            fontSize: 13,
            fontWeight: 600,
            color: "#374151",
            textDecoration: "underline",
            textUnderlineOffset: 4,
          }}
        >
          {caption}
        </div>
      ) : null}
    </div>
  );
}

export function StyleToggle({
  value,
  onChange,
}: {
  value: ChartStyle;
  onChange: (v: ChartStyle) => void;
}) {
  const btn = (id: ChartStyle, label: string) => (
    <button
      type="button"
      onClick={() => onChange(id)}
      style={{
        flex: 1,
        padding: "10px 12px",
        border: "none",
        borderRadius: 6,
        fontWeight: 700,
        fontSize: 13,
        cursor: "pointer",
        background: value === id ? "#e11d48" : "#e5e7eb",
        color: value === id ? "#fff" : "#4b5563",
      }}
    >
      {label}
    </button>
  );
  return (
    <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
      {btn("north", "North Indian")}
      {btn("south", "South Indian")}
    </div>
  );
}

/**
 * Render North Indian diamond kundli as PNG data-URL for V3 chat share.
 * Only the diamond chart (plus optional title) — no planet tables.
 */
export function renderNorthIndianChartPngDataUrl(opts: {
  lagnaSign?: string | null;
  planets: ChartPlanet[];
  title?: string;
  /** Footer label under chart (default: D1 · Lagna Chart). */
  caption?: string;
  /** Chart square size in px (default 720). */
  chartPx?: number;
}): string {
  const chartPx = opts.chartPx ?? 720;
  const titleH = opts.title ? 52 : 20;
  const pad = 20;
  const canvas = document.createElement("canvas");
  canvas.width = chartPx + pad * 2;
  canvas.height = chartPx + pad * 2 + titleH;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas not available");

  const wrapBg = "#f7f4ef";
  const bg = "#ffffff";
  const stroke = "#2f6f6a";
  const signNumFill = "#111827";

  ctx.fillStyle = wrapBg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (opts.title) {
    ctx.fillStyle = "#1f2937";
    ctx.font = "700 22px system-ui, -apple-system, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(opts.title, canvas.width / 2, 34);
  }

  const ox = pad;
  const oy = titleH + pad;
  const scale = chartPx / VB;

  ctx.save();
  ctx.translate(ox, oy);
  ctx.scale(scale, scale);

  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, VB, VB);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2.2;
  ctx.strokeRect(0, 0, VB, VB);

  const lines: [number, number, number, number][] = [
    [0, 0, VB, VB],
    [VB, 0, 0, VB],
    [CX, 0, VB, CY],
    [VB, CY, CX, VB],
    [CX, VB, 0, CY],
    [0, CY, CX, 0],
  ];
  for (const [x1, y1, x2, y2] of lines) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  const lagnaIdx = resolveSignIndex(opts.lagnaSign);
  const { byHouse } = normalizePlanets(opts.planets, lagnaIdx);

  for (const [hStr, { x, y }] of Object.entries(HOUSE_CENTERS)) {
    const house = Number(hStr);
    const signIdx = (lagnaIdx + house - 1) % 12;
    const list = byHouse[house] || [];
    const isLagna = house === 1;
    const startY = y - (list.length > 2 ? 6 : 2);

    ctx.fillStyle = signNumFill;
    ctx.font = "600 14px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(signIdx + 1), x, y - 22);

    list.forEach((p, i) => {
      ctx.fillStyle = PLANET_CLR[p.name || ""] || "#111";
      ctx.font = "700 13px system-ui, sans-serif";
      ctx.fillText(planetLabel(p, false), x, startY + i * 14);
    });

    if (isLagna) {
      ctx.fillStyle = "#64748b";
      ctx.font = "600 12px system-ui, sans-serif";
      ctx.fillText("Asc", x, startY + list.length * 14 + 2);
    }
  }

  ctx.restore();

  ctx.fillStyle = "#374151";
  ctx.font = "600 16px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(opts.caption || "D1 · Lagna Chart", canvas.width / 2, canvas.height - 14);

  return canvas.toDataURL("image/png");
}

/** Dasha timeline card as PNG for V3 chat share (same flow as diamond charts). */
export function renderDashaSharePngDataUrl(opts: {
  personName: string;
  sectionTitle: string;
  current?: {
    maha?: string;
    antar?: string;
    pratyantar?: string;
    start?: string;
    end?: string;
    pdStart?: string;
    pdEnd?: string;
  } | null;
  rows: Array<{ planet: string; start: string; end: string; active?: boolean }>;
}): string {
  const rows = opts.rows.slice(0, 24);
  const rowH = 36;
  const headerH = 40;
  const topH = 56 + (opts.current ? 88 : 12);
  const pad = 20;
  const width = 720;
  const height = topH + headerH + rows.length * rowH + pad * 2 + 28;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas not available");

  const cream = "#f5f2ed";
  const card = "#ffffff";
  const text = "#1f2937";
  const muted = "#6b7280";
  const pink = "#be123c";

  ctx.fillStyle = cream;
  ctx.fillRect(0, 0, width, height);

  ctx.fillStyle = text;
  ctx.font = "700 22px system-ui, -apple-system, Segoe UI, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`${opts.personName} · Dasha`, width / 2, 34);

  ctx.fillStyle = muted;
  ctx.font = "600 14px system-ui, sans-serif";
  ctx.fillText(opts.sectionTitle, width / 2, 54);

  let y = 70;
  if (opts.current) {
    const boxX = pad;
    const boxW = width - pad * 2;
    const boxH = 78;
    ctx.fillStyle = "#fff1f2";
    ctx.strokeStyle = "#fecdd3";
    ctx.lineWidth = 1.5;
    roundRect(ctx, boxX, y, boxW, boxH, 10);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = pink;
    ctx.font = "800 13px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Ab chal rahi (live)", boxX + 14, y + 22);

    const chain = [opts.current.maha, opts.current.antar, opts.current.pratyantar]
      .filter(Boolean)
      .join(" / ");
    ctx.fillStyle = text;
    ctx.font = "700 16px system-ui, sans-serif";
    ctx.fillText(chain || "—", boxX + 14, y + 44);

    ctx.fillStyle = muted;
    ctx.font = "500 12px system-ui, sans-serif";
    const period = `${opts.current.start || "—"} → ${opts.current.end || "—"}`;
    ctx.fillText(`Antar: ${period}`, boxX + 14, y + 64);
    y += boxH + 14;
  }

  const tableX = pad;
  const tableW = width - pad * 2;
  const colPlanet = tableX + 12;
  const colStart = tableX + tableW * 0.42;
  const colEnd = tableX + tableW * 0.72;

  ctx.fillStyle = "#f3f4f6";
  roundRect(ctx, tableX, y, tableW, headerH, 8);
  ctx.fill();
  ctx.fillStyle = muted;
  ctx.font = "700 12px system-ui, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Planet", colPlanet, y + 26);
  ctx.fillText("Start Date", colStart, y + 26);
  ctx.fillText("End Date", colEnd, y + 26);
  y += headerH;

  rows.forEach((r, i) => {
    ctx.fillStyle = r.active ? "#fef3c7" : i % 2 ? "#f9fafb" : card;
    ctx.fillRect(tableX, y, tableW, rowH);
    if (r.active) {
      ctx.fillStyle = "#e11d48";
      ctx.fillRect(tableX, y, 4, rowH);
    }
    ctx.strokeStyle = "#e5e7eb";
    ctx.beginPath();
    ctx.moveTo(tableX, y + rowH);
    ctx.lineTo(tableX + tableW, y + rowH);
    ctx.stroke();

    ctx.fillStyle = text;
    ctx.font = "700 13px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(r.planet || "—", colPlanet, y + 24);
    ctx.font = "500 13px ui-monospace, monospace";
    ctx.fillText(r.start || "—", colStart, y + 24);
    ctx.fillText(r.end || "—", colEnd, y + 24);
    y += rowH;
  });

  ctx.fillStyle = muted;
  ctx.font = "600 12px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Shared from Cosmic Intelligence V3", width / 2, height - 12);

  return canvas.toDataURL("image/png");
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}
