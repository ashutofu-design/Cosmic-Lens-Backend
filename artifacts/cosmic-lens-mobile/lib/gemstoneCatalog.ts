import type { DayKey, PlanetKey } from "@/lib/i18nVedic";

export type GemstoneCatalogKey =
  | "ruby"
  | "pearl"
  | "coral"
  | "emerald"
  | "yellowsapphire"
  | "diamond"
  | "bluesapphire"
  | "hessonite"
  | "catseye";

type Localized = { en: string; hn: string; hi: string };

export type GemstoneCatalogEntry = {
  id: GemstoneCatalogKey;
  planetKey: PlanetKey;
  planetEmoji: string;
  gemstoneKey: GemstoneCatalogKey;
  accent: string;
  gradient: [string, string];
  day: DayKey;
  finger: Localized;
  metal: Localized;
  weight: string;
  benefit: Localized;
};

export const GEMSTONE_CATALOG: GemstoneCatalogEntry[] = [
  {
    id: "ruby",
    planetKey: "surya",
    planetEmoji: "☀️",
    gemstoneKey: "ruby",
    accent: "#ef4444",
    gradient: ["#7f1d1d", "#ef4444"],
    day: "sun",
    finger: { en: "Ring finger", hn: "Angoothi wali ungli", hi: "अनामिका" },
    metal: { en: "Gold", hn: "Sona", hi: "सोना" },
    weight: "3–5 ct",
    benefit: {
      en: "Confidence, authority & vitality",
      hn: "Aatmvishwas, pad aur urja",
      hi: "आत्मविश्वास, पद और ऊर्जा",
    },
  },
  {
    id: "pearl",
    planetKey: "chandra",
    planetEmoji: "🌙",
    gemstoneKey: "pearl",
    accent: "#e2e8f0",
    gradient: ["#334155", "#cbd5e1"],
    day: "mon",
    finger: { en: "Little finger", hn: "Chhoti ungli", hi: "कनिष्ठा" },
    metal: { en: "Silver", hn: "Chandi", hi: "चाँदी" },
    weight: "4–7 ct",
    benefit: {
      en: "Emotional calm & mental peace",
      hn: "Mann ki shanti aur sukoon",
      hi: "मानसिक शांति और सुकून",
    },
  },
  {
    id: "coral",
    planetKey: "mangal",
    planetEmoji: "🔴",
    gemstoneKey: "coral",
    accent: "#f87171",
    gradient: ["#7f1d1d", "#fb7185"],
    day: "tue",
    finger: { en: "Ring finger", hn: "Angoothi wali ungli", hi: "अनामिका" },
    metal: { en: "Gold / Copper", hn: "Sona / Tamba", hi: "सोना / ताँबा" },
    weight: "5–9 ct",
    benefit: {
      en: "Courage, energy & property gains",
      hn: "Himmat, urja aur sampatti",
      hi: "साहस, ऊर्जा और संपत्ति",
    },
  },
  {
    id: "emerald",
    planetKey: "budh",
    planetEmoji: "💚",
    gemstoneKey: "emerald",
    accent: "#34d399",
    gradient: ["#064e3b", "#34d399"],
    day: "wed",
    finger: { en: "Little finger", hn: "Chhoti ungli", hi: "कनिष्ठा" },
    metal: { en: "Gold / Silver", hn: "Sona / Chandi", hi: "सोना / चाँदी" },
    weight: "3–6 ct",
    benefit: {
      en: "Speech, business & intellect",
      hn: "Vaani, vyapar aur buddhi",
      hi: "वाणी, व्यापार और बुद्धि",
    },
  },
  {
    id: "yellowsapphire",
    planetKey: "guru",
    planetEmoji: "🟡",
    gemstoneKey: "yellowsapphire",
    accent: "#fbbf24",
    gradient: ["#78350f", "#fbbf24"],
    day: "thu",
    finger: { en: "Index finger", hn: "Tarjani ungli", hi: "तर्जनी" },
    metal: { en: "Gold", hn: "Sona", hi: "सोना" },
    weight: "3–5 ct",
    benefit: {
      en: "Wisdom, marriage & prosperity",
      hn: "Gyan, vivah aur samriddhi",
      hi: "ज्ञान, विवाह और समृद्धि",
    },
  },
  {
    id: "diamond",
    planetKey: "shukra",
    planetEmoji: "💎",
    gemstoneKey: "diamond",
    accent: "#f472b6",
    gradient: ["#831843", "#f9a8d4"],
    day: "fri",
    finger: { en: "Middle / Little finger", hn: "Madhyama / Chhoti ungli", hi: "मध्यमा / कनिष्ठा" },
    metal: { en: "Platinum / Silver", hn: "Platinum / Chandi", hi: "प्लैटिनम / चाँदी" },
    weight: "0.5–1 ct",
    benefit: {
      en: "Luxury, love & creative charm",
      hn: "Bhogvilas, prem aur kala",
      hi: "विलास, प्रेम और कला",
    },
  },
  {
    id: "bluesapphire",
    planetKey: "shani",
    planetEmoji: "🪐",
    gemstoneKey: "bluesapphire",
    accent: "#60a5fa",
    gradient: ["#1e3a8a", "#60a5fa"],
    day: "sat",
    finger: { en: "Middle finger", hn: "Madhyama ungli", hi: "मध्यमा" },
    metal: { en: "Gold / Iron alloy", hn: "Sona / Loha", hi: "सोना / लोहा" },
    weight: "3–5 ct",
    benefit: {
      en: "Discipline, career stability",
      hn: "Anushasan aur career sthirata",
      hi: "अनुशासन और करियर स्थिरता",
    },
  },
  {
    id: "hessonite",
    planetKey: "rahu",
    planetEmoji: "🌑",
    gemstoneKey: "hessonite",
    accent: "#f59e0b",
    gradient: ["#78350f", "#f59e0b"],
    day: "sat",
    finger: { en: "Middle finger", hn: "Madhyama ungli", hi: "मध्यमा" },
    metal: { en: "Silver / Panchdhatu", hn: "Chandi / Panchdhatu", hi: "चाँदी / पंचधातु" },
    weight: "5–7 ct",
    benefit: {
      en: "Sudden gains & foreign luck",
      hn: "Achaanak labh aur videsh yog",
      hi: "अचानक लाभ और विदेश योग",
    },
  },
  {
    id: "catseye",
    planetKey: "ketu",
    planetEmoji: "👁️",
    gemstoneKey: "catseye",
    accent: "#a3e635",
    gradient: ["#365314", "#a3e635"],
    day: "tue",
    finger: { en: "Middle / Ring finger", hn: "Madhyama / Angoothi ungli", hi: "मध्यमा / अनामिका" },
    metal: { en: "Gold / Silver", hn: "Sona / Chandi", hi: "सोना / चाँदी" },
    weight: "3–5 ct",
    benefit: {
      en: "Intuition, moksha & protection",
      hn: "Antardrishti aur suraksha",
      hi: "अंतर्दृष्टि और सुरक्षा",
    },
  },
];

