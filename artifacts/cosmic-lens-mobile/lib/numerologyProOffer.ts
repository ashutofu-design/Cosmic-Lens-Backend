/**
 * Life Mastery Report — unlock offer & checkout routing.
 */
export const LIFE_MASTERY_UI_PRICING = {
  originalInr: 599,
  offerInr: 499,
  discountLabel: "SPECIAL",
} as const;

export const LIFE_MASTERY_PRIORITY_SURCHARGE_INR = 300 as const;

export function lifeMasteryOrderTotalInr(priorityDelivery: boolean): number {
  return LIFE_MASTERY_UI_PRICING.offerInr + (priorityDelivery ? LIFE_MASTERY_PRIORITY_SURCHARGE_INR : 0);
}

export const LIFE_MASTERY_CHECKOUT_CONFIG = {
  /** Dev only — skips Cashfree; entitlement + PDF run immediately */
  bypassCheckoutForTesting: false,
} as const;
