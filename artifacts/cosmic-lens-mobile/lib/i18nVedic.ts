// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Vedic Vocabulary Translations
// Central lookup for rashi names, planets, days, gemstones, directions, etc.
// 3-bucket strategy: en (English) | hn (Hinglish/Roman) | hi (Devanagari)
// ══════════════════════════════════════════════════════════════════════════════

import type { UILang } from "./i18n";

export type VLang = "en" | "hn" | "hi";

// Bucket all 24 UI langs into 3 vocab buckets.
// English + global langs → en | Hinglish → hn | Hindi + Indian regional → hi
export function vedicLang(l: UILang): VLang {
  if (l === "en") return "en";
  if (l === "hn") return "hn";
  if (["hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"].includes(l as string)) {
    return "hi";
  }
  return "en";
}

export type Triplet = { en: string; hn: string; hi: string };

export function pick(lang: UILang | VLang, t: Triplet): string {
  const v: VLang = (lang === "en" || lang === "hn" || lang === "hi") && (t as any)[lang]
    ? (lang as VLang)
    : vedicLang(lang as UILang);
  return t[v] || t.en;
}

// ── Rashi (zodiac signs) ─────────────────────────────────────────────────────
export type RashiKey =
  | "mesh" | "vrishabh" | "mithun" | "kark" | "simha" | "kanya"
  | "tula" | "vrishchik" | "dhanu" | "makar" | "kumbh" | "meen";

export const RASHI: Record<RashiKey, Triplet & { emoji: string; lord: string }> = {
  mesh:      { en: "Aries",       hn: "Mesh",      hi: "मेष",     emoji: "♈", lord: "mangal" },
  vrishabh:  { en: "Taurus",      hn: "Vrishabh",  hi: "वृषभ",    emoji: "♉", lord: "shukra" },
  mithun:    { en: "Gemini",      hn: "Mithun",    hi: "मिथुन",   emoji: "♊", lord: "budh"   },
  kark:      { en: "Cancer",      hn: "Kark",      hi: "कर्क",    emoji: "♋", lord: "chandra"},
  simha:     { en: "Leo",         hn: "Simha",     hi: "सिंह",    emoji: "♌", lord: "surya"  },
  kanya:     { en: "Virgo",       hn: "Kanya",     hi: "कन्या",   emoji: "♍", lord: "budh"   },
  tula:      { en: "Libra",       hn: "Tula",      hi: "तुला",    emoji: "♎", lord: "shukra" },
  vrishchik: { en: "Scorpio",     hn: "Vrishchik", hi: "वृश्चिक", emoji: "♏", lord: "mangal" },
  dhanu:     { en: "Sagittarius", hn: "Dhanu",     hi: "धनु",     emoji: "♐", lord: "guru"   },
  makar:     { en: "Capricorn",   hn: "Makar",     hi: "मकर",     emoji: "♑", lord: "shani"  },
  kumbh:     { en: "Aquarius",    hn: "Kumbh",     hi: "कुम्भ",   emoji: "♒", lord: "shani"  },
  meen:      { en: "Pisces",      hn: "Meen",      hi: "मीन",     emoji: "♓", lord: "guru"   },
};

// ── Planets ──────────────────────────────────────────────────────────────────
export type PlanetKey =
  | "surya" | "chandra" | "mangal" | "budh" | "guru"
  | "shukra" | "shani" | "rahu" | "ketu";

export const PLANET: Record<PlanetKey, Triplet> = {
  surya:   { en: "Sun",     hn: "Surya",   hi: "सूर्य"  },
  chandra: { en: "Moon",    hn: "Chandra", hi: "चंद्र"   },
  mangal:  { en: "Mars",    hn: "Mangal",  hi: "मंगल"   },
  budh:    { en: "Mercury", hn: "Budh",    hi: "बुध"    },
  guru:    { en: "Jupiter", hn: "Guru",    hi: "गुरु"   },
  shukra:  { en: "Venus",   hn: "Shukra",  hi: "शुक्र"  },
  shani:   { en: "Saturn",  hn: "Shani",   hi: "शनि"    },
  rahu:    { en: "Rahu",    hn: "Rahu",    hi: "राहु"   },
  ketu:    { en: "Ketu",    hn: "Ketu",    hi: "केतु"   },
};

// ── Days of week ─────────────────────────────────────────────────────────────
export type DayKey = "sun" | "mon" | "tue" | "wed" | "thu" | "fri" | "sat";

export const DAY: Record<DayKey, Triplet> = {
  sun: { en: "Sunday",    hn: "Ravivaar",  hi: "रविवार"  },
  mon: { en: "Monday",    hn: "Somvar",    hi: "सोमवार"  },
  tue: { en: "Tuesday",   hn: "Mangalvar", hi: "मंगलवार" },
  wed: { en: "Wednesday", hn: "Budhavar",  hi: "बुधवार"  },
  thu: { en: "Thursday",  hn: "Guruvaar",  hi: "गुरुवार" },
  fri: { en: "Friday",    hn: "Shukravar", hi: "शुक्रवार"},
  sat: { en: "Saturday",  hn: "Shanivaar", hi: "शनिवार"  },
};