const SIGN_TO_RASHI: Record<string, string> = {
  aries: "mesh", mesh: "mesh", "मेष": "mesh",
  taurus: "vrishabh", vrishabh: "vrishabh", "वृषभ": "vrishabh",
  gemini: "mithun", mithun: "mithun", "मिथुन": "mithun",
  cancer: "kark", kark: "kark", "कर्क": "kark",
  leo: "simha", simha: "simha", "सिंह": "simha",
  virgo: "kanya", kanya: "kanya", "कन्या": "kanya",
  libra: "tula", tula: "tula", "तुला": "tula",
  scorpio: "vrishchik", vrishchik: "vrishchik", "वृश्चिक": "vrishchik",
  sagittarius: "dhanu", dhanu: "dhanu", "धनु": "dhanu",
  capricorn: "makar", makar: "makar", "मकर": "makar",
  aquarius: "kumbh", kumbh: "kumbh", "कुम्भ": "kumbh",
  pisces: "meen", meen: "meen", "मीन": "meen",
};

const RASHI_LUCKY_GEM: Record<string, GemstoneCatalogKey> = {
  mesh: "coral",
  vrishabh: "diamond",
  mithun: "emerald",
  kark: "pearl",
  simha: "ruby",
  kanya: "emerald",
  tula: "diamond",
  vrishchik: "coral",
  dhanu: "yellowsapphire",
  makar: "bluesapphire",
  kumbh: "bluesapphire",
  meen: "yellowsapphire",
};

export function recommendedGemstoneKey(
  moonSign?: string | null,
  planets?: Array<{ name: string; rashi?: string; sign?: string }>,
): GemstoneCatalogKey | null {
  if (moonSign) {
    const k = SIGN_TO_RASHI[moonSign.trim().toLowerCase()];
    if (k && RASHI_LUCKY_GEM[k]) return RASHI_LUCKY_GEM[k];
  }
  const moon = planets?.find(p => p?.name === "Moon");
  const sign = moon?.rashi ?? moon?.sign;
  if (sign) {
    const k = SIGN_TO_RASHI[sign.trim().toLowerCase()];
    if (k && RASHI_LUCKY_GEM[k]) return RASHI_LUCKY_GEM[k];
  }
  return null;
}

export function pickLocalized<T extends Localized>(vlang: "en" | "hn" | "hi", block: T): string {
  return block[vlang] ?? block.en;
}
