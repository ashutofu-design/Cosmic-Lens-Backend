/**
 * Modern display layer for classical Ashtakoot koots.
 * Backend keys stay varna/vasya/tara/… — UI shows emotional names.
 */

export type MilanKootKey =
  | "varna"
  | "vasya"
  | "tara"
  | "yoni"
  | "maitri"
  | "gana"
  | "bhakut"
  | "nadi";

export type MilanKootDisplayDef = {
  key: MilanKootKey;
  /** Primary label users see */
  modernTitle: string;
  /** Small classical tag (Gun Milan literacy) */
  classicalLabel: string;
  emoji: string;
  color: string;
  tagline: string;
};

/** Classical Ashtakoot order — used in score breakdown */
export const MILAN_KOOT_DISPLAY: MilanKootDisplayDef[] = [
  {
    key: "varna",
    modernTitle: "Spiritual Harmony",
    classicalLabel: "Varna",
    emoji: "🌊",
    color: "#38bdf8",
    tagline: "Work ethic & spiritual pace between you",
  },
  {
    key: "vasya",
    modernTitle: "Attraction Power",
    classicalLabel: "Vashya",
    emoji: "🧲",
    color: "#34d399",
    tagline: "Mutual pull, influence & magnetic hold",
  },
  {
    key: "tara",
    modernTitle: "Destiny Link",
    classicalLabel: "Tara",
    emoji: "✨",
    color: "#fbbf24",
    tagline: "Luck, timing & life-path alignment",
  },
  {
    key: "yoni",
    modernTitle: "Intimacy Match",
    classicalLabel: "Yoni",
    emoji: "🔥",
    color: "#f43f5e",
    tagline: "Physical chemistry & instinctive closeness",
  },
  {
    key: "maitri",
    modernTitle: "Emotional Bond",
    classicalLabel: "Graha Maitri",
    emoji: "💜",
    color: "#c084fc",
    tagline: "Heart-to-heart understanding & mental sync",
  },
  {
    key: "gana",
    modernTitle: "Personality Energy",
    classicalLabel: "Gana",
    emoji: "⚡",
    color: "#ec4899",
    tagline: "Temperament, nature & daily rhythm",
  },
  {
    key: "bhakut",
    modernTitle: "Life Alignment",
    classicalLabel: "Bhakut",
    emoji: "🌙",
    color: "#f97316",
    tagline: "Family harmony, home & shared prosperity",
  },
  {
    key: "nadi",
    modernTitle: "Soul Sync",
    classicalLabel: "Nadi",
    emoji: "🧬",
    color: "#a78bfa",
    tagline: "Deep soul energy & long-term constitution",
  },
];

const BY_KEY = Object.fromEntries(MILAN_KOOT_DISPLAY.map(d => [d.key, d])) as Record<
  MilanKootKey,
  MilanKootDisplayDef
>;

export function milanKootDef(key: string): MilanKootDisplayDef | undefined {
  return BY_KEY[key as MilanKootKey];
}

export function milanKootModernTitle(key: string): string {
  return milanKootDef(key)?.modernTitle ?? key;
}

/** Hero chips on relationship / marketing surfaces */
export const MILAN_HIGHLIGHT_ITEMS = [
  "Soul Sync",
  "Destiny Link",
  "Emotional Bond",
  "Intimacy Match",
] as const;

export const MILAN_STRUCTURE_HERO = {
  primaryBadge: "PRIMARY SCORE",
  title: "Marriage Structure",
  subtitle: "7th house · D9 · chart depth — your main reading",
} as const;

export const MILAN_TWO_LENS_EXPLAINER =
  "Two different lenses. Structure (/100) = long-term marriage chart strength. Gun Milan (/36) = classical Moon match. Both can differ — that is normal.";

export const MILAN_BREAKDOWN_SECTION = {
  referenceBadge: "REFERENCE",
  title: "Traditional Gun Milan",
  subtitle: "Classical Moon match · 8 koots · out of 36",
} as const;
