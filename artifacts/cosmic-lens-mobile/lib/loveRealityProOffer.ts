/**
 * Love Reality Pro — unlock offer & checkout routing (mirrors Milan).
 */
export const LOVE_REALITY_PRO_UI_PRICING = {
  originalInr: 499,
  offerInr: 149,
  discountLabel: "70% OFF",
} as const;

export const LOVE_REALITY_CHECKOUT_CONFIG = {
  /** Temporarily skip Razorpay — language pick → generate PDF → My Reports */
  bypassCheckoutForTesting: true,
} as const;

/** Opens language picker; payment runs after language selection (see coupleReportCheckoutFlow). */
export function runLoveRealityProUnlockCta(opts: { continueProExperience: () => void }): void {
  opts.continueProExperience();
}
