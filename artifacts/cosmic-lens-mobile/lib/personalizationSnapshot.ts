import type { UILang } from "@/lib/i18n";
import { evaluateNeechaBhanga, signShortFromIndex } from "@/lib/planetStrengthRule";
import { getVargaChart, type VargaKey } from "@/lib/vargaCompute";
import type { KundliData, PlanetInfo } from "@/types";

export type PersonalInsight = {
  key: string;
  label: string;
  title: string;
  sub: string;
  value: number | null;
  tag: string;
  line: string;
  support?: string;
  caution?: string;
  factors?: string[];
};

export type KundliCategoryDetailRow = {
  key: string;
  label: string;
  score: number;
  weightPct: number;
  detail: string;
  factors: string[];
};

export type KundliCategoryScore = {
  type: string;
  score: number;
  selected: boolean;
  reasons: string[];
  line: string;
  checked: string[];
  rules: string[];
  details: KundliCategoryDetailRow[];
};

export type PersonalSnapshot = {
  title: string;
  themeLabel: string;
  powerType: string;
  powerScore: number | null;
  powerLine: string;
  innerType: string;
  innerTypeSub: string;
  identityLine: string;
  strongestTrait: string;
  pressurePoint: string;
  hiddenStrength: string;
  pressureTrigger: string;
  todayTip: string;
  bestMode: string;
  trustLine: string;
  bullets: string[];
  insights: PersonalInsight[];
  categoryScores: KundliCategoryScore[];
  color: string;
  darkGrad: readonly [string, string];
  lightGrad: readonly [string, string];
};

const EXALT: Record<string, number> = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6, Rahu: 1, Ketu: 7 };
const DEBIL: Record<string, number> = { Sun: 6, Moon: 7, Mars: 3, Mercury: 11, Jupiter: 9, Venus: 5, Saturn: 0, Rahu: 7, Ketu: 1 };
const OWN: Record<string, number[]> = {
  Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5],
  Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10], Rahu: [], Ketu: [],
};
const SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"];
const SIGN_INDEX: Record<string, number> = {
  Aries: 0, Taurus: 1, Gemini: 2, Cancer: 3, Leo: 4, Virgo: 5,
  Libra: 6, Scorpio: 7, Sagittarius: 8, Capricorn: 9, Aquarius: 10, Pisces: 11,
};
const FRIENDS: Record<string, string[]> = {
  Sun: ["Moon", "Mars", "Jupiter"], Moon: ["Sun", "Mercury"],
  Mars: ["Sun", "Moon", "Jupiter"], Mercury: ["Sun", "Venus"],
  Jupiter: ["Sun", "Moon", "Mars"], Venus: ["Mercury", "Saturn"],
  Saturn: ["Mercury", "Venus"], Rahu: ["Venus", "Saturn", "Mercury"], Ketu: ["Venus", "Saturn", "Mercury"],
};
const ENEMIES: Record<string, string[]> = {
  Sun: ["Saturn", "Venus"], Moon: [], Mars: ["Mercury"], Mercury: ["Moon"],
  Jupiter: ["Mercury", "Venus"], Venus: ["Sun", "Moon"],
  Saturn: ["Sun", "Moon", "Mars"], Rahu: ["Sun", "Moon", "Mars"], Ketu: ["Sun", "Moon", "Mars"],
};
const BENEFICS = new Set(["Jupiter", "Venus", "Mercury", "Moon"]);
const MALEFICS = new Set(["Saturn", "Mars", "Rahu", "Ketu", "Sun"]);
const CLASSICAL_DIGNITY_PLANETS = new Set(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]);

const DIMS = [
  { key: "nature", label: "NAT", title: "Nature", house: 1, sigs: ["Moon", "Mercury"], sub: "Core personality and behaviour" },
  { key: "body", label: "BODY", title: "Body Energy", house: 1, sigs: ["Sun", "Mars"], sub: "Vitality, stamina, physical drive" },
  { key: "effort", label: "EFF", title: "Effort Style", house: 3, sigs: ["Mars", "Saturn"], sub: "How you fight, work and persist" },
  { key: "peace", label: "PEACE", title: "Peace", house: 4, sigs: ["Moon", "Venus"], sub: "Inner calm, home comfort, mental rest" },
  { key: "knowledge", label: "GYA", title: "Knowledge", house: 5, sigs: ["Jupiter", "Mercury"], sub: "Gyan, intelligence, learning depth" },
  { key: "problems", label: "PROB", title: "Problems", house: 6, sigs: ["Saturn", "Mars"], sub: "Enemies, conflicts, struggle handling", inverse: true },
  { key: "relationship", label: "REL", title: "Relationship", house: 7, sigs: ["Venus", "Moon"], sub: "Bonding, partnership, emotional exchange", varga: "D9" as const },
  { key: "hidden", label: "HID", title: "Hidden Issues", house: 8, sigs: ["Rahu", "Ketu", "Saturn"], sub: "Sudden events, unknown problems, transformations", inverse: true },
  { key: "luck", label: "LUCK", title: "Luck Support", house: 9, sigs: ["Jupiter", "Sun"], sub: "Fortune, blessings, dharma support" },
  { key: "career", label: "CAREER", title: "Career Strength", house: 10, sigs: ["Sun", "Saturn", "Mercury"], sub: "Work direction, authority, karma field", varga: "D10" as const },
  { key: "gains", label: "GAIN", title: "Gains", house: 11, sigs: ["Jupiter", "Saturn"], sub: "Network, gains, support system" },
  { key: "spiritual", label: "MOK", title: "Spirituality", house: 12, sigs: ["Ketu", "Jupiter"], sub: "Moksha pull, surrender, inner detachment", varga: "D20" as const },
] as const;

type VargaName = "D2" | "D3" | "D9" | "D10" | "D20" | "D24" | "D27" | "D30";

function signOf(lon: number): number {
  return Math.floor((((lon % 360) + 360) % 360) / 30);
}

function getPlanet(kundli: KundliData, name: string): PlanetInfo | undefined {
  return kundli.planets?.find(p => p.name === name);
}

function houseSign(kundli: KundliData, house: number): number {
  return (signOf(kundli.ascendantDeg ?? 0) + house - 1) % 12;
}

function houseLord(kundli: KundliData, house: number): string {
  return SIGN_LORDS[houseSign(kundli, house)];
}

function planetSign(p?: PlanetInfo): number | null {
  if (!p) return null;
  if (typeof p.rashiIndex === "number") return p.rashiIndex;
  if (typeof p.longitude === "number") return signOf(p.longitude);
  return null;
}

function dignity(planet: string, sign: number | null): { score: number; label: string } {
  if (sign == null) return { score: 0, label: "unknown dignity" };
  if (!CLASSICAL_DIGNITY_PLANETS.has(planet)) return { score: 0, label: "neutral sign" };
  if (EXALT[planet] === sign) return { score: 18, label: "exalted" };
  if (DEBIL[planet] === sign) return { score: -18, label: "debilitated" };
  if ((OWN[planet] ?? []).includes(sign)) return { score: 15, label: "own sign" };
  const lord = SIGN_LORDS[sign];
  if ((FRIENDS[planet] ?? []).includes(lord)) return { score: 8, label: "friendly sign" };
  if ((ENEMIES[planet] ?? []).includes(lord)) return { score: -8, label: "enemy sign" };
  return { score: 0, label: "neutral sign" };
}

function hasAspect(from: PlanetInfo, targetSign: number): boolean {
  const ps = planetSign(from);
  if (ps == null) return false;
  const d = (targetSign - ps + 12) % 12;
  return d === 6 ||
    (from.name === "Mars" && (d === 3 || d === 7)) ||
    (from.name === "Jupiter" && (d === 4 || d === 8)) ||
    (from.name === "Rahu" && (d === 4 || d === 8)) ||
    (from.name === "Ketu" && (d === 4 || d === 8)) ||
    (from.name === "Saturn" && (d === 2 || d === 9));
}

function aspectsToHouse(kundli: KundliData, house: number): { benefic: string[]; malefic: string[] } {
  const target = houseSign(kundli, house);
  const benefic: string[] = [];
  const malefic: string[] = [];
  for (const p of kundli.planets ?? []) {
    if (!hasAspect(p, target)) continue;
    if (BENEFICS.has(p.name)) benefic.push(p.name);
    if (MALEFICS.has(p.name)) malefic.push(p.name);
  }
  return { benefic, malefic };
}

function occupants(kundli: KundliData, house: number): PlanetInfo[] {
  return (kundli.planets ?? []).filter(p => p.house === house);
}

function isCombust(kundli: KundliData, p: PlanetInfo): boolean {
  if (p.name === "Sun") return false;
  const sun = getPlanet(kundli, "Sun");
  if (!sun || typeof sun.longitude !== "number" || typeof p.longitude !== "number") return false;
  const diff = Math.min(Math.abs(p.longitude - sun.longitude), 360 - Math.abs(p.longitude - sun.longitude));
  return diff < 10;
}

function neechaBhanga(kundli: KundliData, planet: string, sign: number | null): boolean {
  if (sign == null || DEBIL[planet] !== sign) return false;
  return evaluateNeechaBhanga(kundli, planet, signShortFromIndex(sign)).applies;
}

function lordedHouses(kundli: KundliData, planet: string): number[] {
  const lagna = signOf(kundli.ascendantDeg ?? 0);
  const houses: number[] = [];
  for (let h = 1; h <= 12; h++) {
    if (SIGN_LORDS[(lagna + h - 1) % 12] === planet) houses.push(h);
  }
  return houses;
}

function functionalScore(kundli: KundliData, planet: string): number {
  const houses = lordedHouses(kundli, planet);
  if (!houses.length) return 0;
  const trikon = houses.some(h => [1, 5, 9].includes(h));
  const kendra = houses.some(h => [1, 4, 7, 10].includes(h));
  const wealth = houses.some(h => [2, 11].includes(h));
  const dusthana = houses.some(h => [6, 8, 12].includes(h));
  let score = 0;
  if (trikon) score += 8;
  if (kendra) score += 4;
  if (wealth) score += 3;
  if (dusthana) score -= 7;
  return score;
}

function planetStrength(kundli: KundliData, planet: string): { score: number; label: string } {
  const p = getPlanet(kundli, planet);
  if (!p) return { score: 0, label: `${planet} missing` };
  const sign = planetSign(p);
  const dig = dignity(planet, sign);
  let score = dig.score;
  score += functionalScore(kundli, planet);
  if ([1, 4, 7, 10].includes(p.house)) score += 10;
  if ([5, 9].includes(p.house)) score += 8;
  if ([6, 8, 12].includes(p.house)) score -= 8;
  if (p.retrograde) score -= 4;
  if (isCombust(kundli, p)) score -= 5;
  if (neechaBhanga(kundli, planet, sign)) score += 14;
  return { score: Math.max(-35, Math.min(35, score)), label: neechaBhanga(kundli, planet, sign) ? `${dig.label}, corrected` : dig.label };
}

function getVarga(kundli: KundliData, which?: VargaName): KundliData {
  if (!which) return kundli;
  const varga = getVargaChart(kundli, which as VargaKey);
  if (!varga?.planets?.length) return kundli;
  return {
    ...kundli,
    ascendantDeg: (varga.ascendantSignIndex ?? signOf(kundli.ascendantDeg ?? 0)) * 30,
    planets: varga.planets.map(vp => ({
      name: vp.name,
      house: vp.house,
      longitude: (vp.signIndex ?? SIGN_INDEX[vp.sign] ?? 0) * 30,
      sign: vp.sign,
      retrograde: getPlanet(kundli, vp.name)?.retrograde,
    })),
  };
}

function hasVarga(kundli: KundliData, which?: VargaName): boolean {
  if (!which) return true;
  const varga = getVargaChart(kundli, which as VargaKey);
  return !!varga?.planets?.length;
}

function clampScore(n: number): number {
  return Math.max(8, Math.min(96, Math.round(n)));
}

function tagFor(key: string, score: number): string {
  if (key === "problems" || key === "hidden") {
    if (score >= 72) return "Low Disturbance";
    if (score >= 55) return "Manageable";
    if (score >= 40) return "Watchful";
    return "Heavy Pressure";
  }
  if (score >= 78) return "Very Strong";
  if (score >= 64) return "Strong";
  if (score >= 48) return "Mixed";
  return "Needs Support";
}

function relativeHouse(fromHouse: number, toHouse: number): number {
  return ((toHouse - fromHouse + 12) % 12) + 1;
}

