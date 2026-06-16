/** Love Reality Pro upgrade screen — trust-first CRO copy (English). */

export type LoveProUnlockItem = {
  readonly emoji: string;
  readonly title: string;
  readonly description: string;
  readonly shortHook: string;
  readonly answersQuestion?: 1 | 2 | 3;
};

export function loveRealityPartnerReportTitle(p1Name: string, p2Name: string): string {
  return `Report for ${p1Name} & ${p2Name}`;
}

export const LOVE_REALITY_BASIC_TO_PRO_BRIDGE =
  "You saw your Basic scores — this report explains what they mean and what to do next." as const;

export const LOVE_REALITY_FOUNDER_TRUST = {
  title: "Personally Prepared by Founder Astrologer",
  description:
    "Every report is manually reviewed and prepared after studying both charts. This is not an auto-generated AI report.",
  bullets: [
    "Founder-reviewed",
    "Personalized PDF",
    "Remedies included",
    "Saved in My Reports",
  ],
} as const;

export const LOVE_REALITY_PRO_HERO = {
  emoji: "🔄",
  title: "Return or Move On?",
  line: "#1 reason people order — wait, reconcile, or move on?",
} as const;

export const LOVE_REALITY_CORE_QUESTIONS_TITLE = "Your Report Answers These 3 Questions" as const;

export const LOVE_REALITY_CORE_QUESTIONS = [
  "Do they really love me?",
  "Will we survive or break up?",
  "Should I wait or move on?",
] as const;

export const LOVE_REALITY_REPORT_SECTION_TITLE = "What's Inside Your Report" as const;

export const LOVE_PRO_UNLOCK_ITEMS: readonly LoveProUnlockItem[] = [
  {
    emoji: "❤️",
    title: "Emotional Reality",
    description: "What they actually feel for you — beyond surface behaviour.",
    shortHook: "What they truly feel — not just what they show",
    answersQuestion: 1,
  },
  {
    emoji: "🛡️",
    title: "Loyalty & Intentions",
    description: "Real intent behind their actions — devoted, tempted, or unsure.",
    shortHook: "Real intent — loyal, tempted, or unsure",
    answersQuestion: 1,
  },
  {
    emoji: "💔",
    title: "Breakup / Critical Window",
    description: "Whether this bond can survive — and when risk peaks.",
    shortHook: "Survive together or break — and when risk peaks",
    answersQuestion: 2,
  },
  {
    emoji: "🔄",
    title: "Return or Move On",
    description: "Your clearest wait-or-go answer — reconcile or walk away.",
    shortHook: "Wait, patch up, or walk away for good",
    answersQuestion: 3,
  },
  {
    emoji: "🔮",
    title: "Future Timeline",
    description: "Next 3 months, 12 months, and major turning points.",
    shortHook: "3 months, 12 months, and major turning points",
    answersQuestion: 3,
  },
  {
    emoji: "🚩",
    title: "Red Flags & Remedies",
    description: "Hidden risks plus personalized upay — what to watch and what to do.",
    shortHook: "What to watch and what to do",
  },
] as const;

export const LOVE_REALITY_DELIVERY_OPTIONS = [
  {
    emoji: "📦",
    title: "Standard Delivery",
    eta: "Within 24–48 hours",
    surchargeInr: 0,
  },
  {
    emoji: "⚡",
    title: "Priority Delivery",
    eta: "Within 12 hours",
    surchargeInr: 300,
  },
] as const;

/** Shown under Priority toggle — 12h SLA refund for the +₹300 surcharge only. */
export const LOVE_REALITY_PRIORITY_REFUND_GUARANTEE =
  "Not in My Reports within 12 hours? ₹300 priority fee refunded." as const;

/** A/B Version A — swap with LOVE_REALITY_PRO_CTA_TITLE to test */
export const LOVE_REALITY_PRO_CTA_TITLE_ALT_A = "Unlock My Founder-Verified Report" as const;

/** Default CTA — Version B (personalized framing) */
export const LOVE_REALITY_PRO_CTA_TITLE = "Get My Personalized Relationship Report" as const;

export function loveRealitySavingsMessage(savingsInr: number): string {
  return `You saved ₹${savingsInr} today`;
}

export const LOVE_REALITY_PRO_TRUST_BAR =
  "🔒 Secure Payment • Founder Reviewed • Delivered in My Reports" as const;

export const LOVE_REALITY_PRO_CTA_MICROCOPY =
  "Prepared manually after reviewing both charts. No generic AI-generated report is delivered." as const;

/** Hidden until real metrics — toggle via LoveRealitySocialProof visible prop. */
export const LOVE_REALITY_SOCIAL_PROOF = [
  "⭐ Trusted by 100+ relationship seekers",
  "⭐ Average rating 4.9/5",
] as const;

/** @deprecated use LOVE_REALITY_PRO_CTA_TITLE — kept for Basic banner import */
export const LOVE_REALITY_PRO_CTA_LABEL = LOVE_REALITY_PRO_CTA_TITLE;

export const LOVE_REALITY_BASIC_LOCKED_HINT =
  "*Exact reason for this score is locked in your Pro PDF." as const;

/** Legacy exports — avoid breaking older imports */
export const LOVE_REALITY_PRO_BENEFIT = LOVE_REALITY_FOUNDER_TRUST.description;
export const LOVE_REALITY_PRO_SUBTITLE = "Founder-reviewed couple report · remedies included";
export const LOVE_REALITY_PRO_SECTION_LABEL = LOVE_REALITY_REPORT_SECTION_TITLE;
export const LOVE_REALITY_PRO_SECTION_SUB = "6 sections · one personalized PDF";
export const LOVE_REALITY_PRO_FOOTNOTE = LOVE_REALITY_PRO_CTA_MICROCOPY;
