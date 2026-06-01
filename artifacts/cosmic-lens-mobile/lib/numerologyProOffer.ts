/**
 * Life Mastery Report — unlock offer & checkout routing.
 */
export const LIFE_MASTERY_UI_PRICING = {
  originalInr: 599,
  offerInr: 249,
  discountLabel: "58% OFF",
} as const;

export const LIFE_MASTERY_CHECKOUT_CONFIG = {
  /** Dev only — skips Cashfree; entitlement + PDF run immediately */
  bypassCheckoutForTesting: false,
} as const;