function lordPlacementSupport(chart: KundliData, house: number, lord: string) {
  const lordPlanet = getPlanet(chart, lord);
  if (!lordPlanet) return { score: 0, factor: `${lord} placement: missing` };
  const rel = relativeHouse(house, lordPlanet.house);
  let score = 0;
  if ([1, 5, 9].includes(rel)) score += 9;
  else if ([4, 7, 10].includes(rel)) score += 7;
  else if ([2, 11].includes(rel)) score += 5;
  else if ([3, 6].includes(rel)) score += 2;
  else if ([8, 12].includes(rel)) score -= 8;
  return { score, factor: `${lord} placed ${rel}H from ${house}H` };
}

function sambandhaSupport(chart: KundliData, lord: string, sigs: readonly string[]) {
  const lordPlanet = getPlanet(chart, lord);
  if (!lordPlanet) return { score: 0, factors: [`${lord}-significator sambandha: missing lord`] };
  let score = 0;
  const factors: string[] = [];
  for (const sig of sigs) {
    const sigPlanet = getPlanet(chart, sig);
    const sigSign = planetSign(sigPlanet);
    const lordSign = planetSign(lordPlanet);
    if (!sigPlanet || sigSign == null || lordSign == null) continue;
    if (sigPlanet.house === lordPlanet.house) {
      score += 5;
      factors.push(`${lord}+${sig} conjunction`);
    }
    if (hasAspect(lordPlanet, sigSign)) {
      score += 3;
      factors.push(`${lord} aspects ${sig}`);
    }
    if (hasAspect(sigPlanet, lordSign)) {
      score += 3;
      factors.push(`${sig} aspects ${lord}`);
    }
  }
  return { score: Math.max(-2, Math.min(14, score)), factors: factors.length ? factors : [`${lord}-significator sambandha: none`] };
}

function ashtakavargaSupport(kundli: KundliData, house: number) {
  const bindu = sarvaBinduForHouse(kundli, house);
  if (bindu == null) return { score: 0, factor: "Ashtakavarga: unavailable for house" };
  const score = Math.max(-10, Math.min(10, (bindu - 28) * 1.2));
  return { score, factor: `Ashtakavarga ${house}H sign bindu: ${Math.round(bindu)}` };
}

function sarvaBinduForHouse(kundli: KundliData, house: number): number | null {
  const av = kundli.ashtakavarga;
  if (!av) return null;
  const targetSign = houseSign(kundli, house);
  const savKeys = ["SAV", "sav", "Sarva", "sarva", "Sarvashtakavarga", "sarvashtakavarga", "total"];
  for (const key of savKeys) {
    const arr = av[key];
    if (Array.isArray(arr) && typeof arr[targetSign] === "number") return arr[targetSign];
  }
  const arrays = Object.values(av).filter((arr): arr is number[] => Array.isArray(arr) && arr.length >= 12);
  if (arrays.length) return arrays.reduce((sum, arr) => sum + (Number(arr[targetSign]) || 0), 0);
  return null;
}

function wealthAshtakavargaModifier(kundli: KundliData) {
  const rows = [2, 11].map(house => {
    const bindu = sarvaBinduForHouse(kundli, house);
    let modifier = 0;
    if (typeof bindu === "number") {
      if (bindu > 32) modifier = 3;
      else if (bindu < 24) modifier = -3;
    }
    const status = bindu == null
      ? "missing"
      : bindu > 32
        ? "full support"
        : bindu < 24
          ? "high friction"
          : "neutral";
    return { house, bindu, modifier, status };
  });
  const modifier = Math.max(-3, Math.min(3, rows.reduce((sum, row) => sum + row.modifier, 0)));
  return {
    modifier,
    factors: rows.map(row => row.bindu == null
      ? `SAV ${row.house}H: unavailable`
      : `SAV ${row.house}H: ${Math.round(row.bindu)} bindus (${row.status}, ${row.modifier >= 0 ? "+" : ""}${row.modifier})`
    ),
  };
}

function navamshaSupport(kundli: KundliData, house: number, sigs: readonly string[]) {
  if (!hasVarga(kundli, "D9")) {
    return { score: 0, factors: ["D9 cross-check: not available"] };
  }

  const d9 = getVarga(kundli, "D9");
  const d1Lord = houseLord(kundli, house);
  const d1LordInD9 = getPlanet(d9, d1Lord);
  const d9HouseLord = houseLord(d9, house);
  const d1LordStrengthD9 = planetStrength(d9, d1Lord);
  const d9HouseLordStrength = planetStrength(d9, d9HouseLord);
  const d9Occ = occupants(d9, house);
  const d9Asp = aspectsToHouse(d9, house);

  let score = 0;
  if (d1LordInD9) {
    score += d1LordStrengthD9.score * 0.22;
    if ([1, 4, 7, 10].includes(d1LordInD9.house)) score += 6;
    if ([5, 9].includes(d1LordInD9.house)) score += 5;
    if ([6, 8, 12].includes(d1LordInD9.house)) score -= 6;
  }
  score += d9HouseLordStrength.score * 0.16;
  for (const p of d9Occ) score += BENEFICS.has(p.name) ? 4 : MALEFICS.has(p.name) ? -4 : 0;
  score += d9Asp.benefic.length * 3;
  score -= d9Asp.malefic.length * 3;
  score += sigs.reduce((sum, p) => sum + planetStrength(d9, p).score, 0) / sigs.length * 0.08;

  const factors = [
    `D1 ${house}H lord ${d1Lord} in D9: ${d1LordInD9 ? `${d1LordInD9.house}H, ${d1LordStrengthD9.label}` : "missing"}`,
    `D9 ${house}H lord ${d9HouseLord}: ${d9HouseLordStrength.label}`,
    d9Occ.length ? `D9 ${house}H occupants: ${d9Occ.map(p => p.name).join(", ")}` : `D9 ${house}H occupants: none`,
    d9Asp.benefic.length ? `D9 benefic aspect: ${d9Asp.benefic.join(", ")}` : "D9 benefic aspect: none",
    d9Asp.malefic.length ? `D9 malefic aspect: ${d9Asp.malefic.join(", ")}` : "D9 malefic aspect: none",
  ];

  return { score: Math.max(-18, Math.min(18, score)), factors };
}

function scoreHouseDomain(kundli: KundliData, spec: {
  house: number;
  sigs: readonly string[];
  inverse?: boolean;
  varga?: "D9" | "D10" | "D20";
}) {
  const chart = getVarga(kundli, spec.varga);
  const lord = houseLord(chart, spec.house);
  const lordStrength = planetStrength(chart, lord);
  const housePlanets = occupants(chart, spec.house);
  const asp = aspectsToHouse(chart, spec.house);
  const sigStrength = spec.sigs.reduce((sum, p) => sum + planetStrength(chart, p).score, 0) / spec.sigs.length;
  const occupantNames = housePlanets.map(p => p.name);
  const placement = lordPlacementSupport(chart, spec.house, lord);
  const sambandha = sambandhaSupport(chart, lord, spec.sigs);
  const ashtak = ashtakavargaSupport(kundli, spec.house);
  const d9 = navamshaSupport(kundli, spec.house, spec.sigs);

  let raw = 52 + lordStrength.score * 0.55 + sigStrength * 0.35;
  raw += placement.score;
  raw += sambandha.score;
  raw += ashtak.score;
  raw += asp.benefic.length * 6;
  raw -= asp.malefic.length * 5;
  for (const p of housePlanets) raw += BENEFICS.has(p.name) ? 7 : MALEFICS.has(p.name) ? -6 : 0;
  raw += d9.score;
  if (spec.inverse) raw = 100 - raw;

  const value = clampScore(raw);
  const support = asp.benefic[0]
    ? `${asp.benefic[0]} support on ${spec.house}H`
    : `${lord} lord is ${lordStrength.label}`;
  const caution = asp.malefic[0]
    ? `${asp.malefic[0]} pressure on ${spec.house}H`
    : housePlanets.find(p => MALEFICS.has(p.name))?.name
      ? `${housePlanets.find(p => MALEFICS.has(p.name))?.name} placed in ${spec.house}H`
      : "No major harsh marker";
  const factors = [
    `${spec.house}H lord ${lord}: ${lordStrength.label}`,
    `Lord strength: ${lordStrength.score >= 0 ? "+" : ""}${Math.round(lordStrength.score)}`,
    placement.factor,
    ...sambandha.factors,
    `Significators ${spec.sigs.join("/")} avg: ${sigStrength >= 0 ? "+" : ""}${Math.round(sigStrength)}`,
    asp.benefic.length ? `Benefic aspect: ${asp.benefic.join(", ")}` : "Benefic aspect: none",
    asp.malefic.length ? `Malefic aspect: ${asp.malefic.join(", ")}` : "Malefic aspect: none",
    occupantNames.length ? `Occupants: ${occupantNames.join(", ")}` : "Occupants: none",
    ashtak.factor,
    spec.varga ? (hasVarga(kundli, spec.varga) ? `Varga layer: ${spec.varga}` : `Varga layer: D1 fallback (${spec.varga} missing)`) : "Varga layer: D1",
    ...d9.factors,
  ];

  return { value, support, caution, factors, lord, lordStrength };
}

function scoreDimension(kundli: KundliData, dim: typeof DIMS[number]): PersonalInsight {
  const scored = scoreHouseDomain(kundli, dim);
  const value = scored.value;

  return {
    key: dim.key,
    label: dim.label,
    title: dim.title,
    sub: dim.sub,
    value,
    tag: tagFor(dim.key, value),
    support: scored.support,
    caution: scored.caution,
    factors: scored.factors,
    line: `${dim.title}: ${tagFor(dim.key, value)}. ${dim.house}H lord ${scored.lord} is ${scored.lordStrength.label}; ${scored.support}; ${scored.caution}.`,
  };
}

function weighted(items: Array<[number, number]>): number {
  const totalWeight = items.reduce((sum, [, w]) => sum + w, 0) || 1;
  return Math.round(items.reduce((sum, [value, w]) => sum + value * w, 0) / totalWeight);
}

function normPlanetScore(score: number): number {
  return Math.max(8, Math.min(96, Math.round(50 + score * 1.15)));
}

function dignitySupportLabel(label: string): string {
  if (label.includes("exalted")) return "exalted support";
  if (label.includes("own sign")) return "own-sign support";
  if (label.includes("friendly")) return "friendly-sign support";
  if (label.includes("corrected")) return "neecha-bhanga support";
  if (label.includes("debilitated")) return "debilitated pressure";
  if (label.includes("enemy")) return "enemy-sign pressure";
  return "neutral dignity";
}

function atmakaraka(kundli: KundliData): PlanetInfo | undefined {
  const candidates = (kundli.planets ?? []).filter(p =>
    ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"].includes(p.name) &&
    typeof p.longitude === "number"
  );
  return candidates.reduce<PlanetInfo | undefined>((best, p) => {
    const deg = ((p.longitude % 30) + 30) % 30;
    const bestDeg = best ? ((best.longitude % 30) + 30) % 30 : -1;
    return deg > bestDeg ? p : best;
  }, undefined);
}

function occupantSupport(chart: KundliData, house: number, karakas: readonly string[]) {
  let score = 0;
  const factors: string[] = [];
  for (const p of occupants(chart, house)) {
    const strength = planetStrength(chart, p.name);
    const normalized = normPlanetScore(strength.score);
    const strictSavingsPressure = house === 2 && MALEFICS.has(p.name);
    let add = 0;
    if (BENEFICS.has(p.name)) add += 6;
    if (MALEFICS.has(p.name)) {
      if (house === 2) add -= 7;
      else if ([10, 11].includes(house)) add += normalized >= 54 ? 5 : 2;
      else add += normalized >= 62 ? 5 : normalized >= 52 ? 1 : -6;
    }
    if (specHas(karakas, p.name) && !strictSavingsPressure) add += 4;
    if (!strictSavingsPressure) {
      if (strength.label.includes("exalted")) add += 4;
      else if (strength.label.includes("own sign")) add += 3;
      else if (strength.label.includes("friendly")) add += 2;
      else if (strength.label.includes("corrected")) add += 2;
      else if (strength.label.includes("debilitated")) add -= 4;
      else if (strength.label.includes("enemy")) add -= 2;
    }
    score += Math.max(-8, Math.min(12, add));
    factors.push(`${p.name} in ${house}H: ${normalized}%, ${dignitySupportLabel(strength.label)}, support ${add >= 0 ? "+" : ""}${Math.round(add)}`);
  }
  return { score: Math.max(-14, Math.min(18, score)), factors };
}

function specHas(items: readonly string[], value: string): boolean {
  return items.includes(value);
}

