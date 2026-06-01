import type { DivisionalChart, KundliData } from "@/types";
import { enSignToShort, SIGNS_SHORT, type PlanetCardData } from "@/lib/planetPositionUtils";

const EN_SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
] as const;

const PLANET_ORDER = [
  "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
];

const VARGA_PARTS: Record<VargaKey, number> = {
  D2: 2, D3: 3, D4: 4, D7: 7, D9: 9, D10: 10, D12: 12,
  D16: 16, D20: 20, D24: 24, D27: 27, D30: 30, D40: 40, D45: 45, D60: 60,
};

/** Degree within the varga sign (from D1 longitude). */
export function vargaDegreeInSign(lon: number, parts: number): number {
  const partSize = 30 / parts;
  const degInSign = ((lon % 30) + 30) % 30;
  const degInPart = degInSign % partSize;
  return (degInPart / partSize) * 30;
}

const MOVABLE = new Set([0, 3, 6, 9]);
const FIXED = new Set([1, 4, 7, 10]);
const FIRE = new Set([0, 4, 8]);
const EARTH = new Set([1, 5, 9]);
const AIR = new Set([2, 6, 10]);
export type VargaKey =
  | "D2"
  | "D3"
  | "D4"
  | "D7"
  | "D9"
  | "D10"
  | "D12"
  | "D16"
  | "D20"
  | "D24"
  | "D27"
  | "D30"
  | "D40"
  | "D45"
  | "D60";

function partIndex(lon: number, parts: number): number {
  const degInSign = ((lon % 30) + 30) % 30;
  return Math.min(parts - 1, Math.floor(degInSign / (30 / parts)));
}

function signIndex(lon: number): number {
  return Math.floor(lon / 30) % 12;
}

function modalitySeed(sidx: number): number {
  if (MOVABLE.has(sidx)) return 0;
  if (FIXED.has(sidx)) return 4;
  return 8;
}

function d2SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const firstHalf = (lon % 30) < 15;
  return sidx % 2 === 0
    ? (firstHalf ? 4 : 3)
    : (firstHalf ? 3 : 4);
}

function d3SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  return (sidx + partIndex(lon, 3) * 4) % 12;
}

function d4SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const pIdx = partIndex(lon, 4);
  return (sidx + pIdx * 3) % 12;
}

function d7SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const pIdx = partIndex(lon, 7);
  const seed = sidx % 2 === 0 ? sidx : (sidx + 6) % 12;
  return (seed + pIdx) % 12;
}

/** BPHS Navamsha — movable/fixed/dual seed (matches divisional_charts.py). */
function d9SignIdx(lon: number): number {
  const sign = signIndex(lon);
  const nIdx = partIndex(lon, 9);
  let seed: number;
  if (MOVABLE.has(sign)) seed = sign;
  else if (FIXED.has(sign)) seed = (sign + 8) % 12;
  else seed = (sign + 4) % 12;
  return (seed + nIdx) % 12;
}

function d10SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const pada = partIndex(lon, 10);
  return sidx % 2 === 0 ? (sidx + pada) % 12 : (sidx + 8 + pada) % 12;
}

function d12SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  return (sidx + partIndex(lon, 12)) % 12;
}

function d16SignIdx(lon: number): number {
  return (modalitySeed(signIndex(lon)) + partIndex(lon, 16)) % 12;
}

function d20SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const pIdx = partIndex(lon, 20);
  let seed = 4;
  if (MOVABLE.has(sidx)) seed = 0;
  else if (FIXED.has(sidx)) seed = 8;
  return (seed + pIdx) % 12;
}

function d24SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const seed = sidx % 2 === 0 ? 4 : 3;
  return (seed + partIndex(lon, 24)) % 12;
}

function d27SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  let seed = 9;
  if (FIRE.has(sidx)) seed = 0;
  else if (EARTH.has(sidx)) seed = 3;
  else if (AIR.has(sidx)) seed = 6;
  return (seed + partIndex(lon, 27)) % 12;
}

function d30SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const deg = ((lon % 30) + 30) % 30;
  if (sidx % 2 === 0) {
    if (deg < 5) return 0;   // Mars: Aries
    if (deg < 10) return 10; // Saturn: Aquarius
    if (deg < 18) return 8;  // Jupiter: Sagittarius
    if (deg < 25) return 2;  // Mercury: Gemini
    return 6;                // Venus: Libra
  }
  if (deg < 5) return 1;     // Venus: Taurus
  if (deg < 12) return 5;    // Mercury: Virgo
  if (deg < 20) return 11;   // Jupiter: Pisces
  if (deg < 25) return 9;    // Saturn: Capricorn
  return 7;                  // Mars: Scorpio
}

