/**
 * PLANET-STRENGTH RULE (engine / openai_helper Rule K extension).
 * D1 dignity alone is insufficient — cross-check with D9 before strong/weak verdict.
 */

import type { KundliData, PlanetInfo } from "@/types";

export type DignityTier = "exalted" | "debilitated" | "own" | "neutral";

const SIGNS_SHORT = [
  "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
  "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
];
const EXACT_DEGREE_ORB = 1;

const EN_SIGN_TO_SHORT: Record<string, string> = {
  Aries: "Mesh",
  Taurus: "Vrishabh",
  Gemini: "Mithun",
  Cancer: "Kark",
  Leo: "Simha",
  Virgo: "Kanya",
  Libra: "Tula",
  Scorpio: "Vrishchik",
  Sagittarius: "Dhanu",
  Capricorn: "Makar",
  Aquarius: "Kumbh",
  Pisces: "Meen",
};

const EXALT: Record<string, string> = {
  Sun: "Mesh", Moon: "Vrishabh", Mars: "Makar", Mercury: "Kanya",
  Jupiter: "Kark", Venus: "Meen", Saturn: "Tula", Rahu: "Vrishabh", Ketu: "Vrishchik",
};
const DEBIL: Record<string, string> = {
  Sun: "Tula", Moon: "Vrishchik", Mars: "Kark", Mercury: "Meen",
  Jupiter: "Makar", Venus: "Kanya", Saturn: "Mesh", Rahu: "Vrishchik", Ketu: "Vrishabh",
};
const OWN: Record<string, string[]> = {
  Sun: ["Simha"], Moon: ["Kark"], Mars: ["Mesh", "Vrishchik"],
  Mercury: ["Mithun", "Kanya"], Jupiter: ["Dhanu", "Meen"],
  Venus: ["Vrishabh", "Tula"], Saturn: ["Makar", "Kumbh"],
};
const EXALT_DEGREE: Record<string, number> = {
  Sun: 10, Moon: 3, Mars: 28, Mercury: 15, Jupiter: 5,
  Venus: 27, Saturn: 20, Rahu: 20, Ketu: 20,
};
const MOOLTRIKONA: Record<string, { sign: string; from: number; to: number }> = {
  Sun: { sign: "Simha", from: 0, to: 20 },
  Moon: { sign: "Vrishabh", from: 4, to: 30 },
  Mars: { sign: "Mesh", from: 0, to: 12 },
  Mercury: { sign: "Kanya", from: 16, to: 20 },
  Jupiter: { sign: "Dhanu", from: 0, to: 10 },
  Venus: { sign: "Tula", from: 0, to: 15 },
  Saturn: { sign: "Kumbh", from: 0, to: 20 },
};
const SIGN_LORDS: Record<string, string> = {
  Mesh: "Mars",
  Vrishabh: "Venus",
  Mithun: "Mercury",
  Kark: "Moon",
  Simha: "Sun",
  Kanya: "Mercury",
  Tula: "Venus",
  Vrishchik: "Mars",
  Dhanu: "Jupiter",
  Makar: "Saturn",
  Kumbh: "Saturn",
  Meen: "Jupiter",
};
const EXALTED_IN_SIGN: Record<string, string> = Object.fromEntries(
  Object.entries(EXALT).map(([planet, sign]) => [sign, planet]),
);

export function signShortFromIndex(index: number): string {
  return SIGNS_SHORT[((index % 12) + 12) % 12];
}

export function dignityTier(planet: string, signShort: string): DignityTier {
  const sign = normalizeSign(signShort) ?? signShort;
  if (EXALT[planet] === sign) return "exalted";
  if (DEBIL[planet] === sign) return "debilitated";
  if (OWN[planet]?.includes(sign)) return "own";
  return "neutral";
}

function isStrongTier(t: DignityTier): boolean {
  return t === "exalted" || t === "own";
}

function isWeakTier(t: DignityTier): boolean {
  return t === "debilitated";
}