function lordContextSupport(chart: KundliData, house: number, lord: string, lordPlanet: PlanetInfo | undefined, karakas: readonly string[]) {
  if (!lordPlanet) return { score: 0, factors: [`${lord} placement context: missing`] };
  const placement = lordPlacementSupport(chart, house, lord);
  const companions = occupants(chart, lordPlanet.house).filter(p => p.name !== lord);
  let score = placement.score;
  const factors = [`${lord} placement support: ${placement.score >= 0 ? "+" : ""}${placement.score}`];
  for (const p of companions) {
    const strength = planetStrength(chart, p.name);
    const normalized = normPlanetScore(strength.score);
    let add = 0;
    if (normalized >= 62) add += 5;
    else if (normalized >= 54) add += 2;
    else if (MALEFICS.has(p.name)) add -= 3;
    if (specHas(karakas, p.name)) add += 4;
    if (strength.label.includes("exalted")) add += 4;
    else if (strength.label.includes("own sign")) add += 3;
    else if (strength.label.includes("friendly")) add += 2;
    else if (strength.label.includes("corrected")) add += 2;
    else if (strength.label.includes("debilitated")) add -= 4;
    score += Math.max(-6, Math.min(10, add));
    factors.push(`${lord} with ${p.name} in ${lordPlanet.house}H: ${normalized}%, ${dignitySupportLabel(strength.label)}, support ${add >= 0 ? "+" : ""}${Math.round(add)}`);
  }
  if (!companions.length) factors.push(`${lord} placement companions: none`);
  return { score: Math.max(-10, Math.min(18, score)), factors };
}

function cleanHouseScore(chart: KundliData, house: number, karakas: readonly string[]): number {
  const lord = houseLord(chart, house);
  const lordPlanet = getPlanet(chart, lord);
  const lordScore = normPlanetScore(planetStrength(chart, lord).score);
  const asp = aspectsToHouse(chart, house);
  const karakaScore = karakas.length
    ? weighted(karakas.map(k => [normPlanetScore(planetStrength(chart, k).score), 1]))
    : 50;

  let houseSupport = 50 + asp.benefic.length * 6 - asp.malefic.length * 5;
  const occSupport = occupantSupport(chart, house, karakas);
  const contextSupport = lordContextSupport(chart, house, lord, lordPlanet, karakas);
  houseSupport += occSupport.score;
  houseSupport = Math.max(8, Math.min(96, houseSupport));
  const placementContextScore = Math.max(8, Math.min(96, 50 + contextSupport.score));

  return weighted([[lordScore, 0.40], [houseSupport, 0.24], [karakaScore, 0.20], [placementContextScore, 0.16]]);
}

function cleanVargaScore(kundli: KundliData, varga: VargaName, houses: number[], karakas: readonly string[]): number {
  if (!hasVarga(kundli, varga)) return 50;
  const chart = getVarga(kundli, varga);
  const houseScore = weighted(houses.map(h => [cleanHouseScore(chart, h, karakas), 1]));
  const lagnaLordScore = normPlanetScore(planetStrength(chart, houseLord(chart, 1)).score);
  return weighted([[houseScore, 0.74], [lagnaLordScore, 0.26]]);
}

type CleanHouseSpec = { house: number; weight: number; karakas: readonly string[] };
type CleanPlanetSpec = { name: string; weight: number };
type CleanVargaSpec = { chart: VargaName; houses: number[]; karakas: readonly string[]; weight: number };

function weightPct(weight: number, total: number): number {
  return Math.round((weight / (total || 1)) * 100);
}

function houseBreakdown(chart: KundliData, chartLabel: string, spec: CleanHouseSpec, pct: number): KundliCategoryDetailRow {
  const lord = houseLord(chart, spec.house);
  const lordPlanet = getPlanet(chart, lord);
  const lordStrength = planetStrength(chart, lord);
  const lordScore = normPlanetScore(lordStrength.score);
  const lordSign = planetSign(lordPlanet);
  const occ = occupants(chart, spec.house);
  const asp = aspectsToHouse(chart, spec.house);
  const occSupport = occupantSupport(chart, spec.house, spec.karakas);
  const contextSupport = lordContextSupport(chart, spec.house, lord, lordPlanet, spec.karakas);
  const karakaRows = spec.karakas.map(name => {
    const strength = planetStrength(chart, name);
    return `${name}: ${normPlanetScore(strength.score)}%, ${strength.label}`;
  });
  const score = cleanHouseScore(chart, spec.house, spec.karakas);

  return {
    key: `${chartLabel}-${spec.house}H`,
    label: `${chartLabel} ${spec.house}H check`,
    score,
    weightPct: pct,
    detail: `${spec.house}H lord ${lord}, house support and ${spec.karakas.join("/")} karaka strength.`,
    factors: [
      `${spec.house}H lord: ${lord} (${lordScore}%, ${lordStrength.label})`,
      lordSign == null ? `${lord} sign: unknown` : `${lord} sign: ${signShortFromIndex(lordSign)}`,
      lordPlanet ? `${lord} placement: ${lordPlanet.house}H` : `${lord} placement: missing`,
      lordStrength.label.includes("corrected") ? `${lord} neecha-bhanga: applied` : `${lord} neecha-bhanga: not applied`,
      ...contextSupport.factors,
      occ.length ? `Occupants: ${occ.map(p => p.name).join(", ")}` : "Occupants: none",
      ...occSupport.factors,
      asp.benefic.length ? `Benefic aspects: ${asp.benefic.join(", ")}` : "Benefic aspects: none",
      asp.malefic.length ? `Malefic aspects: ${asp.malefic.join(", ")}` : "Malefic aspects: none",
      ...karakaRows,
    ],
  };
}

function planetBreakdown(kundli: KundliData, spec: CleanPlanetSpec, pct: number): KundliCategoryDetailRow {
  const p = getPlanet(kundli, spec.name);
  const strength = planetStrength(kundli, spec.name);
  const score = normPlanetScore(strength.score);
  const sign = planetSign(p);
  return {
    key: `planet-${spec.name}`,
    label: `${spec.name} strength`,
    score,
    weightPct: pct,
    detail: `${spec.name} dignity, house placement, functional role, combustion/retrograde and neecha-bhanga correction.`,
    factors: [
      p ? `House: ${p.house}H` : "House: missing",
      sign == null ? "Sign: unknown" : `Sign: ${signShortFromIndex(sign)}`,
      `Dignity: ${strength.label}`,
      `Raw strength: ${strength.score >= 0 ? "+" : ""}${Math.round(strength.score)}`,
      p?.retrograde ? "Retrograde: yes" : "Retrograde: no/unknown",
      p && isCombust(kundli, p) ? "Combust: yes" : "Combust: no",
    ],
  };
}

function vargaBreakdown(kundli: KundliData, spec: CleanVargaSpec, pct: number): KundliCategoryDetailRow {
  if (!hasVarga(kundli, spec.chart)) {
    return {
      key: `varga-${spec.chart}`,
      label: `${spec.chart} validation`,
      score: 50,
      weightPct: pct,
      detail: `${spec.chart} placements are not available, so this layer stays neutral.`,
      factors: ["Varga chart missing", "Neutral score used so the category is not over-penalized"],
    };
  }

  const chart = getVarga(kundli, spec.chart);
  const lagnaLord = houseLord(chart, 1);
  const lagnaStrength = planetStrength(chart, lagnaLord);
  const houseRows = spec.houses.map(h => {
    const lord = houseLord(chart, h);
    const p = getPlanet(chart, lord);
    const strength = planetStrength(chart, lord);
    const asp = aspectsToHouse(chart, h);
    return `${h}H lord ${lord}: ${normPlanetScore(strength.score)}%, ${strength.label}, placed ${p?.house ?? "missing"}H, aspects B${asp.benefic.length}/M${asp.malefic.length}`;
  });

  return {
    key: `varga-${spec.chart}`,
    label: `${spec.chart} validation`,
    score: cleanVargaScore(kundli, spec.chart, spec.houses, spec.karakas),
    weightPct: pct,
    detail: `${spec.chart} checks ${spec.houses.map(h => `${h}H`).join(", ")} with ${spec.karakas.join("/")} support.`,
    factors: [
      `${spec.chart} Lagna lord ${lagnaLord}: ${normPlanetScore(lagnaStrength.score)}%, ${lagnaStrength.label}`,
      ...houseRows,
      `Karakas checked: ${spec.karakas.join(", ")}`,
    ],
  };
}

function cleanCategoryResult(args: {
  kundli: KundliData;
  d1: CleanHouseSpec[];
  planets: CleanPlanetSpec[];
  vargas?: CleanVargaSpec[];
  checked: string[];
  rules: string[];
}) {
  const totalWeight = [
    ...args.d1.map(item => item.weight),
    ...args.planets.map(item => item.weight),
    ...(args.vargas ?? []).map(item => item.weight),
  ].reduce((sum, w) => sum + w, 0);
  const details = [
    ...args.d1.map(item => houseBreakdown(args.kundli, "D1", item, weightPct(item.weight, totalWeight))),
    ...args.planets.map(item => planetBreakdown(args.kundli, item, weightPct(item.weight, totalWeight))),
    ...(args.vargas ?? []).map(item => vargaBreakdown(args.kundli, item, weightPct(item.weight, totalWeight))),
  ];
  const score = Math.max(8, Math.min(96, weighted(details.map(item => [item.score, item.weightPct]))));
  return { score, details, checked: args.checked, rules: args.rules };
}

function wealthYogaSupport(kundli: KundliData): number {
  const wealthHouses = [2, 5, 9, 10, 11];
  const lords = [...new Set(wealthHouses.map(h => houseLord(kundli, h)))];
  let score = 0;
  for (let i = 0; i < lords.length; i++) {
    const a = getPlanet(kundli, lords[i]);
    const aSign = planetSign(a);
    if (!a || aSign == null) continue;
    for (let j = i + 1; j < lords.length; j++) {
      const b = getPlanet(kundli, lords[j]);
      const bSign = planetSign(b);
      if (!b || bSign == null) continue;
      if (a.house === b.house) score += 3.5;
      if (hasAspect(a, bSign)) score += 2.5;
      if (hasAspect(b, aSign)) score += 2.5;
      if (wealthHouses.includes(a.house) && wealthHouses.includes(b.house)) score += 1.5;
    }
  }
  return Math.max(0, Math.min(18, score));
}

function aspectNamesToPlanet(kundli: KundliData, targetPlanet: string) {
  const target = getPlanet(kundli, targetPlanet);
  const targetSign = planetSign(target);
  const benefic: string[] = [];
  const malefic: string[] = [];
  if (targetSign == null) return { benefic, malefic };
  for (const p of kundli.planets ?? []) {
    if (p.name === targetPlanet || !hasAspect(p, targetSign)) continue;
    if (BENEFICS.has(p.name)) benefic.push(p.name);
    if (MALEFICS.has(p.name)) malefic.push(p.name);
  }
  return { benefic, malefic };
}

function hasMercuryModernContext(kundli: KundliData): boolean {
  const rahu = getPlanet(kundli, "Rahu");
  if (rahu && [3, 6, 10, 11].includes(rahu.house)) return true;
  if (!hasVarga(kundli, "D10")) return false;
  const d10 = getVarga(kundli, "D10");
  const d10Rahu = getPlanet(d10, "Rahu");
  const d10Mercury = getPlanet(d10, "Mercury");
  return !!(
    (d10Rahu && [10, 11].includes(d10Rahu.house)) ||
    (d10Mercury && [3, 6, 10, 11, 12].includes(d10Mercury.house))
  );
}

