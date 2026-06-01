export const SIGNS = [
  "Mesh (Aries)", "Vrishabh (Taurus)", "Mithun (Gemini)", "Kark (Cancer)",
  "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchik (Scorpio)",
  "Dhanu (Sagittarius)", "Makar (Capricorn)", "Kumbh (Aquarius)", "Meen (Pisces)",
];

export const SIGNS_SHORT = [
  "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
  "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
];

export const EN_SIGN_TO_SHORT: Record<string, string> = {
  Aries: "Mesh", Taurus: "Vrishabh", Gemini: "Mithun", Cancer: "Kark",
  Leo: "Simha", Virgo: "Kanya", Libra: "Tula", Scorpio: "Vrishchik",
  Sagittarius: "Dhanu", Capricorn: "Makar", Aquarius: "Kumbh", Pisces: "Meen",
};

const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
  "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
  "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
  "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
];

const NAK_LORDS = [
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
];

const EXALT: Record<string, { sign: string; deg: number }> = {
  Sun: { sign: "Mesh", deg: 10 }, Moon: { sign: "Vrishabh", deg: 3 }, Mars: { sign: "Makar", deg: 28 },
  Mercury: { sign: "Kanya", deg: 15 }, Jupiter: { sign: "Kark", deg: 5 }, Venus: { sign: "Meen", deg: 27 },
  Saturn: { sign: "Tula", deg: 20 }, Rahu: { sign: "Vrishabh", deg: 20 }, Ketu: { sign: "Vrishchik", deg: 20 },
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

export const KARAKA: Record<string, string[]> = {
  Sun: ["Atma", "Pita", "Satta", "Tej", "Hriday"],
  Moon: ["Mann", "Mata", "Bhaavna", "Jal", "Rakta"],
  Mars: ["Sahas", "Bhratra", "Bhoomi", "Urja", "Kshatra"],
  Mercury: ["Buddhi", "Vaani", "Vyaapaar", "Tvacha", "Yukti"],
  Jupiter: ["Gyaan", "Santan", "Dharma", "Dhan", "Guru"],
  Venus: ["Prem", "Patni", "Kala", "Vaibhav", "Kidney"],
  Saturn: ["Karma", "Anushasan", "Ayu", "Seva", "Daant"],
  Rahu: ["Videsh", "Tantra", "Maya", "Achank", "Obsession"],
  Ketu: ["Adhyatm", "Moksha", "Poorvajanm", "Ekant", "Gyan"],
};

export const PLANET_CLR: Record<string, string> = {
  Sun: "#f59e0b", Moon: "#94a3b8", Mars: "#ef4444", Mercury: "#10b981",
  Jupiter: "#facc15", Venus: "#ec4899", Saturn: "#a78bfa",
  Rahu: "#f59e0b", Ketu: "#fb923c",
};

export const PLANET_GLYPH: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mars: "♂", Mercury: "☿", Jupiter: "♃",
  Venus: "♀", Saturn: "♄", Rahu: "☊", Ketu: "☋",
};

export type PlanetCardData = {
  name: string;
  sign: string;
  house: number;
  longitude: number;
  retrograde?: boolean;
  speed?: number;
};

export function enSignToShort(sign: string): string {
  return EN_SIGN_TO_SHORT[sign] ?? sign;
}

export function nakshatra(lon: number) {
  const size = 360 / 27;
  const idx = Math.floor(lon / size) % 27;
  const pada = Math.floor((lon % size) / (size / 4)) + 1;
  return { name: NAKSHATRAS[idx], pada, lord: NAK_LORDS[idx] };
}

export function signStatusFromSign(planet: string, signShort: string): { label: string; color: string } {
  if (EXALT[planet]?.sign === signShort) return { label: "Uchch (Exalted)", color: "#4ade80" };
  if (DEBIL[planet] === signShort) return { label: "Neech (Debilitated)", color: "#ef4444" };
  if (OWN[planet]?.includes(signShort)) return { label: "Svagriha (Own)", color: "#f59e0b" };
  return { label: "Saamaanya (Normal)", color: "#3d5a7a" };
}

export function signStatus(planet: string, lon: number): { label: string; color: string } {
  const sign = SIGNS_SHORT[Math.floor(lon / 30) % 12];
  return signStatusFromSign(planet, sign);
}

export function houseCategory(h: number): { label: string; color: string } {
  if ([1, 4, 7, 10].includes(h)) return { label: "Kendra", color: "#4ade80" };
  if ([5, 9].includes(h)) return { label: "Trikona", color: "#f59e0b" };
  if ([6, 8, 12].includes(h)) return { label: "Dusthana", color: "#ef4444" };
  return { label: "Madhyam", color: "#fbbf24" };
}

export function angDist(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

export function degreeInSign(lon: number): string {
  const deg = ((lon % 30) + 30) % 30;
  return `${deg.toFixed(1)}°`;
}
