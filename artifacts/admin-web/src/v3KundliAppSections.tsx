/**
 * App View-Kundli sections for admin V3 modal (same logic as mobile kundli.tsx).
 * Planet Position (D1 / Divisional charts) stays on separate tabs — these are
 * Ashtakavarga, Navatara, Jaimini, Transit + birth snapshot helpers.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { API_BASE } from "./api";
import type { AdminChartPayload } from "./v3KundliPack";

const CARD = "#ffffff";
const TEXT = "#1f2937";
const MUTED = "#6b7280";
const ACCENT = "#7c3aed";

const NAKSHATRAS = [
  "Ashwini",
  "Bharani",
  "Krittika",
  "Rohini",
  "Mrigashira",
  "Ardra",
  "Punarvasu",
  "Pushya",
  "Ashlesha",
  "Magha",
  "Purva Phalguni",
  "Uttara Phalguni",
  "Hasta",
  "Chitra",
  "Swati",
  "Vishakha",
  "Anuradha",
  "Jyeshtha",
  "Mula",
  "Purva Ashadha",
  "Uttara Ashadha",
  "Shravana",
  "Dhanishtha",
  "Shatabhisha",
  "Purva Bhadrapada",
  "Uttara Bhadrapada",
  "Revati",
];

const NAK_LORDS = [
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
];

const RASHI_EN = [
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
];

const PLANET_HUE: Record<string, string> = {
  Sun: "#f59e0b",
  Moon: "#64748b",
  Mars: "#ef4444",
  Mercury: "#10b981",
  Jupiter: "#ca8a04",
  Venus: "#ec4899",
  Saturn: "#7c3aed",
  Rahu: "#b45309",
  Ketu: "#ea580c",
};

const BAV: Record<string, Record<string, number[]>> = {
  Sun: {
    Sun: [1, 2, 4, 7, 8, 9, 10, 11],
    Moon: [3, 6, 10, 11],
    Mars: [1, 2, 4, 7, 8, 9, 10, 11],
    Mercury: [3, 5, 6, 9, 10, 11, 12],
    Jupiter: [5, 6, 9, 11],
    Venus: [6, 7, 12],
    Saturn: [1, 2, 4, 7, 8, 9, 10, 11],
    Asc: [1, 2, 4, 7, 8, 9, 10, 11],
  },
  Moon: {
    Sun: [3, 6, 7, 8, 10, 11],
    Moon: [1, 3, 6, 7, 10, 11],
    Mars: [2, 3, 5, 6, 9, 10, 11],
    Mercury: [1, 3, 4, 5, 7, 8, 10, 11],
    Jupiter: [1, 4, 7, 8, 10, 11, 12],
    Venus: [3, 4, 5, 7, 9, 10, 11],
    Saturn: [3, 5, 6, 11],
    Asc: [3, 6, 10, 11],
  },
  Mars: {
    Sun: [3, 5, 6, 10, 11],
    Moon: [3, 6, 11],
    Mars: [1, 2, 4, 7, 8, 10, 11],
    Mercury: [3, 5, 6, 11],
    Jupiter: [6, 10, 11, 12],
    Venus: [6, 8, 11, 12],
    Saturn: [1, 4, 7, 8, 9, 10, 11],
    Asc: [1, 2, 4, 7, 8, 10, 11],
  },
  Mercury: {
    Sun: [5, 6, 9, 11, 12],
    Moon: [2, 4, 6, 8, 10, 11],
    Mars: [1, 2, 4, 7, 8, 9, 10, 11],
    Mercury: [1, 3, 5, 6, 9, 10, 11, 12],
    Jupiter: [6, 8, 11, 12],
    Venus: [1, 2, 3, 4, 5, 8, 9, 11],
    Saturn: [1, 2, 4, 7, 8, 9, 10, 11],
    Asc: [1, 2, 4, 6, 8, 10, 11],
  },
  Jupiter: {
    Sun: [1, 2, 3, 4, 7, 8, 9, 10, 11],
    Moon: [2, 5, 7, 9, 11],
    Mars: [1, 2, 4, 7, 8, 10, 11],
    Mercury: [1, 2, 4, 5, 6, 9, 10, 11],
    Jupiter: [1, 2, 3, 4, 7, 8, 10, 11],
    Venus: [2, 5, 6, 9, 10, 11],
    Saturn: [3, 5, 6, 12],
    Asc: [1, 2, 4, 7, 8, 10, 11],
  },
  Venus: {
    Sun: [8, 11, 12],
    Moon: [1, 2, 3, 4, 5, 8, 9, 11, 12],
    Mars: [3, 4, 6, 9, 11, 12],
    Mercury: [3, 5, 6, 9, 11],
    Jupiter: [5, 8, 9, 10, 11],
    Venus: [1, 2, 3, 4, 5, 8, 9, 10, 11],
    Saturn: [3, 4, 5, 8, 9, 10, 11],
    Asc: [1, 2, 3, 4, 5, 8, 9, 11],
  },
  Saturn: {
    Sun: [1, 2, 4, 7, 8, 10, 11],
    Moon: [3, 6, 11],
    Mars: [3, 5, 6, 10, 11, 12],
    Mercury: [6, 8, 9, 10, 11, 12],
    Jupiter: [5, 6, 11, 12],
    Venus: [6, 11, 12],
    Saturn: [3, 5, 6, 11],
    Asc: [1, 3, 4, 6, 10, 11],
  },
};

const TARA = [
  { name: "Janma", desc: "Birth star — self & body", color: "#94a3b8", type: "neutral" },
  { name: "Sampat", desc: "Wealth & prosperity", color: "#22c55e", type: "good" },
  { name: "Vipat", desc: "Danger / obstacles", color: "#ef4444", type: "bad" },
  { name: "Kshema", desc: "Well-being & comfort", color: "#4ade80", type: "good" },
  { name: "Pratyak", desc: "Opposition / delays", color: "#f97316", type: "bad" },
  { name: "Sadhana", desc: "Achievement & effort", color: "#34d399", type: "good" },
  { name: "Naidhana", desc: "Loss / ending themes", color: "#dc2626", type: "bad" },
  { name: "Mitra", desc: "Friendship & support", color: "#60a5fa", type: "good" },
  { name: "Param Mitra", desc: "Great friend — strongest", color: "#a78bfa", type: "great" },
] as const;

const KARAKAS = [
  { key: "AK", name: "Atmakaraka", desc: "Soul significator — deepest desire", color: "#f59e0b" },
  { key: "AmK", name: "Amatyakaraka", desc: "Career & counsel", color: "#22c55e" },
  { key: "BK", name: "Bhratrikaraka", desc: "Siblings & courage", color: "#ef4444" },
  { key: "MK", name: "Matrikaraka", desc: "Mother & mind", color: "#64748b" },
  { key: "PK", name: "Putrakaraka", desc: "Children & creativity", color: "#ec4899" },
  { key: "GK", name: "Gnatikaraka", desc: "Relatives & obstacles", color: "#a78bfa" },
  { key: "DK", name: "Darakaraka", desc: "Spouse & partnerships", color: "#b45309" },
] as const;

type Chart = NonNullable<AdminChartPayload["chart"]>;
type Planet = NonNullable<Chart["planets"]>[number] & {
  longitude?: number;
  degree?: number;
};

function hue(p: string) {
  return PLANET_HUE[p] || ACCENT;
}

function planetLon(p?: Planet | null): number {
  if (!p) return 0;
  if (typeof p.longitude === "number" && Number.isFinite(p.longitude)) return p.longitude;
  if (typeof p.degree === "number" && Number.isFinite(p.degree)) return p.degree;
  return 0;
}

function ascDeg(chart: Chart): number {
  const d = (chart as { ascendantDeg?: number }).ascendantDeg;
  if (typeof d === "number" && Number.isFinite(d)) return d;
  // Fallback: moon house / sign index not reliable — use 0
  return 0;
}

export function resolveNakshatraLord(chart: Chart): string {
  const stored = (chart as { nakshatraRuler?: string }).nakshatraRuler;
  if (stored) return stored;
  const nak = chart.nakshatra || "";
  const idx = NAKSHATRAS.findIndex((n) => n.toLowerCase() === nak.toLowerCase());
  if (idx >= 0) return NAK_LORDS[idx];
  const moon = (chart.planets || []).find((p) => (p.name || "").toLowerCase() === "moon");
  const lon = planetLon(moon as Planet);
  const nIdx = Math.floor((((lon % 360) + 360) % 360) / (360 / 27)) % 27;
  return NAK_LORDS[nIdx] || "—";
}

function computeBAV(chart: Chart) {
  const aDeg = ascDeg(chart);
  const ascRashi = Math.floor((((aDeg % 360) + 360) % 360) / 30) % 12;
  const planets = chart.planets || [];
  const getR = (name: string) => {
    if (name === "Asc") return ascRashi;
    const p = planets.find((pl) => pl.name === name) as Planet | undefined;
    if (!p) return -1;
    return Math.floor(planetLon(p) / 30) % 12;
  };
  const SAV = Array(12).fill(0) as number[];
  const BAVS: Record<string, number[]> = {};
  const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
  for (const planet of PLANETS) {
    const sigs = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Asc"];
    const bav = Array(12).fill(0) as number[];
    for (const sig of sigs) {
      const sR = getR(sig);
      if (sR < 0) continue;
      for (const pos of BAV[planet]?.[sig] ?? []) {
        bav[(sR + pos - 1) % 12] += 1;
      }
    }
    BAVS[planet] = bav;
    for (let r = 0; r < 12; r++) SAV[r] += bav[r];
  }
  return { BAVS, SAV };
}

function computeNavatara(chart: Chart) {
  let moonNakIdx = NAKSHATRAS.findIndex(
    (n) => n.toLowerCase() === (chart.nakshatra || "").toLowerCase(),
  );
  if (moonNakIdx < 0) {
    const moon = (chart.planets || []).find((p) => (p.name || "").toLowerCase() === "moon");
    const lon = planetLon(moon as Planet);
    moonNakIdx = Math.floor((((lon % 360) + 360) % 360) / (360 / 27)) % 27;
  }
  const core = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"];
  return core.map((name) => {
    const p = (chart.planets || []).find((pl) => pl.name === name) as Planet | undefined;
    const lon = planetLon(p);
    const pNakIdx = Math.floor((((lon % 360) + 360) % 360) / (360 / 27)) % 27;
    const count = (pNakIdx - moonNakIdx + 27) % 27;
    const taraNum = count % 9;
    return {
      planet: name,
      nakName: NAKSHATRAS[pNakIdx],
      taraNum: taraNum + 1,
      tara: TARA[taraNum],
    };
  });
}

function computeChara(chart: Chart) {
  const CORE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
  const vals = CORE.map((name) => {
    const p = (chart.planets || []).find((pl) => pl.name === name) as Planet | undefined;
    if (!p) return { name, deg: 0 };
    let deg = planetLon(p) % 30;
    if (name === "Rahu") deg = 30 - deg;
    return { name, deg };
  });
  return [...vals]
    .sort((a, b) => b.deg - a.deg)
    .map((v, i) => ({ ...v, karaka: KARAKAS[i] }));
}

function transitHouseFromLon(lon: number, aDeg: number): number {
  const rashi = Math.floor((((lon % 360) + 360) % 360) / 30) % 12;
  const ascRashi = Math.floor((((aDeg % 360) + 360) % 360) / 30) % 12;
  return ((rashi - ascRashi + 12) % 12) + 1;
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div
      style={{
        background: CARD,
        borderRadius: 14,
        overflow: "hidden",
        border: "1px solid #e5e7eb",
        marginBottom: 12,
      }}
    >
      <div
        style={{
          background: "#f5f3ff",
          padding: "10px 14px",
          borderBottom: "1px solid #e5e7eb",
          fontWeight: 800,
          fontSize: 11,
          letterSpacing: 1,
          color: ACCENT,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
}

function DetailRow({
  label,
  value,
  zebra,
}: {
  label: string;
  value: string;
  zebra?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "10px 14px",
        background: zebra ? "#fafafa" : CARD,
        borderBottom: "1px solid #f3f4f6",
        alignItems: "center",
      }}
    >
      <div style={{ flex: 1, color: MUTED, fontSize: 10, fontWeight: 700, letterSpacing: 0.4 }}>
        {label}
      </div>
      <div style={{ color: TEXT, fontSize: 13, fontWeight: 600, textAlign: "right" }}>{value}</div>
    </div>
  );
}

/** App-style BIRTH CHART SNAPSHOT */
export function BirthChartSnapshot({ chart }: { chart: Chart }) {
  const lord = resolveNakshatraLord(chart);
  const nak = chart.nakshatra
    ? `${chart.nakshatra}${chart.nakshatraPada ? ` (Pada ${chart.nakshatraPada})` : ""}`
    : "—";
  return (
    <SectionCard title="BIRTH CHART SNAPSHOT">
      <DetailRow label="ASCENDANT (LAGNA)" value={chart.ascendant || "—"} />
      <DetailRow label="MOON SIGN (RASHI)" value={chart.moonSign || "—"} zebra />
      <DetailRow label="NAKSHATRA" value={nak} />
      <DetailRow label="NAKSHATRA LORD" value={lord} zebra />
    </SectionCard>
  );
}