// ── Directions (8-way) ───────────────────────────────────────────────────────
export type DirKey = "N" | "S" | "E" | "W" | "NE" | "SE" | "SW" | "NW";

export const DIRECTION: Record<DirKey, Triplet> = {
  N:  { en: "North",     hn: "Uttar",       hi: "उत्तर"   },
  S:  { en: "South",     hn: "Dakshin",     hi: "दक्षिण"  },
  E:  { en: "East",      hn: "Purva",       hi: "पूर्व"   },
  W:  { en: "West",      hn: "Paschim",     hi: "पश्चिम"  },
  NE: { en: "Northeast", hn: "Ishaan",      hi: "ईशान"    },
  SE: { en: "Southeast", hn: "Agni",        hi: "अग्नि"   },
  SW: { en: "Southwest", hn: "Niriti",      hi: "नैऋत्य"  },
  NW: { en: "Northwest", hn: "Vayu",        hi: "वायव्य"  },
};

// ── Colors ───────────────────────────────────────────────────────────────────
export const COLOR: Record<string, Triplet> = {
  red:      { en: "Red",        hn: "Laal",      hi: "लाल"      },
  orange:   { en: "Orange",     hn: "Narangi",   hi: "नारंगी"    },
  white:    { en: "White",      hn: "Safed",     hi: "सफेद"     },
  pink:     { en: "Pink",       hn: "Gulabi",    hi: "गुलाबी"   },
  yellow:   { en: "Yellow",     hn: "Peela",     hi: "पीला"     },
  green:    { en: "Green",      hn: "Hari",      hi: "हरा"      },
  blue:     { en: "Blue",       hn: "Neela",     hi: "नीला"     },
  gold:     { en: "Gold",       hn: "Sona",      hi: "सोना"     },
  silver:   { en: "Silver",     hn: "Chandi",    hi: "चांदी"    },
  black:    { en: "Black",      hn: "Kaala",     hi: "काला"     },
  maroon:   { en: "Maroon",     hn: "Maroon",    hi: "मैरून"    },
  violet:   { en: "Violet",     hn: "Baigani",   hi: "बैंगनी"   },
  lime:     { en: "Lime",       hn: "Neebu",     hi: "नींबू"    },
  seagreen: { en: "Sea Green",  hn: "Sea Green", hi: "सी-ग्रीन" },
  skyblue:  { en: "Sky Blue",   hn: "Aasmani",   hi: "आसमानी"   },
  brown:    { en: "Brown",      hn: "Bhura",     hi: "भूरा"     },
};

// ── Metals ───────────────────────────────────────────────────────────────────
export const METAL: Record<string, Triplet> = {
  copper: { en: "Copper", hn: "Tamba",  hi: "तांबा"  },
  silver: { en: "Silver", hn: "Chandi", hi: "चांदी"  },
  gold:   { en: "Gold",   hn: "Sona",   hi: "सोना"   },
  iron:   { en: "Iron",   hn: "Loha",   hi: "लोहा"   },
  bronze: { en: "Bronze", hn: "Kaansa", hi: "कांसा"  },
};

// ── 5 Elements (Pancha-mahabhuta) ─────────────────────────────────────────────
export const ELEMENT: Record<string, Triplet> = {
  fire:  { en: "Fire",  hn: "Agni",    hi: "अग्नि"   },
  earth: { en: "Earth", hn: "Prithvi", hi: "पृथ्वी"  },
  air:   { en: "Air",   hn: "Vayu",    hi: "वायु"    },
  water: { en: "Water", hn: "Jal",     hi: "जल"      },
  ether: { en: "Ether", hn: "Akash",   hi: "आकाश"    },
};

// ── Gemstones ────────────────────────────────────────────────────────────────
export const GEMSTONE: Record<string, Triplet> = {
  ruby:           { en: "Ruby",            hn: "Manikya",   hi: "माणिक्य"  },
  pearl:          { en: "Pearl",           hn: "Moti",      hi: "मोती"     },
  coral:          { en: "Red Coral",       hn: "Moonga",    hi: "मूंगा"    },
  emerald:        { en: "Emerald",         hn: "Panna",     hi: "पन्ना"    },
  yellowsapphire: { en: "Yellow Sapphire", hn: "Pukhraj",   hi: "पुखराज"   },
  diamond:        { en: "Diamond",         hn: "Heera",     hi: "हीरा"     },
  bluesapphire:   { en: "Blue Sapphire",   hn: "Neelam",    hi: "नीलम"     },
  hessonite:      { en: "Hessonite",       hn: "Gomed",     hi: "गोमेद"    },
  catseye:        { en: "Cat's Eye",       hn: "Lahsuniya", hi: "लहसुनिया" },
};

