/** Planetary positions table for V3 admin live chat (matches app-style columns). */

import { resolveSignIndex, SIGN_LORDS, SIGNS } from "./NorthIndianChartWeb";
import type { AdminChartPayload, AdminChartPlanet } from "./v3KundliPack";

const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", "Punarvasu", "Pushya",
  "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
  "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
  "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
] as const;

const NAK_LORDS = [
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] as const;

const BALADI = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"] as const;

const EXALT_IDX: Record<string, number> = {
  Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6,
};
const DEBIL_IDX: Record<string, number> = {
  Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0,
};
const OWN_IDX: Record<string, number[]> = {
  Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5], Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10],
};
const FRIEND_LORDS: Record<string, Set<string>> = {
  Sun: new Set(["Moon", "Mars", "Jupiter"]),
  Moon: new Set(["Sun", "Mercury"]),
  Mars: new Set(["Sun", "Moon", "Jupiter"]),
  Mercury: new Set(["Sun", "Venus"]),
  Jupiter: new Set(["Sun", "Moon", "Mars"]),
  Venus: new Set(["Mercury", "Saturn"]),
  Saturn: new Set(["Mercury", "Venus"]),
};
const ENEMY_LORDS: Record<string, Set<string>> = {
  Sun: new Set(["Venus", "Saturn"]),
  Moon: new Set([]),
  Mars: new Set(["Mercury"]),
  Mercury: new Set(["Moon"]),
  Jupiter: new Set(["Mercury", "Venus"]),
  Venus: new Set(["Sun", "Moon"]),
  Saturn: new Set(["Sun", "Moon", "Mars"]),
};

const ROW_ORDER = [
  "Ascendant",
  "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu",
  "Neptune", "Uranus", "Pluto",
] as const;

export type PlanetPositionRow = {
  planet: string;
  sign: string;
  signLord: string;
  nakshatra: string;
  nakshLord: string;
  degree: string;
  retro: string;
  house: string;
  state: string;
  status: string;
};

export const POSITION_COLUMNS = [
  "Planet",
  "Sign",
  "Sign Lord",
  "Nakshatra",
  "Naksh Lord",
  "Degree",
  "Retro",
  "House",
  "State",
  "Status",
] as const;

function lonFromPlanet(p: AdminChartPlanet): number | null {
  if (typeof p.longitude === "number" && Number.isFinite(p.longitude)) return p.longitude;
  return null;
}

function parseDegString(raw?: string | null): number | null {
  if (!raw) return null;
  const s = String(raw).trim();
  const m = s.match(/^(\d+)[°º]\s*(\d+)?/);
  if (!m) return null;
  const d = Number(m[1]);
  const min = m[2] != null ? Number(m[2]) : 0;
  if (!Number.isFinite(d) || !Number.isFinite(min)) return null;
  return d + min / 60;
}

function formatDegreeDms(lon: number): string {
  const degInSign = ((lon % 30) + 30) % 30;
  const d = Math.floor(degInSign);
  const minFloat = (degInSign - d) * 60;
  const m = Math.floor(minFloat);
  const s = Math.floor((minFloat - m) * 60);
  return `${d}° ${m}′ ${s}″`;
}

function nakFromLon(lon: number): { name: string; lord: string } {
  const size = 360 / 27;
  const idx = Math.floor(((lon % 360) + 360) % 360 / size) % 27;
  return { name: NAKSHATRAS[idx], lord: NAK_LORDS[idx] };
}

function baladiState(degInSign: number, signIdx: number): string {
  let band = Math.min(4, Math.floor(degInSign / 6));
  if (signIdx % 2 === 1) band = 4 - band;
  return BALADI[band] ?? "—";
}

function dignityStatus(planet: string, signIdx: number): string {
  if (planet === "Ascendant") return "—";
  if (planet === "Rahu" && signIdx === 10) return "OWNED";
  if (planet === "Ketu" && signIdx === 7) return "OWNED";
  if (!EXALT_IDX[planet]) return "—";

  if (EXALT_IDX[planet] === signIdx) return "EXALTED";
  if (DEBIL_IDX[planet] === signIdx) return "DEBILITATED";
  if (OWN_IDX[planet]?.includes(signIdx)) return "OWNED";

  const lord = SIGN_LORDS[signIdx];
  if (FRIEND_LORDS[planet]?.has(lord)) return "FRIENDLY";
  if (ENEMY_LORDS[planet]?.has(lord)) return "ENEMY";
  return "—";
}