export type StrengthVerdict = {
  label: string;
  shortLabel: string;
  color: string;
  code: "vargottama" | "strong" | "neech_bhanga" | "mixed" | "weak" | "neutral";
};

export type NeechaBhangaResult = {
  isDebilitated: boolean;
  applies: boolean;
  reasons: string[];
};

function normalizeSign(sign?: string): string | undefined {
  if (!sign) return undefined;
  if (SIGNS_SHORT.includes(sign)) return sign;
  return EN_SIGN_TO_SHORT[sign] ?? sign;
}

function normalizedLongitude(lon: number): number {
  return ((lon % 360) + 360) % 360;
}

function signFromLongitude(lon: number): string {
  return signShortFromIndex(Math.floor(normalizedLongitude(lon) / 30));
}

function degreeInSign(lon: number | undefined): number | undefined {
  if (typeof lon !== "number" || Number.isNaN(lon)) return undefined;
  return normalizedLongitude(lon) % 30;
}

function isWithinDegreeOrb(a: number, b: number): boolean {
  return Math.abs(a - b) <= EXACT_DEGREE_ORB;
}

function dignityVerdict(planet: string, signShort: string, longitude?: number): StrengthVerdict {
  const sign = normalizeSign(signShort) ?? signShort;
  const deg = degreeInSign(longitude);
  const tier = dignityTier(planet, sign);

  if (deg != null && tier === "exalted" && isWithinDegreeOrb(deg, EXALT_DEGREE[planet])) {
    return { label: `Deep Uchch (exact exaltation near ${EXALT_DEGREE[planet]}°)`, shortLabel: "Deep Uchch", color: "#22c55e", code: "strong" };
  }
  if (deg != null && tier === "debilitated" && isWithinDegreeOrb(deg, EXALT_DEGREE[planet])) {
    return { label: `Deep Neech (exact debility near ${EXALT_DEGREE[planet]}°)`, shortLabel: "Deep Neech", color: "#dc2626", code: "weak" };
  }

  const mool = MOOLTRIKONA[planet];
  if (mool && sign === mool.sign && deg != null && deg >= mool.from && deg < mool.to) {
    return { label: `Mooltrikona (${mool.from}°-${mool.to}° ${sign})`, shortLabel: "Mooltrikona", color: "#84cc16", code: "strong" };
  }

  return singleChartVerdict(tier);
}

function getPlanet(kundli: KundliData, name: string): PlanetInfo | undefined {
  return kundli.planets?.find(p => p.name === name);
}

function planetSign(kundli: KundliData, planet: string): string | undefined {
  const p = getPlanet(kundli, planet);
  if (!p) return undefined;
  if (typeof p.rashiIndex === "number") return SIGNS_SHORT[((p.rashiIndex % 12) + 12) % 12];
  if (typeof p.longitude === "number" && !Number.isNaN(p.longitude)) return signFromLongitude(p.longitude);
  return normalizeSign(p.sign ?? p.rashi);
}

function lagnaSign(kundli: KundliData): string | undefined {
  if (typeof kundli.ascendantDeg === "number" && !Number.isNaN(kundli.ascendantDeg)) {
    return signFromLongitude(kundli.ascendantDeg);
  }
  return normalizeSign(kundli.ascendant);
}

function isKendraFrom(sign: string | undefined, ref: string | undefined): boolean {
  if (!sign || !ref) return false;
  const signIdx = SIGNS_SHORT.indexOf(sign);
  const refIdx = SIGNS_SHORT.indexOf(ref);
  if (signIdx < 0 || refIdx < 0) return false;
  return [0, 3, 6, 9].includes((signIdx - refIdx + 12) % 12);
}

function inKendraFromLagnaOrMoon(kundli: KundliData, sign: string | undefined): boolean {
  return isKendraFrom(sign, lagnaSign(kundli)) || isKendraFrom(sign, planetSign(kundli, "Moon"));
}