function d1WealthPromiseResult(kundli: KundliData, specs: CleanHouseSpec[]) {
  const wealthLords = specs.map(spec => ({ ...spec, lord: houseLord(kundli, spec.house), planet: getPlanet(kundli, houseLord(kundli, spec.house)) }));
  const punished = new Set<string>();
  const coreRows = wealthLords.map(row => {
    const strength = planetStrength(kundli, row.lord);
    const p = row.planet;
    let score = normPlanetScore(strength.score);
    const notes = [`${row.house}H lord ${row.lord}: ${score}%, ${strength.label}`];
    if (p) {
      notes.push(`${row.lord} placement: ${p.house}H`);
      if ([6, 8, 12].includes(p.house)) {
        const basePenalty = row.house === 2 || row.house === 11 ? 12 : 7;
        const penalty = row.lord === "Mercury" && p.house === 12 && hasMercuryModernContext(kundli)
          ? Math.round(basePenalty * 0.4)
          : basePenalty;
        score -= penalty;
        punished.add(`${row.lord}:dusthana`);
        notes.push(`${row.lord} in dusthana: ${penalty < basePenalty ? "modern/foreign-tech context reduces leakage" : "wealth leakage/debt pressure"} -${penalty}`);
      }
      if (isCombust(kundli, p)) {
        score = Math.round(score * 0.5);
        punished.add(`${row.lord}:combust`);
        notes.push(`${row.lord} combust: result capacity reduced by 50%`);
      }
      const sign = planetSign(p);
      if (sign != null && DEBIL[row.lord] === sign) {
        if (neechaBhanga(kundli, row.lord, sign)) {
          score = Math.max(score, 58);
          notes.push(`${row.lord} neecha-bhanga: debility penalty overridden, recovery trigger active`);
        } else {
          score -= 10;
          punished.add(`${row.lord}:debil`);
          notes.push(`${row.lord} debilitated without cancellation: direct weakness`);
        }
      }
    } else {
      notes.push(`${row.lord} placement: missing`);
    }
    return { ...row, score: Math.max(8, Math.min(96, score)), notes };
  });

  const coreScore = weighted(coreRows.map((row, idx) => [row.score, specs[idx].weight]));
  const lord2 = houseLord(kundli, 2);
  const lord11 = houseLord(kundli, 11);
  const lord5 = houseLord(kundli, 5);
  const lord9 = houseLord(kundli, 9);
  const p2 = getPlanet(kundli, lord2);
  const p11 = getPlanet(kundli, lord11);
  const p5 = getPlanet(kundli, lord5);
  const p9 = getPlanet(kundli, lord9);
  const p2Sign = planetSign(p2);
  const p11Sign = planetSign(p11);
  let yogaRaw = 50;
  const yogaFactors: string[] = [];
  if (p2 && p11 && p2.house === p11.house) {
    yogaRaw += 12;
    yogaFactors.push(`2H lord ${lord2} conjunct 11H lord ${lord11}: direct wealth link`);
  }
  if (p2 && p11Sign != null && hasAspect(p2, p11Sign)) {
    yogaRaw += 8;
    yogaFactors.push(`2H lord ${lord2} aspects 11H lord ${lord11}`);
  }
  if (p11 && p2Sign != null && hasAspect(p11, p2Sign)) {
    yogaRaw += 8;
    yogaFactors.push(`11H lord ${lord11} aspects 2H lord ${lord2}`);
  }
  for (const row of [
    { lord: lord5, planet: p5, label: "5H lord" },
    { lord: lord9, planet: p9, label: "9H lord" },
  ]) {
    const rowSign = planetSign(row.planet);
    if (!row.planet || rowSign == null) continue;
    if ([2, 11].includes(row.planet.house)) {
      yogaRaw += 7;
      yogaFactors.push(`${row.label} ${row.lord} placed in ${row.planet.house}H`);
    }
    if (p2Sign != null && hasAspect(row.planet, p2Sign)) {
      yogaRaw += 5;
      yogaFactors.push(`${row.label} ${row.lord} aspects 2H lord`);
    }
    if (p11Sign != null && hasAspect(row.planet, p11Sign)) {
      yogaRaw += 5;
      yogaFactors.push(`${row.label} ${row.lord} aspects 11H lord`);
    }
  }
  const yogaScore = Math.max(8, Math.min(96, yogaRaw + wealthYogaSupport(kundli)));
  if (!yogaFactors.length) yogaFactors.push("No strong 2H/11H/5H/9H lord link found");

  let occupantRaw = 50;
  const occupantFactors: string[] = [];
  for (const house of [2, 9, 10, 11]) {
    const occ = occupants(kundli, house);
    if (!occ.length) {
      occupantFactors.push(`${house}H occupants: none`);
      continue;
    }
    for (const p of occ) {
      let add = 0;
      if (house === 2) {
        if (BENEFICS.has(p.name)) add += 7;
        if (MALEFICS.has(p.name)) add -= p.name === "Sun" ? 4 : 8;
      } else if ([10, 11].includes(house)) {
        if (MALEFICS.has(p.name)) add += 7;
        if (BENEFICS.has(p.name)) add += 4;
      } else if (house === 9) {
        if (BENEFICS.has(p.name)) add += 5;
        if (MALEFICS.has(p.name)) add -= 2;
      }
      occupantRaw += add;
      occupantFactors.push(`${p.name} in ${house}H: ${add >= 0 ? "+" : ""}${add} (${house === 2 && MALEFICS.has(p.name) ? "savings pressure" : [10, 11].includes(house) && MALEFICS.has(p.name) ? "upachaya ambition" : "occupant effect"})`);
    }
  }
  const occupantScore = Math.max(8, Math.min(96, occupantRaw));

  let aspectRaw = 50;
  const aspectFactors: string[] = [];
  for (const house of [2, 9, 10, 11]) {
    const houseLordName = houseLord(kundli, house);
    const asp = aspectsToHouse(kundli, house);
    aspectRaw += asp.benefic.length * 5;
    for (const mal of asp.malefic) aspectRaw -= (FRIENDS[mal] ?? []).includes(houseLordName) ? 1 : 4;
    aspectFactors.push(`${house}H aspects: benefic ${asp.benefic.length ? asp.benefic.join(", ") : "none"}, malefic ${asp.malefic.length ? asp.malefic.join(", ") : "none"}`);
    const lordAsp = aspectNamesToPlanet(kundli, houseLordName);
    aspectRaw += lordAsp.benefic.length * 4;
    for (const mal of lordAsp.malefic) aspectRaw -= (FRIENDS[mal] ?? []).includes(houseLordName) ? 1 : 4;
    aspectFactors.push(`${house}H lord ${houseLordName} aspects received: benefic ${lordAsp.benefic.length ? lordAsp.benefic.join(", ") : "none"}, malefic ${lordAsp.malefic.length ? lordAsp.malefic.join(", ") : "none"}`);
  }
  const aspectScore = Math.max(8, Math.min(96, aspectRaw));

  const jupiterStrength = planetStrength(kundli, "Jupiter");
  const venusStrength = planetStrength(kundli, "Venus");
  const karakaScore = weighted([
    [normPlanetScore(jupiterStrength.score), 0.55],
    [normPlanetScore(venusStrength.score), 0.45],
  ]);

  let filterRaw = 50;
  const filterFactors: string[] = [];
  for (const row of coreRows) {
    const p = row.planet;
    if (!p) continue;
    if (isCombust(kundli, p)) {
      if (!punished.has(`${row.lord}:combust`)) {
        filterRaw -= 8;
        punished.add(`${row.lord}:combust`);
        filterFactors.push(`${row.lord} combust: penalty`);
      } else {
        filterFactors.push(`${row.lord} combust: already counted, duplicate skipped`);
      }
    }
    if ([6, 8, 12].includes(p.house) && [2, 11].includes(row.house)) {
      if (!punished.has(`${row.lord}:dusthana`)) {
        filterRaw -= 10;
        punished.add(`${row.lord}:dusthana`);
        filterFactors.push(`${row.house}H lord ${row.lord} in ${p.house}H: leakage/debt risk`);
      } else {
        filterFactors.push(`${row.house}H lord ${row.lord} dusthana: already counted, duplicate skipped`);
      }
    }
    const sign = planetSign(p);
    if (sign != null && DEBIL[row.lord] === sign) {
      if (neechaBhanga(kundli, row.lord, sign)) {
        filterRaw += 4;
        filterFactors.push(`${row.lord} neecha-bhanga: recovery trigger, no debility penalty stack`);
      } else {
        if (!punished.has(`${row.lord}:debil`)) {
          filterRaw -= 8;
          punished.add(`${row.lord}:debil`);
          filterFactors.push(`${row.lord} debilitation: penalty`);
        } else {
          filterFactors.push(`${row.lord} debilitation: already counted, duplicate skipped`);
        }
      }
    }
  }
  if (!filterFactors.length) filterFactors.push("No major combustion, dusthana leakage or unresolved debility penalty");
  const filterScore = Math.max(8, Math.min(96, filterRaw));

  const score = weighted([
    [coreScore, 0.35],
    [yogaScore, 0.20],
    [occupantScore, 0.15],
    [aspectScore, 0.12],
    [karakaScore, 0.10],
    [filterScore, 0.08],
  ]);

  return {
    score,
    factors: [
      `Loop 1 - Core house lords: ${coreScore}%`,
      ...coreRows.flatMap(row => row.notes),
      `Loop 2 - Dhan yoga links: ${yogaScore}%`,
      ...yogaFactors,
      `Loop 3 - Occupants with upachaya rule: ${occupantScore}%`,
      ...occupantFactors,
      `Loop 4 - Aspects on wealth houses and lords: ${aspectScore}%`,
      ...aspectFactors,
      `Loop 5 - Natural wealth karakas: ${karakaScore}%`,
      `Jupiter: ${normPlanetScore(jupiterStrength.score)}%, ${jupiterStrength.label}`,
      `Venus: ${normPlanetScore(venusStrength.score)}%, ${venusStrength.label}`,
      `Loop 6 - Edge filters: ${filterScore}%`,
      ...filterFactors,
    ],
  };
}

function horaNameForSign(sign: number | null): "Moon Hora" | "Sun Hora" | "Other Hora" {
  if (sign === 3) return "Moon Hora";
  if (sign === 4) return "Sun Hora";
  return "Other Hora";
}

function horaNameForPlanet(chart: KundliData, planet: string): "Moon Hora" | "Sun Hora" | "Other Hora" {
  return horaNameForSign(planetSign(getPlanet(chart, planet)));
}