export function AshtakavargaPanel({ chart }: { chart: Chart }) {
  const { BAVS, SAV } = useMemo(() => computeBAV(chart), [chart]);
  const [sel, setSel] = useState("SAV");
  const PLANETS = ["SAV", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
  const scores = sel === "SAV" ? SAV : BAVS[sel] || Array(12).fill(0);
  const maxScore = sel === "SAV" ? 56 : 8;
  const total = scores.reduce((a, b) => a + b, 0);

  return (
    <div>
      <div style={{ color: MUTED, fontSize: 12, marginBottom: 10, lineHeight: 1.45 }}>
        Same Ashtakavarga as app View Kundli — SAV / BAV bindus per rashi.
      </div>
      <div style={{ display: "flex", gap: 6, overflowX: "auto", marginBottom: 12 }}>
        {PLANETS.map((p) => {
          const on = p === sel;
          const c = p === "SAV" ? ACCENT : hue(p);
          return (
            <button
              key={p}
              type="button"
              onClick={() => setSel(p)}
              style={{
                flex: "0 0 auto",
                border: on ? `2px solid ${c}` : "1px solid #e5e7eb",
                background: on ? `${c}18` : CARD,
                borderRadius: 10,
                padding: "8px 12px",
                fontWeight: 700,
                fontSize: 12,
                color: on ? c : MUTED,
                cursor: "pointer",
              }}
            >
              {p === "SAV" ? "SAV" : p.slice(0, 3)}
            </button>
          );
        })}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
          padding: "8px 12px",
          background: "#f5f3ff",
          borderRadius: 10,
          border: "1px solid #e9e5ff",
        }}
      >
        <strong style={{ color: TEXT, fontSize: 14 }}>
          {sel === "SAV" ? "Sarvashtakavarga" : `${sel} BAV`}
        </strong>
        <span style={{ color: ACCENT, fontWeight: 800, fontSize: 13 }}>
          {total}/{sel === "SAV" ? 336 : 56}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {RASHI_EN.map((rashi, i) => {
          const score = scores[i] ?? 0;
          const pct = score / maxScore;
          const color =
            pct >= 0.7 ? "#16a34a" : pct >= 0.5 ? "#ca8a04" : pct >= 0.3 ? "#ea580c" : "#dc2626";
          return (
            <div
              key={rashi}
              style={{
                background: CARD,
                border: "1px solid #e5e7eb",
                borderRadius: 10,
                padding: 8,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 9, fontWeight: 700, color: MUTED }}>{rashi.slice(0, 3)}</div>
              <div style={{ fontSize: 20, fontWeight: 800, color }}>{score}</div>
              <div
                style={{
                  height: 4,
                  borderRadius: 2,
                  background: "#f3f4f6",
                  overflow: "hidden",
                  marginTop: 4,
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${Math.round(pct * 100)}%`,
                    background: color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function NavataraPanel({ chart }: { chart: Chart }) {
  const rows = useMemo(() => computeNavatara(chart), [chart]);
  return (
    <div>
      <div style={{ color: MUTED, fontSize: 12, marginBottom: 10, lineHeight: 1.45 }}>
        From Moon nakshatra — 9 Tara cycle (same as app).
      </div>
      <div
        style={{
          marginBottom: 12,
          padding: 12,
          borderRadius: 12,
          background: "#f5f3ff",
          border: "1px solid #e9e5ff",
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 800, color: MUTED, letterSpacing: 1 }}>
          CHANDRA NAKSHATRA (BASE)
        </div>
        <div style={{ fontSize: 16, fontWeight: 800, color: TEXT, marginTop: 4 }}>
          {chart.nakshatra || "—"}
        </div>
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {rows.map(({ planet, nakName, taraNum, tara }) => (
          <div
            key={planet}
            style={{
              display: "flex",
              gap: 10,
              padding: 12,
              borderRadius: 12,
              border: `1px solid ${tara.color}40`,
              background: CARD,
              borderLeft: `3px solid ${tara.color}`,
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: `${hue(planet)}18`,
                color: hue(planet),
                fontWeight: 800,
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {planet.slice(0, 2)}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <strong style={{ color: TEXT, fontSize: 13 }}>{planet}</strong>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 800,
                    color: tara.color,
                    background: `${tara.color}18`,
                    padding: "2px 8px",
                    borderRadius: 8,
                  }}
                >
                  {taraNum}. {tara.name}
                </span>
              </div>
              <div style={{ color: MUTED, fontSize: 11, marginTop: 2 }}>Nakshatra: {nakName}</div>
              <div style={{ color: tara.color, fontSize: 11, fontWeight: 600, marginTop: 2 }}>
                {tara.desc}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function JaiminiPanel({ chart }: { chart: Chart }) {
  const data = useMemo(() => computeChara(chart), [chart]);
  const ak = data[0];
  return (
    <div>
      <div style={{ color: MUTED, fontSize: 12, marginBottom: 10, lineHeight: 1.45 }}>
        Chara karakas by degree in sign — same as app Jaimini tab.
      </div>
      {ak?.karaka ? (
        <div
          style={{
            marginBottom: 12,
            padding: 14,
            borderRadius: 14,
            border: `1.5px solid ${hue(ak.name)}55`,
            background: CARD,
            borderLeft: `4px solid ${hue(ak.name)}`,
          }}
        >
          <div style={{ fontSize: 10, fontWeight: 800, color: MUTED, letterSpacing: 1 }}>
            ATMAKARAKA
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: TEXT, marginTop: 4 }}>{ak.name}</div>
          <div style={{ color: MUTED, fontSize: 12, marginTop: 4 }}>{ak.karaka.desc}</div>
          <div style={{ marginTop: 8, fontSize: 12, color: MUTED }}>
            Degree in sign:{" "}
            <strong style={{ color: hue(ak.name) }}>{ak.deg.toFixed(2)}°</strong>
          </div>
        </div>
      ) : null}
      <div style={{ display: "grid", gap: 8 }}>
        {data.map(({ name, deg, karaka }) => {
          if (!karaka) return null;
          return (
            <div
              key={name}
              style={{
                display: "flex",
                gap: 10,
                padding: 12,
                borderRadius: 12,
                border: `1px solid ${karaka.color}35`,
                background: CARD,
                borderLeft: `3px solid ${karaka.color}`,
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${karaka.color}18`,
                  color: karaka.color,
                  fontWeight: 800,
                  fontSize: 12,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                {karaka.key}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <strong style={{ color: TEXT, fontSize: 13 }}>{name}</strong>
                  <span style={{ color: MUTED, fontSize: 11 }}>{deg.toFixed(1)}°</span>
                </div>
                <div style={{ color: karaka.color, fontWeight: 700, fontSize: 12, marginTop: 2 }}>
                  {karaka.name}
                </div>
                <div style={{ color: MUTED, fontSize: 11, marginTop: 2 }}>{karaka.desc}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

type TransitPlanet = {
  name: string;
  longitude: number;
  signName?: string;
  signIndex?: number;
  degInSign?: number;
  retrograde?: boolean;
};

export function TransitPanel({ chart, active }: { chart: Chart; active: boolean }) {
  const [rows, setRows] = useState<TransitPlanet[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const aDeg = ascDeg(chart);

  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setErr(null);
      try {
        const res = await fetch(`${API_BASE}/api/current_transits`);
        if (!res.ok) throw new Error(`transits ${res.status}`);
        const json = (await res.json()) as { planets?: TransitPlanet[] };
        if (!cancelled) setRows(Array.isArray(json.planets) ? json.planets : []);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load transits");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    const t = window.setInterval(load, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, [active]);

  return (
    <div>
      <div style={{ color: MUTED, fontSize: 12, marginBottom: 10, lineHeight: 1.45 }}>
        Live gochar (current transits) vs birth lagna — same idea as app Transit tab.
      </div>
      {loading && !rows.length ? (
        <div style={{ color: MUTED }}>Loading live transits…</div>
      ) : err && !rows.length ? (
        <div style={{ color: "#dc2626" }}>{err}</div>
      ) : (
        <div
          style={{
            background: CARD,
            borderRadius: 12,
            border: "1px solid #e5e7eb",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1.2fr 70px 36px",
              gap: 6,
              padding: "8px 12px",
              background: "#f3f4f6",
              fontSize: 9,
              fontWeight: 800,
              color: MUTED,
              letterSpacing: 0.5,
            }}
          >
            <span>PLANET</span>
            <span>SIGN · NAK</span>
            <span style={{ textAlign: "right" }}>DEG</span>
            <span style={{ textAlign: "center" }}>H</span>
          </div>
          {rows.map((p, i) => {
            const lon = p.longitude ?? 0;
            const si =
              p.signIndex != null
                ? p.signIndex
                : Math.floor((((lon % 360) + 360) % 360) / 30) % 12;
            const nIdx = Math.floor((((lon % 360) + 360) % 360) / (360 / 27)) % 27;
            const house = transitHouseFromLon(lon, aDeg);
            const deg = p.degInSign != null ? p.degInSign : lon % 30;
            const natal = (chart.planets || []).find((x) => x.name === p.name) as
              | Planet
              | undefined;
            const natalR = natal ? Math.floor(planetLon(natal) / 30) % 12 : -1;
            const conj = natalR === si && natalR >= 0;
            return (
              <div
                key={p.name}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1.2fr 70px 36px",
                  gap: 6,
                  padding: "10px 12px",
                  borderTop: "1px solid #f3f4f6",
                  background: conj ? `${hue(p.name)}0d` : i % 2 ? "#fafafa" : CARD,
                  alignItems: "center",
                }}
              >
                <div>
                  <div style={{ fontWeight: 800, fontSize: 12, color: TEXT }}>
                    {p.name}
                    {p.retrograde ? (
                      <span style={{ color: "#dc2626", marginLeft: 4, fontSize: 10 }}>R</span>
                    ) : null}
                  </div>
                  {conj ? (
                    <div style={{ fontSize: 9, fontWeight: 700, color: hue(p.name) }}>
                      Natal conj.
                    </div>
                  ) : null}
                </div>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: TEXT }}>
                    {p.signName || RASHI_EN[si]}
                  </div>
                  <div style={{ fontSize: 10, color: MUTED }}>{NAKSHATRAS[nIdx]}</div>
                </div>
                <div
                  style={{
                    textAlign: "right",
                    fontSize: 11,
                    fontWeight: 700,
                    color: hue(p.name),
                  }}
                >
                  {deg.toFixed(1)}°
                </div>
                <div style={{ textAlign: "center", fontWeight: 800, fontSize: 12, color: TEXT }}>
                  H{house}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
