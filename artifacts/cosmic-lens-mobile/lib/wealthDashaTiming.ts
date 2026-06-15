import { getVargaChart } from "@/lib/vargaCompute";
import type { DashaData, KundliData, PlanetInfo } from "@/types";

const SIGN_LORDS = [
  "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
  "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
];
const EXALT: Record<string, number> = {
  Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6,
};
const DEBIL: Record<string, number> = {
  Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0,
};
const OWN: Record<string, number[]> = {
  Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5],
  Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10],
};

export type WealthAntardashaRow = {
  planet: string;
  startDate: string;
  endDate: string;
  score: number;
  isCurrent: boolean;
  isWealthLinked: boolean;
};

export type WealthMahadashaRow = {
  planet: string;
  startDate: string;
  endDate: string;
  score: number;
  isCurrent: boolean;
  isWealthLinked: boolean;
  antardashas: WealthAntardashaRow[];
};

export type WealthDashaTimeline = {
  baseScore: number;
  mahadashas: WealthMahadashaRow[];
  bestMd: { planet: string; score: number } | null;
  bestAd: { mdPlanet: string; planet: string; score: number } | null;
};

function signOf(lon: number): number {
  return Math.floor((((lon % 360) + 360) % 360) / 30);
}

function ascIdx(kundli: KundliData): number {
  return signOf(kundli.ascendantDeg ?? 0);
}

function houseLord(kundli: KundliData, house: number): string {
  return SIGN_LORDS[(ascIdx(kundli) + house - 1) % 12];
}

function getPlanet(kundli: KundliData, name: string): PlanetInfo | undefined {
  return kundli.planets?.find(p => p.name === name);
}

function planetSign(p?: PlanetInfo): number | null {
  if (!p) return null;
  if (typeof p.rashiIndex === "number") return p.rashiIndex;
  if (typeof p.longitude === "number") return signOf(p.longitude);
  return null;
}

function dignityLabel(planet: string, sign: number | null): string {
  if (sign == null) return "neutral";
  if (EXALT[planet] === sign) return "exalted";
  if (DEBIL[planet] === sign) return "debilitated";
  if ((OWN[planet] ?? []).includes(sign)) return "own sign";
  return "neutral";
}

function vargaPlanetHouse(kundli: KundliData, chart: "D2" | "D9" | "D10", planet: string): number | null {
  const v = getVargaChart(kundli, chart);
  const p = v?.planets?.find(row => row.name === planet);
  return p?.house ?? null;
}

function vargaPlanetSign(kundli: KundliData, chart: "D9", planet: string): number | null {
  const v = getVargaChart(kundli, chart);
  const p = v?.planets?.find(row => row.name === planet);
  return p?.signIndex ?? null;
}

export function wealthLinkedPlanets(kundli: KundliData): Set<string> {
  const set = new Set<string>();
  for (const h of [2, 5, 9, 11]) set.add(houseLord(kundli, h));
  for (const name of ["Jupiter", "Venus", "Mercury"]) set.add(name);
  for (const p of kundli.planets ?? []) {
    if ([2, 11].includes(p.house)) set.add(p.name);
  }
  return set;
}

/** Planet multiplier when it runs as MD/AD — mirrors server _mb_dasha_planet_multiplier. */
export function dashaWealthPlanetMultiplier(kundli: KundliData, planet: string): number {
  if (!planet) return 1;
  const p = getPlanet(kundli, planet);
  let mult = 1;
  if (p && [3, 6, 10, 11].includes(p.house)) mult += 0.15;
  const d1Dig = dignityLabel(planet, planetSign(p));
  const d9Sign = vargaPlanetSign(kundli, "D9", planet);
  const d9Strong = d9Sign != null && (d9Sign === EXALT[planet] || (OWN[planet] ?? []).includes(d9Sign));
  if (d1Dig === "exalted" || d1Dig === "own sign" || d9Strong) mult += 0.1;
  const d10H = vargaPlanetHouse(kundli, "D10", planet);
  if (d10H != null && [2, 10, 11].includes(d10H)) mult += 0.1;
  const d2Sign = (() => {
    const v = getVargaChart(kundli, "D2");
    const row = v?.planets?.find(r => r.name === planet);
    return row?.signIndex ?? null;
  })();
  const wealthLords = new Set([houseLord(kundli, 2), houseLord(kundli, 9), houseLord(kundli, 11)]);
  if (d2Sign === 3 && wealthLords.has(planet)) mult += 0.05;
  const hasSupport = d9Strong;
  if (p && [8, 12].includes(p.house) && !hasSupport) mult -= 0.15;
  if (d1Dig === "debilitated") mult -= 0.1;
  return Math.max(0.8, Math.min(1.25, mult));
}

export function operationalWealthScore(
  baseScore: number,
  kundli: KundliData,
  mdPlanet: string,
  adPlanet?: string,
): number {
  const mdMult = dashaWealthPlanetMultiplier(kundli, mdPlanet);
  if (!adPlanet) {
    return Math.max(8, Math.min(96, Math.round(baseScore * mdMult)));
  }
  const adMult = dashaWealthPlanetMultiplier(kundli, adPlanet);
  const combined = Math.max(0.8, Math.min(1.25, mdMult * 0.6 + adMult * 0.4));
  return Math.max(8, Math.min(96, Math.round(baseScore * combined)));
}

function isRangeActive(startDate: string, endDate: string, now = new Date()): boolean {
  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return false;
  return now >= start && now <= end;
}

function formatDashaDate(raw: string): string {
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short" });
}

export function formatDashaRange(startDate: string, endDate: string): string {
  return `${formatDashaDate(startDate)} – ${formatDashaDate(endDate)}`;
}

export function buildWealthDashaTimeline(
  kundli: KundliData | null | undefined,
  baseScore: number,
): WealthDashaTimeline | null {
  if (!kundli?.dashas?.length || baseScore <= 0) return null;

  const wealthSet = wealthLinkedPlanets(kundli);
  const currentMd = kundli.currentDasha?.maha ?? "";
  const currentAd = kundli.currentDasha?.antar ?? "";

  const cycle = kundli.dashas.slice(0, 9);
  const mahadashas: WealthMahadashaRow[] = cycle.map((md: DashaData) => {
    const mdScore = operationalWealthScore(baseScore, kundli, md.planet);
    const antardashas: WealthAntardashaRow[] = (md.subDashas ?? []).map((ad: DashaData) => ({
      planet: ad.planet,
      startDate: ad.startDate,
      endDate: ad.endDate,
      score: operationalWealthScore(baseScore, kundli, md.planet, ad.planet),
      isCurrent: isRangeActive(ad.startDate, ad.endDate)
        || (md.planet === currentMd && ad.planet === currentAd),
      isWealthLinked: wealthSet.has(ad.planet),
    }));

    return {
      planet: md.planet,
      startDate: md.startDate,
      endDate: md.endDate,
      score: mdScore,
      isCurrent: isRangeActive(md.startDate, md.endDate) || md.planet === currentMd,
      isWealthLinked: wealthSet.has(md.planet),
      antardashas,
    };
  });

  let bestMd: WealthDashaTimeline["bestMd"] = null;
  let bestAd: WealthDashaTimeline["bestAd"] = null;

  for (const md of mahadashas) {
    if (!bestMd || md.score > bestMd.score) {
      bestMd = { planet: md.planet, score: md.score };
    }
    for (const ad of md.antardashas) {
      if (!bestAd || ad.score > bestAd.score) {
        bestAd = { mdPlanet: md.planet, planet: ad.planet, score: ad.score };
      }
    }
  }

  return { baseScore, mahadashas, bestMd, bestAd };
}
