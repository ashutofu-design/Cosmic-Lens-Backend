/** Love Reality Pro upgrade screen — CRO copy (English). */

export type LoveProUnlockItem = {
  readonly emoji: string;
  readonly title: string;
  /** Full CRO copy — reference / future expand */
  readonly description: string;
  /** One-line hook for compact Pro screen list */
  readonly shortHook: string;
};

export const LOVE_PRO_UNLOCK_ITEMS: readonly LoveProUnlockItem[] = [
  {
    emoji: "💘",
    title: "Love Depth",
    description:
      "Basic gave you the surface percentages. Unlock the exact planetary degrees causing the block—and if it's fixable.",
    shortHook: "Degrees behind the block + fixable?",
  },
  {
    emoji: "💔",
    title: "Breakup Window",
    description:
      "You see the risk level is high. Get the exact critical dates and planetary transits when things can slip out of control—before it's too late.",
    shortHook: "Critical dates before things slip",
  },
  {
    emoji: "🛡️",
    title: "Loyalty Triggers",
    description:
      "The underlying triggers behind the behavioral scores. Understand if this instability is temporary or a permanent trait.",
    shortHook: "Temporary doubt or permanent trait?",
  },
  {
    emoji: "🔄",
    title: "Return or Part?",
    description:
      "Timing is everything. Discover the hidden Karmic window that decides whether you will part ways permanently or patch up stronger.",
    shortHook: "Karmic window to patch up or move on",
  },
  {
    emoji: "🔮",
    title: "Future 1–3 Years",
    description:
      "A month-by-month cosmic roadmap of your relationship. Know exactly when the storm clears and when stability returns.",
    shortHook: "Month-by-month when stability returns",
  },
  {
    emoji: "🚩",
    title: "Red Flags + Upay",
    description:
      "The full 14-page personalized breakdown containing custom remedial measures to defuse planetary afflictions.",
    shortHook: "Personal remedies for your charts",
  },
] as const;

/** Emotional bridge from Basic shock → Pro purchase */
export const LOVE_REALITY_PRO_BENEFIT =
  "Basic showed the score. Founder verifies your full PDF personally." as const;

export const LOVE_REALITY_PRO_SUBTITLE =
  "14-page couple report · astrologer-prepared · remedies included" as const;

export const LOVE_REALITY_PRO_CTA_TITLE = "Order Verified PDF ✨" as const;

export const LOVE_REALITY_PRO_SECTION_LABEL = "WHAT YOU GET" as const;

export const LOVE_REALITY_PRO_FOOTNOTE =
  "Pick language · WhatsApp or email delivery · 24–48h (urgent available)" as const;

/** @deprecated use LOVE_REALITY_PRO_CTA_TITLE — kept for Basic banner import */
export const LOVE_REALITY_PRO_CTA_LABEL = LOVE_REALITY_PRO_CTA_TITLE;

export const LOVE_REALITY_BASIC_LOCKED_HINT =
  "*Exact reason for this score is locked in your Pro PDF." as const;
