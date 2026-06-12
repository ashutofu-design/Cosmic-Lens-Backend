/**
 * Love Reality Pro — unlock offer & checkout routing.
 */
export const LOVE_REALITY_PRO_UI_PRICING = {
  regularInr: 999,
  todayInr: 499,
  firstTimeDiscountBadge: "First-Time User Discount Applied",
  /** @deprecated use regularInr */
  originalInr: 999,
  /** @deprecated use todayInr */
  offerInr: 499,
} as const;

export const LOVE_REALITY_URGENT_SURCHARGE_INR = 300 as const;

export function loveRealityOrderTotalInr(urgent: boolean): number {
  return (
    LOVE_REALITY_PRO_UI_PRICING.todayInr +
    (urgent ? LOVE_REALITY_URGENT_SURCHARGE_INR : 0)
  );
}

export const LOVE_REALITY_CHECKOUT_CONFIG = {
  /** Temporarily skip Razorpay — language pick → human order screen */
  bypassCheckoutForTesting: true,
} as const;

/** Opens language picker; payment runs after language selection (see coupleReportCheckoutFlow). */
export function runLoveRealityProUnlockCta(opts: { continueProExperience: () => void }): void {
  opts.continueProExperience();
}