function aspectsSign(fromPlanet: string, fromSign: string | undefined, targetSign: string): boolean {
  if (!fromSign) return false;
  const fromIdx = SIGNS_SHORT.indexOf(fromSign);
  const targetIdx = SIGNS_SHORT.indexOf(targetSign);
  if (fromIdx < 0 || targetIdx < 0) return false;
  const d = (targetIdx - fromIdx + 12) % 12;
  return d === 6 ||
    (fromPlanet === "Mars" && (d === 3 || d === 7)) ||
    (fromPlanet === "Jupiter" && (d === 4 || d === 8)) ||
    (fromPlanet === "Saturn" && (d === 2 || d === 9)) ||
    ((fromPlanet === "Rahu" || fromPlanet === "Ketu") && (d === 4 || d === 8));
}

export function evaluateNeechaBhanga(
  kundli: KundliData | null | undefined,
  planet: string,
  d1Sign: string | undefined,
): NeechaBhangaResult {
  const sign = normalizeSign(d1Sign);
  if (!sign || DEBIL[planet] !== sign) {
    return { isDebilitated: false, applies: false, reasons: [] };
  }
  if (!kundli) {
    return { isDebilitated: true, applies: false, reasons: [] };
  }

  const reasons: string[] = [];
  const debilSignLord = SIGN_LORDS[sign];
  const debilSignLordSign = planetSign(kundli, debilSignLord);
  const planetExaltedInDebilSign = EXALTED_IN_SIGN[sign];
  const exaltedPlanetSign = planetExaltedInDebilSign ? planetSign(kundli, planetExaltedInDebilSign) : undefined;

  if (inKendraFromLagnaOrMoon(kundli, debilSignLordSign)) {
    reasons.push(`${debilSignLord} (neecha rashi lord) in kendra from Lagna/Moon`);
  }

  if (planetExaltedInDebilSign && inKendraFromLagnaOrMoon(kundli, exaltedPlanetSign)) {
    reasons.push(`${planetExaltedInDebilSign} (exalted in ${sign}) in kendra from Lagna/Moon`);
  }

  if (dignityTier(debilSignLord, debilSignLordSign ?? "") === "exalted") {
    reasons.push(`${debilSignLord} dispositor exalted`);
  }

  const exaltationSignLord = SIGN_LORDS[EXALT[planet]];
  if (exaltationSignLord && aspectsSign(exaltationSignLord, planetSign(kundli, exaltationSignLord), sign)) {
    reasons.push(`${exaltationSignLord} (exaltation-sign lord) aspects the debilitated planet`);
  }

  return { isDebilitated: true, applies: reasons.length > 0, reasons };
}