function d40SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const seed = sidx % 2 === 0 ? 0 : 6;
  return (seed + partIndex(lon, 40)) % 12;
}

function d45SignIdx(lon: number): number {
  return (modalitySeed(signIndex(lon)) + partIndex(lon, 45)) % 12;
}

function d60SignIdx(lon: number): number {
  const sidx = signIndex(lon);
  const pIdx = partIndex(lon, 60);
  return sidx % 2 === 0 ? (sidx + pIdx) % 12 : (sidx - pIdx + 120) % 12;
}

const VARGA_FN: Record<VargaKey, (lon: number) => number> = {
  D2: d2SignIdx,
  D3: d3SignIdx,
  D4: d4SignIdx,
  D7: d7SignIdx,
  D9: d9SignIdx,
  D10: d10SignIdx,
  D12: d12SignIdx,
  D16: d16SignIdx,
  D20: d20SignIdx,
  D24: d24SignIdx,
  D27: d27SignIdx,
  D30: d30SignIdx,
  D40: d40SignIdx,
  D45: d45SignIdx,
  D60: d60SignIdx,
};

function buildChart(
  signFn: (lon: number) => number,
  ascLon: number,
  positions: Record<string, number>,
): DivisionalChart {
  const ascIdx = signFn(ascLon);
  const planets = PLANET_ORDER.map(name => {
    const lon = positions[name];
    if (typeof lon !== "number") return null;
    const sidx = signFn(lon);
    return {
      name,
      sign: EN_SIGNS[sidx],
      signIndex: sidx,
      house: ((sidx - ascIdx + 12) % 12) + 1,
    };
  }).filter(Boolean) as DivisionalChart["planets"];

  return {
    ascendant: EN_SIGNS[ascIdx],
    ascendantSignIndex: ascIdx,
    planets,
  };
}

function planetLongitudes(kundli: KundliData): Record<string, number> | null {
  const out: Record<string, number> = {};
  for (const p of kundli.planets ?? []) {
    if (p.name && typeof p.longitude === "number" && !Number.isNaN(p.longitude)) {
      out[p.name] = p.longitude;
    }
  }
  return PLANET_ORDER.every(n => n in out) ? out : null;
}

/** Stored chart from API, or compute on-device from D1 longitudes (old saved kundlis). */
export function getVargaChart(kundli: KundliData | null | undefined, key: VargaKey): DivisionalChart | null {
  if (!kundli) return null;

  const div = kundli.divisionalCharts;
  const lc = key.toLowerCase() as Lowercase<VargaKey>;
  const stored = div?.[key] ?? div?.[lc];
  if (stored?.planets?.length) return stored;

  const ascLon = kundli.ascendantDeg;
  const positions = planetLongitudes(kundli);
  if (typeof ascLon !== "number" || !positions) return null;

  return buildChart(VARGA_FN[key], ascLon, positions);
}

/** Planet rows for Planet Position–style cards in divisional charts. */
export function getVargaPlanetCards(
  kundli: KundliData | null | undefined,
  key: VargaKey,
): { lagnaShort: string; planets: PlanetCardData[] } | null {
  const chart = getVargaChart(kundli, key);
  if (!chart || !kundli) return null;

  const positions = planetLongitudes(kundli);
  if (!positions) return null;

  const parts = VARGA_PARTS[key];
  const d1ByName = Object.fromEntries((kundli.planets ?? []).map(p => [p.name, p]));

  const planets: PlanetCardData[] = chart.planets.map(p => {
    const lon = positions[p.name];
    const signShort = enSignToShort(p.sign) || SIGNS_SHORT[p.signIndex] || p.sign;
    const deg = vargaDegreeInSign(lon, parts);
    return {
      name: p.name,
      sign: signShort,
      house: p.house,
      longitude: p.signIndex * 30 + deg,
      retrograde: d1ByName[p.name]?.retrograde,
      speed: d1ByName[p.name]?.speed,
    };
  });

  const lagnaShort = enSignToShort(chart.ascendant) || SIGNS_SHORT[chart.ascendantSignIndex] || chart.ascendant;
  return { lagnaShort, planets };
}
