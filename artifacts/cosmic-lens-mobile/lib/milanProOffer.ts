/**
 * Kundli Milan — Pro unlock offer & checkout routing (client).
 *
 * Temporary testing mode: show promotional sticker prices and let the user
 * continue the Pro experience (language picker → confirm → PDF) without
 * hitting the payment gateway. For production, set `bypassCheckoutForTesting`
 * to false and point `paymentEntryRoute` at your Cashfree / native checkout
 * screen instead of `/subscription`.
 */

/** Shown in the Milan Pro upgrade UI (strikethrough vs offer). */
export const MILAN_PRO_UI_PRICING = {
  originalInr: 699,
  offerInr: 299,
} as const;

export const MILAN_PRO_CHECKOUT_CONFIG = {
  /**
   * When true, "Unlock Full Analysis" runs the in-app Pro flow immediately
   * (same as today). When false, the CTA should send the user to checkout
   * before generating the PDF.
   */
  /** Set true only for local dev without Cashfree. Production: false */
  bypassCheckoutForTesting: false,

} as const;

/** Opens language picker; payment runs after language selection (see coupleReportCheckoutFlow). */
export function runMilanProUnlockCta(opts: { continueProExperience: () => void }): void {
  opts.continueProExperience();
}
