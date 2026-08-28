/** Marriage Compatibility Pro — trust-first CRO copy (English). */

export type MilanProUnlockItem = {
  readonly emoji: string;
  readonly title: string;
  readonly description: string;
  readonly shortHook: string;
  readonly answersQuestion?: 1 | 2 | 3;
};

export const MILAN_PRO_HERO = {
  emoji: "💍",
  title: "Marry or Wait?",
  line: "#1 reason people order — is this the right marriage match and timing?",
} as const;

export const MILAN_CORE_QUESTIONS_TITLE = "Your Report Answers These 3 Questions" as const;

export const MILAN_CORE_QUESTIONS = [
  "Should we get married?",
  "Will this marriage last?",
  "When is the best wedding window?",
] as const;

export const MILAN_REPORT_SECTION_TITLE = "What's Inside Your Report" as const;

export const MILAN_PRO_UNLOCK_ITEMS: readonly MilanProUnlockItem[] = [
  {
    emoji: "🏠",
    title: "D1 Marriage Structure",
    description: "7th house, lord strength, Darakaraka — how each chart supports marriage.",
    shortHook: "Birth chart marriage foundation for both",
    answersQuestion: 1,
  },
  {
    emoji: "💫",
    title: "D9 Long-Term Bond",
    description: "Navamsa marriage tone — early years vs long married life together.",
    shortHook: "Inner chart — long-term married life tone",
    answersQuestion: 2,
  },
  {
    emoji: "🔗",
    title: "Cross-Chart Synastry",
    description: "How Partner A's marriage ruler lands in Partner B's chart — and vice versa.",
    shortHook: "How you affect each other's marriage path",
    answersQuestion: 1,
  },
  {
    emoji: "🔥",
    title: "Manglik & Alerts",
    description: "Manglik balance, cancellation, and hidden cross-chart warnings.",
    shortHook: "Risk flags Basic intentionally hides",
    answersQuestion: 2,
  },
  {
    emoji: "📅",
    title: "Marriage Dasha Windows",
    description: "Best and risky timing for engagement, wedding, and first years.",
    shortHook: "When to marry — and when to wait",
    answersQuestion: 3,
  },
  {
    emoji: "🪔",
    title: "Remedies & Pro PDF",
    description: "Personalized upay chain + founder-reviewed PDF in My Reports.",
    shortHook: "What to do — full remedy map",
  },
] as const;

export const MILAN_DELIVERY_OPTIONS = [
  {
    emoji: "📦",
    title: "Standard Delivery",
    eta: "4–6 business days",
    surchargeInr: 0,
  },
  {
    emoji: "⚡",
    title: "Priority Delivery",
    eta: "Within 12 hours",
    surchargeInr: 299,
  },
] as const;

export const MILAN_PRIORITY_REFUND_GUARANTEE =
  "12-hour Priority Guarantee — If we miss the 12-hour delivery window, your Priority fee is 100% refunded." as const;

export const MILAN_PRO_CTA_TITLE = "Get My Personalized Marriage Compatibility Report" as const;

export function milanSavingsMessage(savingsInr: number): string {
  return `You saved ₹${savingsInr} today`;
}

export const MILAN_PRO_TRUST_BAR =
  "🔒 Secure Payment • Founder Reviewed • Delivered in My Reports" as const;
