/** Love Reality Pro upgrade screen — CRO copy (English). */

export type LoveProUnlockItem = {
  readonly emoji: string;
  readonly title: string;
  /** Full CRO copy — reference / future expand */
  readonly description: string;
  /** One-line hook for compact Pro screen list */
  readonly shortHook: string;
  /** Maps to one of the 3 buyer questions (for UI grouping) */
  readonly answersQuestion?: 1 | 2 | 3;
};

/** Top-of-Pro hero — strongest hook (wait vs move on). */
export const LOVE_REALITY_PRO_HERO = {
  emoji: "🔄",
  title: "Return or Move On?",
  line: "#1 reason people order — should you wait, reconcile, or let go?",
} as const;

/** The 3 questions in every crisis buyer's mind. */
export const LOVE_REALITY_CORE_QUESTIONS = [
  "Do they really love me?",
  "Will we survive or break up?",
  "Should I wait or move on?",
] as const;

export const LOVE_PRO_UNLOCK_ITEMS: readonly LoveProUnlockItem[] = [
  {
    emoji: "💘",
    title: "Emotional Reality",
    description:
      "Beyond the Basic score — what they actually feel for you, where the bond is real, and where it goes cold.",
    shortHook: "What they truly feel — not just what they show",
    answersQuestion: 1,
  },
  {
    emoji: "🛡️",
    title: "Loyalty & Intentions",
    description:
      "Intent behind their behaviour — devoted bond, mixed signals, or hidden pull elsewhere. Temporary doubt vs permanent pattern.",
    shortHook: "Real intent — loyal, tempted, or unsure?",
    answersQuestion: 1,
  },
  {
    emoji: "💔",
    title: "Breakup / Critical Window",
    description:
      "Whether this relationship can survive — critical dates and transits when things can slip before it's too late.",
    shortHook: "Survive together or break — and when risk peaks",
    answersQuestion: 2,
  },
  {
    emoji: "🔄",
    title: "Return or Move On",
    description:
      "The karmic window that decides reconciliation vs permanent parting — your clearest wait-or-go answer.",
    shortHook: "Wait, patch up, or walk away for good",
    answersQuestion: 3,
  },
  {
    emoji: "🔮",
    title: "Future Timeline",
    description:
      "Believable horizon — next 3 months, next 12 months, and key turning points (not vague 3-year guesses).",
    shortHook: "3 mo · 12 mo · key turning points ahead",
    answersQuestion: 3,
  },
  {
    emoji: "🚩",
    title: "Red Flags & Remedies",
    description:
      "Hidden risks in both charts plus personalized upay to soften afflictions — action steps, not fear.",
    shortHook: "What to watch + what you can do",
  },
] as const;

/** Emotional bridge from Basic shock → Pro purchase */
export const LOVE_REALITY_PRO_BENEFIT =
  "Basic showed the score. Founder verifies your full PDF personally." as const;

export const LOVE_REALITY_PRO_SUBTITLE =
  "14-page couple report · astrologer-prepared · remedies included" as const;

export const LOVE_REALITY_PRO_CTA_TITLE = "Order Verified PDF ✨" as const;

export const LOVE_REALITY_PRO_SECTION_LABEL = "WHAT YOU GET" as const;

export const LOVE_REALITY_PRO_SECTION_SUB =
  "6 sections · answers all 3 questions in one verified PDF" as const;

export const LOVE_REALITY_PRO_FOOTNOTE =
  "Pick language · WhatsApp or email delivery · 24–48h (urgent available)" as const;

/** @deprecated use LOVE_REALITY_PRO_CTA_TITLE — kept for Basic banner import */
export const LOVE_REALITY_PRO_CTA_LABEL = LOVE_REALITY_PRO_CTA_TITLE;

export const LOVE_REALITY_BASIC_LOCKED_HINT =
  "*Exact reason for this score is locked in your Pro PDF." as const;