function d2HoraCapacityResult(kundli: KundliData, wealthBase: number) {
  if (!hasVarga(kundli, "D2")) {
    const fallback = weighted([
      [wealthBase, 0.45],
      [normPlanetScore(planetStrength(kundli, "Jupiter").score), 0.30],
      [normPlanetScore(planetStrength(kundli, "Venus").score), 0.25],
    ]);
    return {
      score: fallback,
      factors: [
        "D2 missing: fallback used",
        `Fallback D1 2H: ${wealthBase}%`,
        `Fallback Jupiter strength: ${normPlanetScore(planetStrength(kundli, "Jupiter").score)}%`,
        `Fallback Venus strength: ${normPlanetScore(planetStrength(kundli, "Venus").score)}%`,
        `Aggregate fallback: ${fallback}%`,
      ],
    };
  }

  const d2 = getVarga(kundli, "D2");
  const d1LagnaLord = houseLord(kundli, 1);
  const d1Lord2 = houseLord(kundli, 2);
  const d1Lord11 = houseLord(kundli, 11);
  const planets = d2.planets ?? [];
  const moonHoraCount = planets.filter(p => horaNameForPlanet(d2, p.name) === "Moon Hora").length;
  const sunHoraCount = planets.filter(p => horaNameForPlanet(d2, p.name) === "Sun Hora").length;
  const keyPlanets = [d1LagnaLord, d1Lord2, d1Lord11, "Jupiter"];
  const keyMoonCount = keyPlanets.filter(p => horaNameForPlanet(d2, p) === "Moon Hora").length;
  const keySunCount = keyPlanets.filter(p => horaNameForPlanet(d2, p) === "Sun Hora").length;
  const dominanceScore = Math.max(8, Math.min(96, Math.round(
    48 + (moonHoraCount - sunHoraCount) * 2.5 + keyMoonCount * 7 - keySunCount * 2
  )));

  const d2LagnaSign = signOf(d2.ascendantDeg ?? 0);
  const d2FirstOcc = occupants(d2, 1);
  let lagnaRaw = d2LagnaSign === 3 ? 62 : d2LagnaSign === 4 ? 56 : 50;
  const lagnaFactors = [`D2 Lagna: ${signShortFromIndex(d2LagnaSign)} (${horaNameForSign(d2LagnaSign)})`];
  if (!d2FirstOcc.length) lagnaFactors.push("D2 1H occupants: none");
  for (const p of d2FirstOcc) {
    let add = 0;
    if (BENEFICS.has(p.name)) add += 7;
    else if (["Sun", "Mars", "Rahu"].includes(p.name)) add += d2LagnaSign === 4 ? 4 : 1;
    else if (["Saturn", "Ketu"].includes(p.name)) add -= 3;
    lagnaRaw += add;
    lagnaFactors.push(`${p.name} in D2 1H: ${add >= 0 ? "+" : ""}${add}`);
  }
  const lagnaScore = Math.max(8, Math.min(96, Math.round(lagnaRaw)));

  const d2SecondOcc = occupants(d2, 2);
  let vaultRaw = 50;
  const vaultFactors: string[] = [];
  if (!d2SecondOcc.length) vaultFactors.push("D2 2H vault occupants: none");
  for (const p of d2SecondOcc) {
    let add = 0;
    if (["Jupiter", "Venus", "Mercury"].includes(p.name)) add += 10;
    else if (["Rahu", "Ketu", "Mars"].includes(p.name)) add -= 10;
    else if (p.name === "Saturn") add -= 3;
    else if (p.name === "Moon") add += 4;
    else if (p.name === "Sun") add += 1;
    vaultRaw += add;
    vaultFactors.push(`${p.name} in D2 2H vault: ${add >= 0 ? "+" : ""}${add}`);
  }
  const vaultScore = Math.max(8, Math.min(96, Math.round(vaultRaw)));

  const jupiterHora = horaNameForPlanet(d2, "Jupiter");
  const venusHora = horaNameForPlanet(d2, "Venus");
  const karakaScore = weighted([
    [jupiterHora === "Moon Hora" ? 82 : jupiterHora === "Sun Hora" ? 58 : 50, 0.55],
    [venusHora === "Moon Hora" ? 78 : venusHora === "Sun Hora" ? 60 : 50, 0.45],
  ]);

  const d1Lord2InD2 = getPlanet(d2, d1Lord2);
  const d1Lord11InD2 = getPlanet(d2, d1Lord11);
  let crossRaw = 50;
  const crossFactors = [
    `D1 2H lord ${d1Lord2} in D2: ${d1Lord2InD2?.house ?? "missing"}H, ${horaNameForPlanet(d2, d1Lord2)}`,
    `D1 11H lord ${d1Lord11} in D2: ${d1Lord11InD2?.house ?? "missing"}H, ${horaNameForPlanet(d2, d1Lord11)}`,
  ];
  if (d1Lord2InD2?.house === 2) {
    crossRaw += 8;
    crossFactors.push(`D1 2H lord ${d1Lord2} in D2 2H: savings capacity support`);
  }
  if (d1Lord11InD2?.house === 2) {
    crossRaw += 14;
    crossFactors.push(`D1 11H lord ${d1Lord11} in D2 2H: double bonus, income converts to savings`);
  }
  if (horaNameForPlanet(d2, d1Lord2) === "Moon Hora") crossRaw += 5;
  if (horaNameForPlanet(d2, d1Lord11) === "Moon Hora") crossRaw += 5;
  if (d1Lord2InD2 && [6, 8, 12].includes(d1Lord2InD2.house)) crossRaw -= 6;
  if (d1Lord11InD2 && [6, 8, 12].includes(d1Lord11InD2.house)) crossRaw -= 6;
  const crossScore = Math.max(8, Math.min(96, Math.round(crossRaw)));

  const score = weighted([
    [dominanceScore, 0.30],
    [lagnaScore, 0.18],
    [vaultScore, 0.22],
    [karakaScore, 0.16],
    [crossScore, 0.14],
  ]);

  return {
    score,
    factors: [
      `Loop 1 - Sun/Moon Hora dominance: ${dominanceScore}%`,
      `Moon Hora planets: ${moonHoraCount}`,
      `Sun Hora planets: ${sunHoraCount}`,
      `Key planets in Moon Hora: ${keyMoonCount}/${keyPlanets.length}`,
      `Key planets in Sun Hora: ${keySunCount}/${keyPlanets.length}`,
      `Loop 2 - D2 Lagna/1H wealth attitude: ${lagnaScore}%`,
      ...lagnaFactors,
      `Loop 3 - D2 2H vault: ${vaultScore}%`,
      ...vaultFactors,
      `Loop 4 - Jupiter/Venus Hora status: ${karakaScore}%`,
      `Jupiter: ${jupiterHora}`,
      `Venus: ${venusHora}`,
      `Loop 5 - D1 wealth lords in D2: ${crossScore}%`,
      ...crossFactors,
    ],
  };
}

function d10DignityPoints(chart: KundliData, planet: string) {
  const p = getPlanet(chart, planet);
  const sign = planetSign(p);
  const dig = dignity(planet, sign);
  let points = 0;
  if (dig.label === "exalted" || dig.label === "own sign") points = 5;
  else if (dig.label === "friendly sign") points = 3;
  else if (dig.label === "enemy sign") points = -2;
  else if (dig.label === "debilitated") points = neechaBhanga(chart, planet, sign) ? 2 : -3;
  return { points, label: dig.label, house: p?.house };
}

function d10IncomeEngineResult(kundli: KundliData, fallbackCareer: number) {
  if (!hasVarga(kundli, "D10")) {
    return {
      score: fallbackCareer,
      factors: ["D10 missing", `Fallback from career dimension: ${fallbackCareer}%`],
    };
  }

  const d10 = getVarga(kundli, "D10");
  const lord10 = houseLord(d10, 10);
  const lord11 = houseLord(d10, 11);
  const p10 = getPlanet(d10, lord10);
  const p11 = getPlanet(d10, lord11);
  const p10Sign = planetSign(p10);
  const p11Sign = planetSign(p11);
  let points = 0;
  const factors: string[] = [];

  const lord10Dig = d10DignityPoints(d10, lord10);
  const lord11Dig = d10DignityPoints(d10, lord11);
  points += lord10Dig.points + lord11Dig.points;
  factors.push(`D10 10H lord ${lord10}: ${lord10Dig.label}, ${lord10Dig.points >= 0 ? "+" : ""}${lord10Dig.points}, placed ${lord10Dig.house ?? "missing"}H`);
  factors.push(`D10 11H lord ${lord11}: ${lord11Dig.label}, ${lord11Dig.points >= 0 ? "+" : ""}${lord11Dig.points}, placed ${lord11Dig.house ?? "missing"}H`);

  const connected = !!(p10 && p11 && (
    p10.house === p11.house ||
    (p11Sign != null && hasAspect(p10, p11Sign)) ||
    (p10Sign != null && hasAspect(p11, p10Sign))
  ));
  if (connected) {
    points += 5;
    factors.push(`10L ${lord10} and 11L ${lord11} connected by conjunction/aspect: +5`);
  } else {
    factors.push(`10L ${lord10} and 11L ${lord11} connection: not found`);
  }

  const exchangeLike = p10?.house === 11 || p11?.house === 10;
  if (exchangeLike) {
    points += 5;
    factors.push(`10L/11L placed in each other's income nodes: +5`);
  } else {
    factors.push("10L in 11H / 11L in 10H: not found");
  }

  if (p11?.house === 2) {
    points += 4;
    factors.push(`D10 11H lord ${lord11} in 2H: gains flowing into savings +4`);
  } else {
    factors.push(`D10 11H lord ${lord11} in ${p11?.house ?? "missing"}H: no 2H vault bonus`);
  }

  let companionPoints = 0;
  for (const row of [
    { label: "10H lord", lord: lord10, planet: p10 },
    { label: "11H lord", lord: lord11, planet: p11 },
  ]) {
    if (!row.planet) continue;
    const companions = occupants(d10, row.planet.house).filter(p => p.name !== row.lord);
    if (!companions.length) {
      factors.push(`${row.label} ${row.lord} companion support: none`);
      continue;
    }
    for (const comp of companions) {
      const compDig = d10DignityPoints(d10, comp.name);
      const add = compDig.label === "exalted" || compDig.label === "own sign" ? 3 : 0;
      companionPoints += add;
      factors.push(`${row.label} ${row.lord} with ${comp.name}: ${compDig.label}, support ${add >= 0 ? "+" : ""}${add}`);
    }
  }
  companionPoints = Math.min(6, companionPoints);
  points += companionPoints;
  factors.push(`Companion support total: +${companionPoints}`);

  let upachayaPoints = 0;
  for (const house of [10, 11]) {
    const occ = occupants(d10, house);
    if (!occ.length) {
      factors.push(`D10 ${house}H occupants: none`);
      continue;
    }
    for (const p of occ) {
      let add = 0;
      if (["Saturn", "Mars", "Rahu", "Sun"].includes(p.name)) add = 2;
      else if (["Jupiter", "Venus"].includes(p.name)) add = 1;
      upachayaPoints += add;
      factors.push(`${p.name} in D10 ${house}H: ${add >= 0 ? "+" : ""}${add} (${add === 2 ? "upachaya ambition boost" : add === 1 ? "smooth support" : "neutral"})`);
    }
  }
  upachayaPoints = Math.min(8, upachayaPoints);
  points += upachayaPoints;
  factors.push(`Upachaya occupant boost total: +${upachayaPoints}`);

  let bridgePoints = 0;
  for (const house of [10, 11]) {
    const d1Lord = houseLord(kundli, house);
    const p = getPlanet(d10, d1Lord);
    let add = 0;
    if (p && [1, 4, 5, 7, 9, 10].includes(p.house)) add = 3;
    else if (p && [6, 8, 12].includes(p.house)) add = -2;
    bridgePoints += add;
    factors.push(`D1 ${house}H lord ${d1Lord} in D10: ${p?.house ?? "missing"}H, bridge ${add >= 0 ? "+" : ""}${add}`);
  }
  points += bridgePoints;
  factors.push(`D1-to-D10 bridge total: ${bridgePoints >= 0 ? "+" : ""}${bridgePoints}`);

  const score = Math.max(8, Math.min(96, Math.round(50 + points * 1.5)));
  return {
    score,
    factors: [
      `D10 raw points: ${points >= 0 ? "+" : ""}${points}`,
      `Normalized D10 income score: ${score}%`,
      ...factors,
    ],
  };
}

function exactCombust(kundli: KundliData, p: PlanetInfo | undefined, limit = 8): boolean {
  if (!p || p.name === "Sun") return false;
  const sun = getPlanet(kundli, "Sun");
  if (!sun || typeof sun.longitude !== "number" || typeof p.longitude !== "number") return false;
  const diff = Math.min(Math.abs(p.longitude - sun.longitude), 360 - Math.abs(p.longitude - sun.longitude));
  return diff < limit;
}

function vipreetException(kundli: KundliData, planet: string, p: PlanetInfo | undefined): boolean {
  if (!p || ![6, 8, 12].includes(p.house)) return false;
  return lordedHouses(kundli, planet).some(h => [6, 8, 12].includes(h));
}

function d9WealthValidationResult(kundli: KundliData) {
  if (!hasVarga(kundli, "D9")) {
    return {
      modifier: 0,
      score: 50,
      factors: ["D9 missing: neutral validator"],
    };
  }
  const d9 = getVarga(kundli, "D9");
  const houses = [2, 5, 9, 11];
  let modifier = 0;
  const factors: string[] = [];
  for (const house of houses) {
    const lord = houseLord(kundli, house);
    const p = getPlanet(d9, lord);
    const sign = planetSign(p);
    const dig = dignity(lord, sign);
    let add = 0;
    if (dig.label === "exalted" || dig.label === "own sign") add = 1.5;
    else if (dig.label === "debilitated") add = -1.5;
    modifier += add;
    factors.push(`D1 ${house}H lord ${lord} in D9: ${dig.label}, placed ${p?.house ?? "missing"}H, modifier ${add >= 0 ? "+" : ""}${add}`);
  }
  modifier = Math.max(-5, Math.min(5, modifier));
  return {
    modifier,
    score: Math.max(8, Math.min(96, Math.round(50 + modifier * 8))),
    factors: [
      `Applied D9 modifier: ${modifier >= 0 ? "+" : ""}${modifier}`,
      ...factors,
    ],
  };
}

function globalWealthLeakagePenalty(kundli: KundliData) {
  let penalty = 0;
  const factors: string[] = [];
  for (const house of [2, 11]) {
    const lord = houseLord(kundli, house);
    const p = getPlanet(kundli, lord);
    if (p && [6, 8, 12].includes(p.house)) {
      if (vipreetException(kundli, lord, p)) {
        factors.push(`${house}H lord ${lord} in ${p.house}H: Vipreet exception, no -5`);
      } else {
        penalty -= 5;
        factors.push(`${house}H lord ${lord} in ${p.house}H: direct leakage penalty -5`);
      }
    } else {
      factors.push(`${house}H lord ${lord} dusthana placement: clear`);
    }
    if (exactCombust(kundli, p, 8)) {
      penalty -= 3;
      factors.push(`${house}H lord ${lord} combust within 8 degrees: -3`);
    } else {
      factors.push(`${house}H lord ${lord} combustion under 8 degrees: clear`);
    }
  }
  if (occupants(kundli, 2).some(p => p.name === "Ketu")) {
    penalty -= 1;
    factors.push("Ketu in 2H: savings/family expense volatility -1");
  } else {
    factors.push("Ketu in 2H: not present");
  }
  if (occupants(kundli, 8).some(p => p.name === "Rahu")) {
    penalty -= 1;
    factors.push("Rahu in 8H: sudden/unconventional finance volatility -1");
  } else {
    factors.push("Rahu in 8H: not present");
  }
  return {
    penalty,
    score: Math.max(8, Math.min(96, Math.round(50 + penalty * 6))),
    factors: [
      `Applied global leakage penalty: ${penalty}`,
      ...factors,
    ],
  };
}

