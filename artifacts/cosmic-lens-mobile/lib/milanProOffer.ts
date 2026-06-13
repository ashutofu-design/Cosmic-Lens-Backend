/**
 * Kundli Milan — Marriage Compatibility Pro offer & checkout (client).
 */
export const MILAN_PRO_UI_PRICING = {
  regularInr: 999,
  todayInr: 699,
} as const;

export const MILAN_URGENT_SURCHARGE_INR = 300 as const;

export function milanOrderTotalInr(priorityDelivery: boolean): number {
  return MILAN_PRO_UI_PRICING.todayInr + (priorityDelivery ? MILAN_URGENT_SURCHARGE_INR : 0);
}

export function milanFirstTimeSavingsInr(): number {
  return MILAN_PRO_UI_PRICING.regularInr - MILAN_PRO_UI_PRICING.todayInr;
}

export const MILAN_PRO_CHECKOUT_CONFIG = {
  /** Language pick → human order (same as Love Pro). Set false for Razorpay. */
  bypassCheckoutForTesting: true,
} as const;

export function runMilanProUnlockCta(opts: { continueProExperience: () => void }): void {
  opts.continueProExperience();
}

export function milanProRouteParams(partnerId?: string | null) {
  return {
    pathname: "/kundli-milan-pro" as const,
    params: { partnerId: partnerId ?? "" },
  };
}