// ── Deities (transliteration only — sacred names kept consistent across langs) ─
export const DEITY: Record<string, Triplet> = {
  hanuman:   { en: "Hanuman",       hn: "Hanuman",       hi: "हनुमान"     },
  lakshmi:   { en: "Lakshmi",       hn: "Lakshmi",       hi: "लक्ष्मी"     },
  ganesh:    { en: "Ganesha",       hn: "Ganesh",        hi: "गणेश"        },
  shiva:     { en: "Shiva",         hn: "Shiva",         hi: "शिव"         },
  surya:     { en: "Surya (Sun)",   hn: "Surya",         hi: "सूर्य देव"    },
  saraswati: { en: "Saraswati",     hn: "Saraswati",     hi: "सरस्वती"     },
  kali:      { en: "Kali",          hn: "Kali",          hi: "काली"        },
  vishnu:    { en: "Vishnu",        hn: "Vishnu",        hi: "विष्णु"      },
  shani:     { en: "Shani Dev",     hn: "Shani Dev",     hi: "शनि देव"     },
  durga:     { en: "Durga",         hn: "Durga",         hi: "दुर्गा"      },
  parvati:   { en: "Parvati",       hn: "Parvati",       hi: "पार्वती"     },
};

// ── Convenience: rashi triplet with name only ────────────────────────────────
export function rashiName(key: RashiKey, lang: UILang): string {
  return pick(lang, RASHI[key]);
}

export function planetName(key: PlanetKey, lang: UILang): string {
  return pick(lang, PLANET[key]);
}

export function dayName(key: DayKey, lang: UILang): string {
  return pick(lang, DAY[key]);
}

// Map weekday number (0=Sun..6=Sat) → DayKey
export const WEEKDAY_KEYS: DayKey[] = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

// ── Nakshatra (27 lunar mansions) ────────────────────────────────────────────
// Order is canonical (0=Ashwini ... 26=Revati).
export const NAKSHATRA: Triplet[] = [
  { en:"Ashwini",          hn:"Ashwini",          hi:"अश्विनी" },
  { en:"Bharani",          hn:"Bharani",          hi:"भरणी" },
  { en:"Krittika",         hn:"Krittika",         hi:"कृत्तिका" },
  { en:"Rohini",           hn:"Rohini",           hi:"रोहिणी" },
  { en:"Mrigashira",       hn:"Mrigashira",       hi:"मृगशिरा" },
  { en:"Ardra",            hn:"Ardra",            hi:"आर्द्रा" },
  { en:"Punarvasu",        hn:"Punarvasu",        hi:"पुनर्वसु" },
  { en:"Pushya",           hn:"Pushya",           hi:"पुष्य" },
  { en:"Ashlesha",         hn:"Ashlesha",         hi:"आश्लेषा" },
  { en:"Magha",            hn:"Magha",            hi:"मघा" },
  { en:"Purva Phalguni",   hn:"Purva Phalguni",   hi:"पूर्व फाल्गुनी" },
  { en:"Uttara Phalguni",  hn:"Uttara Phalguni",  hi:"उत्तर फाल्गुनी" },
  { en:"Hasta",            hn:"Hasta",            hi:"हस्त" },
  { en:"Chitra",           hn:"Chitra",           hi:"चित्रा" },
  { en:"Swati",            hn:"Swati",            hi:"स्वाति" },
  { en:"Vishakha",         hn:"Vishakha",         hi:"विशाखा" },
  { en:"Anuradha",         hn:"Anuradha",         hi:"अनुराधा" },
  { en:"Jyeshtha",         hn:"Jyeshtha",         hi:"ज्येष्ठा" },
  { en:"Mula",             hn:"Mula",             hi:"मूल" },
  { en:"Purva Ashadha",    hn:"Purva Ashadha",    hi:"पूर्वाषाढ़ा" },
  { en:"Uttara Ashadha",   hn:"Uttara Ashadha",   hi:"उत्तराषाढ़ा" },
  { en:"Shravana",         hn:"Shravana",         hi:"श्रवण" },
  { en:"Dhanishtha",       hn:"Dhanishtha",       hi:"धनिष्ठा" },
  { en:"Shatabhisha",      hn:"Shatabhisha",      hi:"शतभिषा" },
  { en:"Purva Bhadrapada", hn:"Purva Bhadrapada", hi:"पूर्व भाद्रपद" },
  { en:"Uttara Bhadrapada",hn:"Uttara Bhadrapada",hi:"उत्तर भाद्रपद" },
  { en:"Revati",           hn:"Revati",           hi:"रेवती" },
];

export function nakshatraName(idx: number, lang: UILang | VLang): string {
  const n = NAKSHATRA[idx];
  if (!n) return "";
  return pick(lang, n);
}

// ── Rashi index helper (0=Mesh..11=Meen) ────────────────────────────────────
export const RASHI_KEYS: RashiKey[] = [
  "mesh","vrishabh","mithun","kark","simha","kanya",
  "tula","vrishchik","dhanu","makar","kumbh","meen",
];
export function rashiAt(idx: number, lang: UILang | VLang): string {
  const k = RASHI_KEYS[((idx % 12) + 12) % 12];
  return pick(lang, RASHI[k]);
}