function modernWealthModifier(kundli: KundliData) {
  let modifier = 0;
  const factors: string[] = [];
  const rahu = getPlanet(kundli, "Rahu");
  const mercury = getPlanet(kundli, "Mercury");
  const saturn = getPlanet(kundli, "Saturn");

  if (rahu && [3, 6, 10, 11].includes(rahu.house)) {
    modifier += 2;
    factors.push(`Rahu in ${rahu.house}H: modern scaling/upachaya ambition +2`);
  } else if (rahu?.house === 8) {
    modifier += 1;
    factors.push("Rahu in 8H: hidden systems/research/speculative transformation +1");
  } else {
    factors.push("Rahu modern scaling: neutral");
  }

  if (mercury && [3, 6, 10, 11, 12].includes(mercury.house)) {
    modifier += mercury.house === 12 ? 1.5 : 2;
    factors.push(`Mercury in ${mercury.house}H: digital/trade/remote earning channel +${mercury.house === 12 ? 1.5 : 2}`);
  } else {
    factors.push("Mercury digital/trade channel: neutral");
  }

  if (saturn && [3, 6, 10, 11].includes(saturn.house)) {
    modifier += 1.5;
    factors.push(`Saturn in ${saturn.house}H: persistence/compounding work ethic +1.5`);
  } else if (planetStrength(kundli, "Saturn").label.includes("corrected")) {
    modifier += 1;
    factors.push("Saturn neecha-bhanga: slow compounding recovery +1");
  } else {
    factors.push("Saturn persistence modifier: neutral");
  }

  if (hasVarga(kundli, "D10")) {
    const d10 = getVarga(kundli, "D10");
    const d10Rahu = getPlanet(d10, "Rahu");
    const d10Saturn = getPlanet(d10, "Saturn");
    const d10Mercury = getPlanet(d10, "Mercury");
    if (d10Rahu && [10, 11].includes(d10Rahu.house)) {
      modifier += 2;
      factors.push(`D10 Rahu in ${d10Rahu.house}H: career-scale ambition +2`);
    }
    if (d10Rahu?.house === 11 || d10Saturn?.house === 11) {
      modifier += 2;
      factors.push("Grand booster: D10 Rahu/Saturn in 11H self-made scaling pattern +2");
    }
    if (d10Mercury && [3, 6, 10, 11, 12].includes(d10Mercury.house)) {
      modifier += 1;
      factors.push(`D10 Mercury in ${d10Mercury.house}H: income via systems/communication +1`);
    }
  }

  modifier = Math.max(0, Math.min(8, modifier));
  return {
    modifier,
    score: Math.max(8, Math.min(96, Math.round(50 + modifier * 6))),
    factors: [
      `Applied modern wealth modifier: +${Math.round(modifier * 10) / 10}`,
      ...factors,
    ],
  };
}

function trajectoryResult(d1Score: number, d2Score: number, d10Score: number, modernModifier: number) {
  const earlyFriction = Math.max(0, 60 - d1Score) * 0.12;
  const futureScaling = Math.max(0, d2Score - 60) * 0.10 + Math.max(0, d10Score - 60) * 0.12 + modernModifier * 0.45;
  const slope = Math.max(-4, Math.min(6, futureScaling - earlyFriction));
  const label = slope >= 3 ? "Current friction, strong future scaling"
    : slope >= 1 ? "Gradual upward wealth trajectory"
      : slope <= -2 ? "Current friction needs discipline"
        : "Stable wealth trajectory";
  return {
    modifier: Math.round(slope * 10) / 10,
    score: Math.max(8, Math.min(96, Math.round(50 + slope * 7))),
    factors: [
      `Trajectory slope: ${slope >= 0 ? "+" : ""}${Math.round(slope * 10) / 10}`,
      `Early friction from D1: -${Math.round(earlyFriction * 10) / 10}`,
      `Future scaling from D2/D10/modern indicators: +${Math.round(futureScaling * 10) / 10}`,
      label,
    ],
  };
}

function dashaTime(value?: string) {
  if (!value) return NaN;
  const time = new Date(value).getTime();
  return Number.isFinite(time) ? time : NaN;
}

function isActiveDashaWindow(item: { startDate?: string; endDate?: string }, now: number) {
  const start = dashaTime(item.startDate);
  const end = dashaTime(item.endDate);
  return Number.isFinite(start) && Number.isFinite(end) && start <= now && now <= end;
}

function resolveCurrentDasha(kundli: KundliData) {
  const currentMaha = kundli.currentDasha?.maha || "";
  const currentAntar = kundli.currentDasha?.antar || "";
  if (currentMaha || currentAntar) {
    return {
      maha: currentMaha,
      antar: currentAntar,
      startDate: kundli.currentDasha?.startDate,
      endDate: kundli.currentDasha?.endDate,
      source: "currentDasha field",
    };
  }

  const now = Date.now();
  const activeMaha = kundli.dashas?.find(item => isActiveDashaWindow(item, now));
  const activeAntar = activeMaha?.subDashas?.find(item => isActiveDashaWindow(item, now));
  return {
    maha: activeMaha?.planet || "",
    antar: activeAntar?.planet || "",
    startDate: activeAntar?.startDate ?? activeMaha?.startDate,
    endDate: activeAntar?.endDate ?? activeMaha?.endDate,
    source: activeMaha ? "dashas timeline fallback" : "missing",
  };
}

function dashaPlanetMultiplier(kundli: KundliData, planet: string) {
  if (!planet) return { multiplier: 1, factors: ["Dasha planet missing: neutral"] };
  let multiplier = 1;
  const factors: string[] = [];
  const p = getPlanet(kundli, planet);
  const d1Strength = planetStrength(kundli, planet);
  const d1Sign = planetSign(p);
  const d1Dignity = dignity(planet, d1Sign);
  const lordships = lordedHouses(kundli, planet);

  factors.push(`${planet} D1 strength: ${normPlanetScore(d1Strength.score)}%, ${d1Strength.label}`);
  factors.push(p ? `${planet} D1 placement: ${p.house}H, ${d1Sign == null ? "unknown sign" : signShortFromIndex(d1Sign)}` : `${planet} D1 placement: missing`);
  factors.push(`${planet} lordship: ${lordships.length ? lordships.map(h => `${h}H`).join(", ") : "not a classical house lord"}`);

  if (p && [3, 6, 10, 11].includes(p.house)) {
    multiplier += 0.15;
    factors.push(`${planet} in D1 ${p.house}H upachaya: +0.15`);
  }

  let d9Strong = false;
  if (hasVarga(kundli, "D9")) {
    const d9 = getVarga(kundli, "D9");
    const d9Planet = getPlanet(d9, planet);
    const d9Dig = dignity(planet, planetSign(d9Planet));
    factors.push(`${planet} D9 placement: ${d9Planet?.house ?? "missing"}H, ${d9Dig.label}`);
    if (d9Dig.label === "exalted" || d9Dig.label === "own sign") {
      d9Strong = true;
      factors.push(`${planet} in D9 ${d9Dig.label}: strength support`);
    }
  } else {
    factors.push(`${planet} D9 placement: not available`);
  }
  if (d1Dignity.label === "exalted" || d1Dignity.label === "own sign" || d9Strong) {
    multiplier += 0.10;
    factors.push(`${planet} D1/D9 dignity support: +0.10`);
  }

  if (hasVarga(kundli, "D10")) {
    const d10 = getVarga(kundli, "D10");
    const d10Planet = getPlanet(d10, planet);
    factors.push(`${planet} D10 placement: ${d10Planet?.house ?? "missing"}H`);
    if (d10Planet && [2, 10, 11].includes(d10Planet.house)) {
      multiplier += 0.10;
      factors.push(`${planet} in D10 ${d10Planet.house}H income node: +0.10`);
    }
  } else {
    factors.push(`${planet} D10 placement: not available`);
  }

  if (hasVarga(kundli, "D2")) {
    const d2 = getVarga(kundli, "D2");
    const d2Planet = getPlanet(d2, planet);
    const d2Hora = horaNameForSign(planetSign(d2Planet));
    factors.push(`${planet} D2 placement: ${d2Planet?.house ?? "missing"}H, ${d2Hora}`);
    const wealthLords = [houseLord(kundli, 2), houseLord(kundli, 9), houseLord(kundli, 11)];
    if (d2Hora === "Moon Hora" && wealthLords.includes(planet)) {
      multiplier += 0.05;
      factors.push(`${planet} is wealth lord in D2 Moon Hora: +0.05`);
    }
  } else {
    factors.push(`${planet} D2 placement: not available`);
  }

  const hasSupport = d9Strong || hasMercuryModernContext(kundli) || d1Strength.label.includes("corrected");
  if (p && [8, 12].includes(p.house) && !hasSupport) {
    multiplier -= 0.15;
    factors.push(`${planet} in D1 ${p.house}H without support: -0.15`);
  } else if (p && [8, 12].includes(p.house)) {
    factors.push(`${planet} in D1 ${p.house}H but support present: no loss penalty`);
  }

  if (d1Dignity.label === "debilitated" && !d1Strength.label.includes("corrected")) {
    multiplier -= 0.10;
    factors.push(`${planet} debilitated without neecha-bhanga: -0.10`);
  }

  multiplier = Math.max(0.80, Math.min(1.25, multiplier));
  return {
    multiplier,
    factors: [`${planet} multiplier: ${Math.round(multiplier * 100) / 100}`, ...factors],
  };
}

export function calculateWealthOperationalScore(kundli: KundliData | null | undefined, baseScore: number) {
  if (!kundli) {
    return { score: Math.round(baseScore), multiplier: 1, factors: ["Kundli missing: neutral dasha multiplier"] };
  }
  const activeDasha = resolveCurrentDasha(kundli);
  const md = activeDasha.maha;
  const ad = activeDasha.antar;
  const mdResult = dashaPlanetMultiplier(kundli, md);
  const adResult = dashaPlanetMultiplier(kundli, ad);
  const multiplier = Math.max(0.80, Math.min(1.25, mdResult.multiplier * 0.60 + adResult.multiplier * 0.40));
  return {
    score: Math.max(8, Math.min(96, Math.round(baseScore * multiplier))),
    multiplier,
    factors: [
      `Active dasha: MD ${md || "missing"} / AD ${ad || "missing"}`,
      activeDasha.startDate && activeDasha.endDate ? `Active dasha period: ${activeDasha.startDate} to ${activeDasha.endDate}` : "Active dasha period: missing",
      `Dasha source: ${activeDasha.source}`,
      `MD ${md || "missing"} weight 60%: ${Math.round(mdResult.multiplier * 100) / 100}`,
      ...mdResult.factors,
      `AD ${ad || "missing"} weight 40%: ${Math.round(adResult.multiplier * 100) / 100}`,
      ...adResult.factors,
      `Final dasha multiplier: ${Math.round(multiplier * 100) / 100}`,
    ],
  };
}