/** Combined D1 + D9 verdict per engine rule. */
export function combinedPlanetStrength(
  planet: string,
  d1Sign: string,
  d9Sign: string | undefined,
  neechaBhanga?: NeechaBhangaResult,
  d1Longitude?: number,
): StrengthVerdict {
  const normalizedD1Sign = normalizeSign(d1Sign) ?? d1Sign;
  const normalizedD9Sign = d9Sign ? normalizeSign(d9Sign) ?? d9Sign : undefined;
  const d1 = dignityTier(planet, normalizedD1Sign);
  const d1Verdict = dignityVerdict(planet, normalizedD1Sign, d1Longitude);
  if (!d9Sign) {
    if (isWeakTier(d1) && neechaBhanga?.applies) {
      return {
        label: `Classical Neech Bhanga — ${neechaBhanga.reasons[0]}`,
        shortLabel: "Neech Bhanga",
        color: "#38bdf8",
        code: "neech_bhanga",
      };
    }
    return d1Verdict;
  }

  const d9 = dignityTier(planet, normalizedD9Sign ?? "");
  const varg = normalizedD1Sign.trim().toLowerCase() === (normalizedD9Sign ?? "").trim().toLowerCase();

  if (isWeakTier(d1) && neechaBhanga?.applies) {
    return {
      label: `Classical Neech Bhanga — ${neechaBhanga.reasons[0]}`,
      shortLabel: "Neech Bhanga",
      color: "#38bdf8",
      code: "neech_bhanga",
    };
  }
  if (d1Verdict.shortLabel === "Mooltrikona" && !isWeakTier(d9)) {
    return {
      label: varg
        ? "Mooltrikona Vargottama — D1 mooltrikona, D9 same rashi"
        : "Mooltrikona — D1 mooltrikona; D9 not weak",
      shortLabel: "Mooltrikona",
      color: d1Verdict.color,
      code: "strong",
    };
  }
  if (d1 === "exalted" && !isWeakTier(d9)) {
    return {
      label: d1Verdict.shortLabel === "Deep Uchch"
        ? (varg ? "Deep Uchch Vargottama — D1 exact exaltation, D9 same rashi" : "Deep Uchch — D1 exact exaltation; D9 not weak")
        : varg
        ? "Uchch Vargottama — D1 exalted, D9 same rashi"
        : "Uchch — D1 exalted; D9 not weak",
      shortLabel: d1Verdict.shortLabel === "Deep Uchch" ? "Deep Uchch" : "Uchch",
      color: d1Verdict.shortLabel === "Deep Uchch" ? d1Verdict.color : "#4ade80",
      code: "strong",
    };
  }
  if (varg) {
    if (isWeakTier(d1)) {
      return {
        label: "Neecha vargottama — D1 & D9 same debilitated rashi",
        shortLabel: "Neech",
        color: "#ef4444",
        code: "weak",
      };
    }
    return {
      label: "Vargottama — D1 & D9 same rashi (strong)",
      shortLabel: "Vargottama",
      color: "#f59e0b",
      code: "vargottama",
    };
  }
  if (isStrongTier(d1) && isStrongTier(d9)) {
    return {
      label: "Truly strong — D1 & D9 both supportive",
      shortLabel: "Balwan",
      color: "#4ade80",
      code: "strong",
    };
  }
  if (isWeakTier(d1) && isStrongTier(d9)) {
    return {
      label: "D9 support — D1 neecha, D9 strong; no classical bhanga found",
      shortLabel: "D9 Support",
      color: "#fb923c",
      code: "mixed",
    };
  }
  if (isStrongTier(d1) && isWeakTier(d9)) {
    return {
      label: "Mixed — D1 ok, D9 weak (fragile in life)",
      shortLabel: "Mixed",
      color: "#fb923c",
      code: "mixed",
    };
  }
  if (isWeakTier(d1) && isWeakTier(d9)) {
    return {
      label: "Truly weak — D1 & D9 both weak",
      shortLabel: "Kamzor",
      color: "#ef4444",
      code: "weak",
    };
  }
  if (isWeakTier(d1)) {
    return {
      label: "Weak — D1 neecha, no classical bhanga found",
      shortLabel: "Kamzor",
      color: "#ef4444",
      code: "weak",
    };
  }
  return {
    label: "Average — check houses & dasha",
    shortLabel: "Saamaanya",
    color: "#94a3b8",
    code: "neutral",
  };
}

function singleChartVerdict(t: DignityTier): StrengthVerdict {
  if (t === "exalted") {
    return { label: "Uchch (exalted)", shortLabel: "Uchch", color: "#4ade80", code: "strong" };
  }
  if (t === "debilitated") {
    return { label: "Neech (debilitated)", shortLabel: "Neech", color: "#ef4444", code: "weak" };
  }
  if (t === "own") {
    return { label: "Svagriha (own sign)", shortLabel: "Svagriha", color: "#f59e0b", code: "strong" };
  }
  return { label: "Saamaanya (normal)", shortLabel: "Saamaanya", color: "#64748b", code: "neutral" };
}

/** Single-chart badge (D1-only tab fallback). */
export function chartDignityLabel(planet: string, signShort: string, longitude?: number): StrengthVerdict {
  return dignityVerdict(planet, signShort, longitude);
}