function displayPlanet(name: string): string {
  return name === "Ascendant" ? "Ascendant" : name.toUpperCase();
}

function signName(raw?: string | null): string {
  if (!raw) return "—";
  const idx = resolveSignIndex(raw);
  return SIGNS[idx] ?? String(raw);
}

function buildAscRow(chart: NonNullable<AdminChartPayload["chart"]>): PlanetPositionRow | null {
  const ascSign = signName(chart.ascendant);
  if (ascSign === "—") return null;
  const signIdx = resolveSignIndex(chart.ascendant);
  const lon =
    typeof chart.ascendantDeg === "number" && Number.isFinite(chart.ascendantDeg)
      ? chart.ascendantDeg
      : signIdx * 30;
  const degInSign = ((lon % 30) + 30) % 30;
  const nak = nakFromLon(lon);
  return {
    planet: "Ascendant",
    sign: ascSign,
    signLord: SIGN_LORDS[signIdx] ?? "—",
    nakshatra: nak.name,
    nakshLord: nak.lord,
    degree: formatDegreeDms(lon),
    retro: "No",
    house: "1",
    state: baladiState(degInSign, signIdx),
    status: "—",
  };
}

function buildPlanetRow(p: AdminChartPlanet): PlanetPositionRow | null {
  const name = String(p.name || "").trim();
  if (!name) return null;

  const sign = signName(p.sign || p.rashi);
  const signIdx = resolveSignIndex(p.sign || p.rashi);
  const lon = lonFromPlanet(p);
  const degInSign =
    lon != null
      ? ((lon % 30) + 30) % 30
      : parseDegString(p.degrees) ?? (typeof p.degree === "number" ? p.degree : null);

  const nakName = p.nakshatra ? String(p.nakshatra) : lon != null ? nakFromLon(lon).name : "—";
  const nakLord = p.nakshatraRuler || (lon != null ? nakFromLon(lon).lord : "—");

  const degree =
    lon != null
      ? formatDegreeDms(lon)
      : p.degrees
        ? String(p.degrees)
        : degInSign != null
          ? formatDegreeDms(signIdx * 30 + degInSign)
          : "—";

  const house = p.house != null && p.house >= 1 && p.house <= 12 ? String(p.house) : "—";
  const state =
    degInSign != null && signIdx >= 0 ? baladiState(degInSign, signIdx) : "—";

  return {
    planet: displayPlanet(name),
    sign,
    signLord: signIdx >= 0 ? SIGN_LORDS[signIdx] ?? "—" : "—",
    nakshatra: nakName,
    nakshLord: String(nakLord || "—"),
    degree,
    retro: p.retrograde ? "Yes" : "No",
    house,
    state,
    status: signIdx >= 0 ? dignityStatus(name, signIdx) : "—",
  };
}

export function buildPlanetPositionRows(data: AdminChartPayload | null | undefined): PlanetPositionRow[] {
  const chart = data?.chart;
  if (!chart) return [];

  const byName = new Map<string, AdminChartPlanet>();
  for (const p of chart.planets || []) {
    const n = String(p.name || "").trim();
    if (n) byName.set(n, p);
  }

  const rows: PlanetPositionRow[] = [];
  const asc = buildAscRow(chart);
  if (asc) rows.push(asc);

  for (const key of ROW_ORDER) {
    if (key === "Ascendant") continue;
    const p = byName.get(key);
    if (!p) continue;
    const row = buildPlanetRow(p);
    if (row) rows.push(row);
  }

  return rows;
}

export function formatPlanetPositionsCopyText(data: AdminChartPayload | null | undefined): string {
  const rows = buildPlanetPositionRows(data);
  if (!rows.length) return "";

  const c = data?.chart || {};
  const b = data?.birth || {};
  const name = b.name || data?.name || c.name || "User";
  const header = [
    "Planetary Positions",
    `Name: ${name}`,
    `DOB: ${b.dob || c.dob || "—"} · Time: ${b.time || c.time || "—"}`,
    `Place: ${b.place || c.place || "—"} · Lagna: ${c.ascendant || "—"}`,
    "",
    POSITION_COLUMNS.join("\t"),
  ];

  const body = rows.map((r) =>
    [
      r.planet,
      r.sign,
      r.signLord,
      r.nakshatra,
      r.nakshLord,
      r.degree,
      r.retro,
      r.house,
      r.state,
      r.status,
    ].join("\t"),
  );

  return [...header, ...body].join("\n");
}