function wealthBuilderResult(kundli: KundliData, valueOf: (key: string) => number, wealthBase: number) {
  const d1Specs: CleanHouseSpec[] = [
    { house: 2, weight: 0.30, karakas: ["Jupiter", "Venus", "Mercury"] },
    { house: 11, weight: 0.30, karakas: ["Jupiter", "Saturn"] },
    { house: 10, weight: 0.25, karakas: ["Sun", "Saturn", "Mercury"] },
    { house: 9, weight: 0.15, karakas: ["Jupiter", "Sun"] },
  ];
  const d1Wealth = d1WealthPromiseResult(kundli, d1Specs);
  const wealthPlanetRows = ["Jupiter", "Venus", "Mercury", "Saturn"].map(name => {
    const strength = planetStrength(kundli, name);
    return { name, score: normPlanetScore(strength.score), strength };
  });
  const wealthPlanetScore = weighted([
    [wealthPlanetRows[0].score, 0.30],
    [wealthPlanetRows[1].score, 0.24],
    [wealthPlanetRows[2].score, 0.24],
    [wealthPlanetRows[3].score, 0.22],
  ]);
  const d2Hora = d2HoraCapacityResult(kundli, wealthBase);
  const d10Income = d10IncomeEngineResult(kundli, valueOf("career"));
  const d9Validation = d9WealthValidationResult(kundli);
  const wealthAshtak = wealthAshtakavargaModifier(kundli);
  const globalLeakage = globalWealthLeakagePenalty(kundli);
  const modernWealth = modernWealthModifier(kundli);
  const trajectory = trajectoryResult(d1Wealth.score, d2Hora.score, d10Income.score, modernWealth.modifier);
  const highPotentialOverride = d2Hora.score >= 65 && d10Income.score >= 65;

  let score = highPotentialOverride
    ? weighted([
      [d1Wealth.score, 0.20],
      [d2Hora.score, 0.35],
      [d10Income.score, 0.30],
      [wealthPlanetScore, 0.10],
      [50 + wealthYogaSupport(kundli), 0.05],
    ])
    : weighted([
      [d1Wealth.score, 0.40],
      [d2Hora.score, 0.25],
      [d10Income.score, 0.20],
      [wealthPlanetScore, 0.10],
      [50 + wealthYogaSupport(kundli), 0.05],
    ]);
  score += d9Validation.modifier;
  score += wealthAshtak.modifier;
  score += modernWealth.modifier;
  score += trajectory.modifier;
  score += globalLeakage.penalty;
  const baseScore = Math.max(8, Math.min(96, Math.round(score)));
  const operationalWealth = calculateWealthOperationalScore(kundli, baseScore);
  const details: KundliCategoryDetailRow[] = [
    {
      key: "money-d1",
      label: "D1 wealth promise",
      score: d1Wealth.score,
      weightPct: 40,
      detail: "D1 runs the 6-loop wealth blueprint: lords, yogas, occupants, aspects, karakas and edge filters.",
      factors: d1Wealth.factors,
    },
    {
      key: "money-d2",
      label: "D2 capacity",
      score: d2Hora.score,
      weightPct: 25,
      detail: "D2 runs the 5-loop Hora blueprint: Sun/Moon dominance, Lagna, vault, Jupiter/Venus and D1 wealth-lord status.",
      factors: d2Hora.factors,
    },
    {
      key: "money-d10",
      label: "D10 income engine",
      score: d10Income.score,
      weightPct: 20,
      detail: "D10 checks only career-to-income wealth generation: 10L/11L nodes, companions, upachaya occupants and D1 bridge.",
      factors: d10Income.factors,
    },
    {
      key: "money-planets",
      label: "Wealth planets",
      score: wealthPlanetScore,
      weightPct: 10,
      detail: "Jupiter, Venus, Mercury and Saturn are checked for dignity and placement.",
      factors: wealthPlanetRows.map(row => `${row.name}: ${row.score}%, ${row.strength.label}`),
    },
    {
      key: "money-dasha",
      label: "Current dasha timing",
      score: operationalWealth.score,
      weightPct: 0,
      detail: "Shows which Mahadasha/Antardasha is running now, their placement/strength, and the current finance operating score.",
      factors: [
        `Money Builder base score: ${baseScore}%`,
        `Dasha-adjusted current score: ${operationalWealth.score}%`,
        ...operationalWealth.factors,
      ],
    },
    {
      key: "money-yoga",
      label: "Dhan-yoga links",
      score: Math.max(8, Math.min(96, Math.round(50 + wealthYogaSupport(kundli)))),
      weightPct: 5,
      detail: "Links among 2H/5H/9H/10H/11H lords add a small support only.",
      factors: [`Dhan-yoga support: +${Math.round(wealthYogaSupport(kundli))}`],
    },
  ];
  details.push({
    key: "money-d9",
    label: "D9 validation",
    score: d9Validation.score,
    weightPct: 0,
    detail: "D9 is only a reality check: D1 2L/5L/9L/11L sustain wealth in Navamsha or not.",
    factors: d9Validation.factors,
  });
  details.push({
    key: "money-ashtak",
    label: "Ashtakavarga validator",
    score: Math.max(8, Math.min(96, Math.round(50 + wealthAshtak.modifier * 10))),
    weightPct: 0,
    detail: "2H and 11H bindu support acts as a small validator.",
    factors: [
      ...wealthAshtak.factors,
      `Applied modifier: ${wealthAshtak.modifier >= 0 ? "+" : ""}${Math.round(wealthAshtak.modifier * 10) / 10}`,
    ],
  });
  details.push({
    key: "money-global-leakage",
    label: "Global leakage penalty",
    score: globalLeakage.score,
    weightPct: 0,
    detail: "Final absolute deduction after D1/D2/D10/D9/Ashtakavarga: dusthana wealth lords, exact combustion, Ketu/Rahu leakage.",
    factors: globalLeakage.factors,
  });
  details.push({
    key: "money-modern",
    label: "Modern wealth modifier",
    score: modernWealth.score,
    weightPct: 0,
    detail: "Small calibration for modern wealth generation: digital work, unconventional systems, upachaya Rahu/Mercury and Saturn persistence.",
    factors: modernWealth.factors,
  });
  details.push({
    key: "money-trajectory",
    label: "Trajectory resolver",
    score: trajectory.score,
    weightPct: 0,
    detail: "Resolves contradiction between early friction and future scaling indicators.",
    factors: [
      highPotentialOverride
        ? "Synthesis priority active: D2 and D10 both cross 65%, D1 weight reduced"
        : "Synthesis priority inactive: standard D1/D2/D10 weights used",
      ...trajectory.factors,
    ],
  });
  return {
    score: baseScore,
    details,
    checked: [
      "Current Mahadasha/Antardasha operational timing",
      "D1 2H/11H/10H/9H",
      "D2 Sun/Moon Hora dominance, Lagna, vault, Jupiter/Venus and D1 wealth lords",
      "D10 10L/11L relation, companion backup, upachaya occupants and D1 bridge",
      "Jupiter/Venus/Mercury/Saturn",
      "Dhan-yoga links",
      "D9 validation, threshold Ashtakavarga, modern wealth modifier and global leakage penalty",
    ],
    rules: [
      "Old backend Finance Wealth Category is not used; this Money Builder score now feeds LifeMap Finance category.",
      "D1, D2 and D10 carry the main score.",
      "D10 uses only the income engine checks: 10L/11L dignity, connection/exchange/vault, companion support, upachaya occupants and D1-to-D10 bridge.",
      "D2 uses only the 5 Hora checks; if D2 is missing, fallback uses D1 2H plus Jupiter and Venus strength.",
      "Ashtakavarga uses SAV thresholds: >32 support, 26-31 neutral, <24 friction.",
      "D9 validates D1 2L/5L/9L/11L only; each exalted/own lord gives +1.5 and each debilitated lord gives -1.5, capped at +/-5.",
      "Modern wealth modifier adds a small capped boost for digital/unconventional earning signatures.",
      "Synthesis resolver reduces D1 drag when both D2 vault and D10 income engine are high-potential.",
      "Penalty stacking control follows one weakness, one punch: duplicate debility/dusthana/combustion penalties are skipped.",
      "Global leakage is a final direct deduction, but Ketu 2H and Rahu 8H are treated as volatility rather than absolute poverty.",
      "Current dasha uses MD 60% and AD 40% to create an operational finance score; if currentDasha is absent, active dashas timeline is used.",
    ],
  };
}

