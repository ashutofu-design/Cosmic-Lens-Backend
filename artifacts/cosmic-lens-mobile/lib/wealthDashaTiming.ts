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

/** MD anchor + AD modifier; +0.03 synergy when both lords ≥ 1.08. Mirrors server _mb_combine_dasha_wealth_multiplier. */
function combineDashaWealthMultipliers(mdMult: number, adMult?: number): number {
  let combined = adMult == null ? mdMult : mdMult * (0.6 + 0.4 * adMult);
  if (adMult != null && mdMult >= 1.08 && adMult >= 1.08) combined += 0.03;
  return Math.max(0.8, Math.min(1.25, combined));
}

export function operationalWealthScore(
  baseScore: number,
  kundli: KundliData,
  mdPlanet: string,
  adPlanet?: string,
): number {
  const mdMult = dashaWealthPlanetMultiplier(kundli, mdPlanet);
  const adMult = adPlanet ? dashaWealthPlanetMultiplier(kundli, adPlanet) : undefined;
  const combined = combineDashaWealthMultipliers(mdMult, adMult);
  return Math.max(8, Math.min(96, Math.round(baseScore * combined)));
}

/** Current MD/AD operational wealth score — same logic as active row in dasha timing modal. */
export function currentOperationalWealthScore(
  kundli: KundliData | null | undefined,
  baseScore: number,
): { mdPlanet: string; adPlanet: string; score: number } | null {
  if (!kundli || baseScore <= 0) return null;
  const mdPlanet = kundli.currentDasha?.maha ?? "";
  if (!mdPlanet) return null;
  const adPlanet = kundli.currentDasha?.antar ?? "";
  return {
    mdPlanet,
    adPlanet,
    score: operationalWealthScore(baseScore, kundli, mdPlanet, adPlanet || undefined),
  };
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

function parseDashaDate(raw: string): Date | null {
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d;
}

function horizonDate(now: Date, years: number): Date {
  const d = new Date(now);
  d.setFullYear(d.getFullYear() + years);
  return d;
}

/** Period touches [now, horizon] window. */
function overlapsWindow(startDate: string, endDate: string, now: Date, horizon: Date): boolean {
  const start = parseDashaDate(startDate);
  const end = parseDashaDate(endDate);
  if (!start || !end) return false;
  return end >= now && start <= horizon;
}

function findCurrentMahadashaIndex(dashas: DashaData[], now: Date, currentMd: string): number {
  for (let i = 0; i < dashas.length; i++) {
    if (isRangeActive(dashas[i].startDate, dashas[i].endDate, now)) return i;
  }
  if (currentMd) {
    const idx = dashas.findIndex(md => md.planet === currentMd && overlapsWindow(
      md.startDate, md.endDate, now, horizonDate(now, 100),
    ));
    if (idx >= 0) return idx;
  }
  for (let i = 0; i < dashas.length; i++) {
    const end = parseDashaDate(dashas[i].endDate);
    if (end && end >= now) return i;
  }
  return 0;
}

function filterForwardAntardashas(
  md: DashaData,
  now: Date,
  horizon: Date,
  currentMd: string,
  currentAd: string,
): DashaData[] {
  const ads = md.subDashas ?? [];
  const isCurrentMd = isRangeActive(md.startDate, md.endDate, now)
    || (currentMd && md.planet === currentMd);

  let startIdx = 0;
  if (isCurrentMd) {
    for (let j = 0; j < ads.length; j++) {
      if (isRangeActive(ads[j].startDate, ads[j].endDate, now)) {
        startIdx = j;
        break;
      }
      if (currentMd === md.planet && currentAd && ads[j].planet === currentAd) {
        startIdx = j;
        break;
      }
      const adEnd = parseDashaDate(ads[j].endDate);
      if (adEnd && adEnd >= now) {
        startIdx = j;
        break;
      }
    }
  }

  return ads
    .slice(startIdx)
    .filter(ad => overlapsWindow(ad.startDate, ad.endDate, now, horizon));
}

export function buildWealthDashaTimeline(
  kundli: KundliData | null | undefined,
  baseScore: number,
  horizonYears = 100,
): WealthDashaTimeline | null {
  if (!kundli?.dashas?.length || baseScore <= 0) return null;

  const wealthSet = wealthLinkedPlanets(kundli);
  const currentMd = kundli.currentDasha?.maha ?? "";
  const currentAd = kundli.currentDasha?.antar ?? "";
  const now = new Date();
  const horizon = horizonDate(now, horizonYears);
  const allMd = kundli.dashas;
  const startIdx = findCurrentMahadashaIndex(allMd, now, currentMd);

  const mahadashas: WealthMahadashaRow[] = [];

  for (let i = startIdx; i < allMd.length; i++) {
    const md = allMd[i];
    const mdStart = parseDashaDate(md.startDate);
    if (mdStart && mdStart > horizon) break;
    if (!overlapsWindow(md.startDate, md.endDate, now, horizon)) continue;

    const forwardAds = filterForwardAntardashas(md, now, horizon, currentMd, currentAd);
    const antardashas: WealthAntardashaRow[] = forwardAds.map((ad: DashaData) => ({
      planet: ad.planet,
      startDate: ad.startDate,
      endDate: ad.endDate,
      score: operationalWealthScore(baseScore, kundli, md.planet, ad.planet),
      isCurrent: isRangeActive(ad.startDate, ad.endDate, now)
        || (md.planet === currentMd && ad.planet === currentAd),
      isWealthLinked: wealthSet.has(ad.planet),
    }));

    mahadashas.push({
      planet: md.planet,
      startDate: md.startDate,
      endDate: md.endDate,
      score: operationalWealthScore(baseScore, kundli, md.planet),
      isCurrent: isRangeActive(md.startDate, md.endDate, now) || md.planet === currentMd,
      isWealthLinked: wealthSet.has(md.planet),
      antardashas,
    });
  }

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
