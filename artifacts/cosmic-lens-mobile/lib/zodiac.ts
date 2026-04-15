// ── Zodiac sign detection + accent color system ────────────────────────────

export type ZodiacSign =
  | "Aries" | "Taurus" | "Gemini" | "Cancer" | "Leo" | "Virgo"
  | "Libra" | "Scorpio" | "Sagittarius" | "Capricorn" | "Aquarius" | "Pisces";

export interface ZodiacAccent {
  accent:   string;
  accentBg: string;
}

// ── Accent colors per sign ─────────────────────────────────────────────────
// Kept premium and readable on both dark and light backgrounds
export const ZODIAC_ACCENTS: Record<ZodiacSign, ZodiacAccent> = {
  Aries:       { accent: "#EF4444", accentBg: "rgba(239,68,68,0.10)"   },
  Taurus:      { accent: "#22C55E", accentBg: "rgba(34,197,94,0.10)"   },
  Gemini:      { accent: "#34D399", accentBg: "rgba(52,211,153,0.10)"  },
  Cancer:      { accent: "#93C5FD", accentBg: "rgba(147,197,253,0.12)" },
  Leo:         { accent: "#F59E0B", accentBg: "rgba(245,158,11,0.10)"  },
  Virgo:       { accent: "#84CC16", accentBg: "rgba(132,204,22,0.10)"  },
  Libra:       { accent: "#F472B6", accentBg: "rgba(244,114,182,0.10)" },
  Scorpio:     { accent: "#B91C1C", accentBg: "rgba(185,28,28,0.10)"   },
  Sagittarius: { accent: "#8B5CF6", accentBg: "rgba(139,92,246,0.10)"  },
  Capricorn:   { accent: "#64748B", accentBg: "rgba(100,116,139,0.10)" },
  Aquarius:    { accent: "#3B82F6", accentBg: "rgba(59,130,246,0.10)"  },
  Pisces:      { accent: "#06B6D4", accentBg: "rgba(6,182,212,0.10)"   },
};

// ── Default fallback (indigo) ──────────────────────────────────────────────
export const DEFAULT_ACCENT: ZodiacAccent = {
  accent:   "#6366F1",
  accentBg: "rgba(99,102,241,0.08)",
};

// Emoji for each sign (used in profile / tooltips)
export const ZODIAC_EMOJI: Record<ZodiacSign, string> = {
  Aries: "♈", Taurus: "♉", Gemini: "♊", Cancer: "♋",
  Leo: "♌", Virgo: "♍", Libra: "♎", Scorpio: "♏",
  Sagittarius: "♐", Capricorn: "♑", Aquarius: "♒", Pisces: "♓",
};

// ── Western zodiac boundary detection ─────────────────────────────────────
export function getZodiacSign(day: number, month: number): ZodiacSign {
  if ((month === 3  && day >= 21) || (month === 4  && day <= 19)) return "Aries";
  if ((month === 4  && day >= 20) || (month === 5  && day <= 20)) return "Taurus";
  if ((month === 5  && day >= 21) || (month === 6  && day <= 20)) return "Gemini";
  if ((month === 6  && day >= 21) || (month === 7  && day <= 22)) return "Cancer";
  if ((month === 7  && day >= 23) || (month === 8  && day <= 22)) return "Leo";
  if ((month === 8  && day >= 23) || (month === 9  && day <= 22)) return "Virgo";
  if ((month === 9  && day >= 23) || (month === 10 && day <= 22)) return "Libra";
  if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return "Scorpio";
  if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return "Sagittarius";
  if ((month === 12 && day >= 22) || (month === 1  && day <= 19)) return "Capricorn";
  if ((month === 1  && day >= 20) || (month === 2  && day <= 18)) return "Aquarius";
  return "Pisces";
}

// ── Convenience: get accent from optional day/month (with fallback) ────────
export function getZodiacAccent(
  day: number | undefined,
  month: number | undefined
): ZodiacAccent {
  if (!day || !month) return DEFAULT_ACCENT;
  return ZODIAC_ACCENTS[getZodiacSign(day, month)];
}