function buildStrictPowerOptions(kundli: KundliData, valueOf: (key: string) => number, wealthBase: number) {
  const lagnaLord = houseLord(kundli, 1);
  const ak = atmakaraka(kundli);
  const coreIdentity = weighted([
    [normPlanetScore(planetStrength(kundli, lagnaLord).score), 0.34],
    [normPlanetScore(planetStrength(kundli, "Moon").score), 0.24],
    [normPlanetScore(planetStrength(kundli, "Sun").score), 0.20],
    [valueOf("nature"), 0.14],
    [ak ? normPlanetScore(planetStrength(kundli, ak.name).score) : 50, 0.08],
  ]);
  const naturalLeader = cleanCategoryResult({
    kundli,
    d1: [
      { house: 1, weight: 0.30, karakas: ["Sun", "Mars"] },
      { house: 10, weight: 0.28, karakas: ["Sun", "Saturn"] },
      { house: 3, weight: 0.14, karakas: ["Mars"] },
    ],
    planets: [{ name: "Sun", weight: 0.14 }, { name: "Mars", weight: 0.08 }, { name: lagnaLord, weight: 0.06 }],
    vargas: [{ chart: "D10", houses: [1, 10], karakas: ["Sun", "Saturn", "Mercury"], weight: 0.18 }],
    checked: ["D1 Lagna", "D1 10H authority", "D1 3H courage", "Sun/Mars drive", "D10 career authority"],
    rules: ["Leadership is judged from Lagna, 10H and 3H.", "D10 validates authority only.", "Dignity, friendly/enemy sign, exalted/debilitated state and affliction are included inside each house/planet strength."],
  });
  const emotionalSoul = cleanCategoryResult({
    kundli,
    d1: [
      { house: 4, weight: 0.32, karakas: ["Moon", "Venus"] },
      { house: 1, weight: 0.18, karakas: ["Moon"] },
      { house: 7, weight: 0.16, karakas: ["Venus", "Moon"] },
    ],
    planets: [{ name: "Moon", weight: 0.22 }, { name: "Venus", weight: 0.12 }],
    vargas: [{ chart: "D9", houses: [4, 7], karakas: ["Moon", "Venus"], weight: 0.16 }],
    checked: ["D1 4H emotions", "D1 Lagna nature", "D1 7H bonding", "Moon/Venus", "D9 emotional validation"],
    rules: ["Emotional category is not judged from breakup/marriage promise.", "Moon is the main karaka; Venus is secondary.", "D9 validates bonding sensitivity only."],
  });
  const strategicThinker = cleanCategoryResult({
    kundli,
    d1: [
      { house: 5, weight: 0.34, karakas: ["Mercury", "Jupiter"] },
      { house: 9, weight: 0.18, karakas: ["Jupiter"] },
      { house: 3, weight: 0.10, karakas: ["Mercury"] },
    ],
    planets: [{ name: "Mercury", weight: 0.20 }, { name: "Jupiter", weight: 0.12 }],
    vargas: [{ chart: "D24", houses: [1, 5, 9], karakas: ["Mercury", "Jupiter"], weight: 0.20 }],
    checked: ["D1 5H intelligence", "D1 9H wisdom", "D1 3H skill", "Mercury/Jupiter", "D24 education/learning"],
    rules: ["5H is primary for intelligence.", "Mercury handles strategy; Jupiter handles wisdom.", "D24 validates learning depth."],
  });
  const spiritualSeeker = cleanCategoryResult({
    kundli,
    d1: [
      { house: 9, weight: 0.26, karakas: ["Jupiter", "Ketu"] },
      { house: 12, weight: 0.30, karakas: ["Ketu", "Jupiter"] },
      { house: 4, weight: 0.10, karakas: ["Moon"] },
    ],
    planets: [{ name: "Jupiter", weight: 0.14 }, { name: "Ketu", weight: 0.10 }],
    vargas: [{ chart: "D20", houses: [1, 9, 12], karakas: ["Jupiter", "Ketu"], weight: 0.24 }],
    checked: ["D1 9H dharma", "D1 12H moksha", "D1 4H inner peace", "Jupiter/Ketu", "D20 spiritual validation"],
    rules: ["Spiritual category needs 9H/12H support.", "D20 is the main divisional validation.", "Ketu is treated as neutral dignity but important as spiritual karaka."],
  });
  const survivorMindset = cleanCategoryResult({
    kundli,
    d1: [
      { house: 3, weight: 0.24, karakas: ["Mars", "Saturn"] },
      { house: 6, weight: 0.26, karakas: ["Mars", "Saturn"] },
      { house: 8, weight: 0.14, karakas: ["Saturn", "Ketu"] },
    ],
    planets: [{ name: "Mars", weight: 0.16 }, { name: "Saturn", weight: 0.16 }],
    vargas: [
      { chart: "D27", houses: [1, 3, 6], karakas: ["Mars", "Saturn"], weight: 0.12 },
      { chart: "D30", houses: [6, 8], karakas: ["Mars", "Saturn", "Ketu"], weight: 0.10 },
    ],
    checked: ["D1 3H courage", "D1 6H fight capacity", "D1 8H crisis handling", "Mars/Saturn", "D27/D30 resilience"],
    rules: ["This category means pressure-handling, not suffering prediction.", "3H and 6H are primary.", "D27/D30 validate resilience only."],
  });
  const moneyBuilder = wealthBuilderResult(kundli, valueOf, wealthBase);
  const creativeMind = cleanCategoryResult({
    kundli,
    d1: [
      { house: 5, weight: 0.32, karakas: ["Venus", "Mercury", "Moon"] },
      { house: 3, weight: 0.20, karakas: ["Mercury", "Venus"] },
      { house: 2, weight: 0.10, karakas: ["Mercury", "Venus"] },
    ],
    planets: [{ name: "Venus", weight: 0.18 }, { name: "Mercury", weight: 0.14 }, { name: "Moon", weight: 0.08 }],
    vargas: [
      { chart: "D3", houses: [3], karakas: ["Mercury", "Venus"], weight: 0.10 },
      { chart: "D10", houses: [10], karakas: ["Venus", "Mercury"], weight: 0.08 },
    ],
    checked: ["D1 5H creativity", "D1 3H expression", "D1 2H voice/style", "Venus/Mercury/Moon", "D3/D10 expression validation"],
    rules: ["5H is primary for creativity.", "3H/2H show expression and voice.", "D3 and D10 validate skill output, not fame guarantee."],
  });
  const magneticPresence = cleanCategoryResult({
    kundli,
    d1: [
      { house: 1, weight: 0.34, karakas: ["Venus", "Moon"] },
      { house: 7, weight: 0.18, karakas: ["Venus", "Moon"] },
      { house: 2, weight: 0.10, karakas: ["Venus", "Mercury"] },
    ],
    planets: [{ name: "Venus", weight: 0.24 }, { name: "Moon", weight: 0.14 }],
    vargas: [{ chart: "D9", houses: [1, 7], karakas: ["Venus", "Moon"], weight: 0.16 }],
    checked: ["D1 Lagna aura", "D1 7H public response", "D1 2H speech/face", "Venus/Moon", "D9 presence validation"],
    rules: ["This category means presence/aura, not beauty ranking.", "Lagna and Venus are primary.", "D9 validates interpersonal magnetism."],
  });
  const matureMind = cleanCategoryResult({
    kundli,
    d1: [
      { house: 5, weight: 0.22, karakas: ["Jupiter", "Mercury"] },
      { house: 8, weight: 0.18, karakas: ["Saturn", "Jupiter"] },
      { house: 9, weight: 0.18, karakas: ["Jupiter", "Saturn"] },
      { house: 4, weight: 0.10, karakas: ["Moon"] },
    ],
    planets: [{ name: "Saturn", weight: 0.16 }, { name: "Jupiter", weight: 0.14 }, { name: "Mercury", weight: 0.08 }, { name: "Moon", weight: 0.06 }],
    vargas: [{ chart: "D9", houses: [1, 9], karakas: ["Saturn", "Jupiter"], weight: 0.12 }],
    checked: ["D1 5H judgement", "D1 8H life-depth", "D1 9H wisdom", "D1 4H mental steadiness", "Saturn/Jupiter/Mercury/Moon", "D9 maturity validation"],
    rules: ["Mature Mind is judged from patience, judgement and depth.", "8H is used for life-depth, not fear content.", "D9 validates inner maturity only."],
  });
  const options = [
    {
      type: "Powerful Kundli → Natural Leader",
      kind: "career" as const,
      score: naturalLeader.score,
      line: "Strict read: Natural Leader uses D1 Lagna/10H/3H, Sun-Mars drive and D10 authority validation.",
      why: ["D1 Lagna/10H/3H", "Sun-Mars drive", "D10 authority validation"],
      checked: naturalLeader.checked,
      rules: naturalLeader.rules,
      details: naturalLeader.details,
    },
    {
      type: "Emotional Kundli → Emotional Soul",
      kind: "relationship" as const,
      score: emotionalSoul.score,
      line: "Strict read: Emotional Soul uses Moon, D1 4H/7H and D9 emotional-bond validation.",
      why: ["Moon strength", "D1 4H/7H", "D9 emotional validation"],
      checked: emotionalSoul.checked,
      rules: emotionalSoul.rules,
      details: emotionalSoul.details,
    },
    {
      type: "Intelligent Kundli → Strategic Thinker",
      kind: "intelligence" as const,
      score: strategicThinker.score,
      line: "Strict read: Strategic Thinker uses D1 5H/9H, Mercury-Jupiter and D24 learning validation.",
      why: ["D1 5H/9H", "Mercury-Jupiter", "D24 learning validation"],
      checked: strategicThinker.checked,
      rules: strategicThinker.rules,
      details: strategicThinker.details,
    },
    {
      type: "Spiritual Kundli → Spiritual Seeker",
      kind: "spiritual" as const,
      score: spiritualSeeker.score,
      line: "Strict read: Spiritual Seeker uses D1 9H/12H, Jupiter-Ketu and D20 sadhana validation.",
      why: ["D1 9H/12H", "Jupiter-Ketu", "D20 validation"],
      checked: spiritualSeeker.checked,
      rules: spiritualSeeker.rules,
      details: spiritualSeeker.details,
    },
    {
      type: "Fighter Kundli → Survivor Mindset",
      kind: "fighter" as const,
      score: survivorMindset.score,
      line: "Strict read: Survivor Mindset uses D1 3H/6H/8H, Mars-Saturn and D27/D30 resilience validation.",
      why: ["D1 3H/6H/8H", "Mars-Saturn", "D27/D30 resilience"],
      checked: survivorMindset.checked,
      rules: survivorMindset.rules,
      details: survivorMindset.details,
    },
    {
      type: "Wealth Builder Kundli → Money Builder",
      kind: "wealth" as const,
      score: moneyBuilder.score,
      line: "Strict read: Money Builder prioritizes D1 wealth promise, D2 capacity and D10 income engine; current dasha is shown as timing-only operational score.",
      why: ["Current dasha timing", "D1 wealth promise", "D2 vault + D10 income", "D9/SAV + leakage filter"],
      checked: moneyBuilder.checked,
      rules: moneyBuilder.rules,
      details: moneyBuilder.details,
    },
    {
      type: "Creative Kundli → Creative Mind",
      kind: "intelligence" as const,
      score: creativeMind.score,
      line: "Strict read: Creative Mind uses D1 5H/3H/2H, Venus-Mercury-Moon and D3/D10 expression validation.",
      why: ["D1 5H/3H/2H", "Venus-Mercury-Moon", "D3/D10 validation"],
      checked: creativeMind.checked,
      rules: creativeMind.rules,
      details: creativeMind.details,
    },
    {
      type: "Attractive Kundli → Magnetic Presence",
      kind: "relationship" as const,
      score: magneticPresence.score,
      line: "Strict read: Magnetic Presence uses D1 Lagna/7H, Venus-Moon and D9 presence validation.",
      why: ["D1 Lagna/7H", "Venus-Moon", "D9 presence validation"],
      checked: magneticPresence.checked,
      rules: magneticPresence.rules,
      details: magneticPresence.details,
    },
    {
      type: "Wise Kundli → Mature Mind",
      kind: "identity" as const,
      score: matureMind.score,
      line: "Strict read: Mature Mind uses D1 5H/8H/9H/4H, Saturn-Jupiter-Mercury-Moon and D9 maturity validation.",
      why: ["D1 5H/8H/9H/4H", "Saturn-Jupiter-Mercury-Moon", "D9 validation"],
      checked: matureMind.checked,
      rules: matureMind.rules,
      details: matureMind.details,
    },
  ].map(opt => ({ ...opt, score: Math.max(8, Math.min(96, Math.round(opt.score))) }));

  return {
    coreIdentity,
    atmakaraka: ak?.name,
    options: options.sort((a, b) => b.score - a.score),
  };
}

export function buildPersonalSnapshot(kundli: KundliData | null | undefined, _lang: UILang): PersonalSnapshot {
  if (!kundli) {
    return {
      title: "Personalization",
      themeLabel: "Kundli locked",
      powerType: "Kundli Power Locked",
      powerScore: null,
      powerLine: "Create your kundli to see the main power signature of your chart.",
      innerType: "Create Kundli",
      innerTypeSub: "Your 12-house personalization will appear after birth chart creation.",
      identityLine: "Create your kundli to reveal your full life operating system.",
      strongestTrait: "Locked",
      pressurePoint: "Create Kundli",
      hiddenStrength: "Your hidden strengths will unlock from house and planet analysis.",
      pressureTrigger: "Your pressure areas will appear here.",
      todayTip: "Create kundli to see your first personal tip.",
      bestMode: "Personal mode locked",
      trustLine: "This engine uses house lords, dignity, aspects, friend/enemy signs and varga support.",
      bullets: ["No generic zodiac text. This reads the structure of your saved kundli."],
      insights: [{ key: "locked", label: "YOU", title: "Locked", sub: "Create kundli first", value: null, tag: "Locked", line: "Create kundli to unlock." }],
      categoryScores: [],
      color: "#a78bfa",
      darkGrad: ["#241044", "#3b1570"],
      lightGrad: ["#f5f0ff", "#ede0fe"],
    };
  }

  const insights = DIMS.map(dim => scoreDimension(kundli, dim));
  const valueOf = (key: string): number => insights.find(item => item.key === key)?.value ?? 50;
  const wealthBase = cleanHouseScore(kundli, 2, ["Jupiter", "Venus", "Mercury"]);
  const strictPower = buildStrictPowerOptions(kundli, valueOf, wealthBase);
  const powerOptions = strictPower.options;
  const power = powerOptions[0];
  const runnerUp = powerOptions[1];
  const confidence = Math.max(58, Math.min(94, Math.round(62 + (power.score - (runnerUp?.score ?? 50)) * 1.4)));
  const categoryScores = powerOptions.map(option => ({
    type: option.type,
    score: option.score,
    selected: option.type === power.type,
    reasons: option.why,
    line: option.line,
    checked: option.checked,
    rules: option.rules,
    details: option.details,
  }));
  const strongest = insights.reduce((best, item) => (item.value ?? 0) > (best.value ?? 0) ? item : best);
  const weakest = insights.reduce((worst, item) => (item.value ?? 100) < (worst.value ?? 100) ? item : worst);
  const strongestLifeTheme = strongest.key === "spiritual" ? "Spiritual Seeker"
    : strongest.key === "career" ? "Karma Builder"
      : strongest.key === "knowledge" ? "Gyan-Oriented"
        : strongest.key === "relationship" ? "Relationship Mirror"
          : strongest.key === "effort" ? "Effort Warrior"
            : "Life Pattern Reader";
  const categoryTheme = power.type.includes("→")
    ? power.type.split("→").pop()?.trim() || power.type
    : power.type.replace(/\s+Kundli$/, "");

  const color = strongest.key === "career" ? "#3b82f6"
    : strongest.key === "spiritual" ? "#a78bfa"
      : strongest.key === "knowledge" ? "#f59e0b"
        : strongest.key === "relationship" ? "#ec4899"
          : "#10b981";

  return {
    title: "Personalization",
    themeLabel: `${categoryTheme} · strict category engine`,
    powerType: power.type,
    powerScore: power.score,
    powerLine: `${power.line} Confidence ${confidence}%.`,
    innerType: categoryTheme,
    innerTypeSub: `Your selected category is ${power.type}. Strongest life area: ${strongest.key}. Awareness area: ${weakest.key}.`,
    identityLine: `Your kundli category is ${power.type}; within it, ${strongest.key} is your strongest life pattern and ${weakest.key} needs awareness.`,
    strongestTrait: `${strongest.key.toUpperCase()} · ${strongest.tag}`,
    pressurePoint: `${weakest.key.toUpperCase()} · ${weakest.tag}`,
    hiddenStrength: strongest.support ?? strongest.line,
    pressureTrigger: weakest.caution ?? weakest.line,
    todayTip: `Use your ${strongest.key} strength, but do not ignore ${weakest.key} signals.`,
    bestMode: strongest.key === "career" ? "Build and execute"
      : strongest.key === "spiritual" ? "Reflect and detach"
        : strongest.key === "relationship" ? "Connect and listen"
          : strongest.key === "knowledge" ? "Learn and teach"
            : "Act with awareness",
    trustLine: "Strict lifetime engine: Lagna/Lagna lord, Moon, Sun, Atmakaraka, functional house lords, dignity, debility correction, combustion, retrograde, Ashtakavarga, benefic/malefic aspects and D9/D10/D20 validation.",
    bullets: [
      `${power.type} selected by: ${power.why.join(" · ")}.`,
      `Core identity score: ${strictPower.coreIdentity}%${strictPower.atmakaraka ? ` · Atmakaraka: ${strictPower.atmakaraka}` : ""}.`,
      runnerUp ? `Runner-up pattern: ${runnerUp.type} (${runnerUp.score}%).` : `${strongest.title} is your strongest readable pattern.`,
      `Strongest life theme: ${strongestLifeTheme}. ${weakest.title} needs awareness because the chart shows weaker support there.`,
    ],
    insights,
    categoryScores,
    color,
    darkGrad: ["#111827", "#312e81"],
    lightGrad: ["#eef2ff", "#e0e7ff"],
  };
}
