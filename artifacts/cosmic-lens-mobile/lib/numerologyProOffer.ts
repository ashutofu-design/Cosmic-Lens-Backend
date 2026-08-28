/**
 * Life Mastery Report — unlock offer & checkout routing.
 */
import { STANDARD_DELIVERY_ETA, type DeliveryDeliverable } from "@/lib/deliverySla";

export const LIFE_MASTERY_UI_PRICING = {
  originalInr: 399,
  offerInr: 299,
  discountLabel: "SPECIAL",
} as const;

export const LIFE_MASTERY_VIDEO_PRICE_INR = 799 as const;
export type NumerologyDeliverable = DeliveryDeliverable;

export const NUMEROLOGY_REPORT_PRIORITY_FEE_INR = 149 as const;
export const NUMEROLOGY_VIDEO_PRIORITY_FEE_INR = 299 as const;

/** @deprecated Use numerologyPriorityFeeInr() */
export const LIFE_MASTERY_PRIORITY_SURCHARGE_INR = NUMEROLOGY_REPORT_PRIORITY_FEE_INR;

export function numerologyPriorityFeeInr(
  deliverable: NumerologyDeliverable = "report",
): number {
  return deliverable === "video"
    ? NUMEROLOGY_VIDEO_PRIORITY_FEE_INR
    : NUMEROLOGY_REPORT_PRIORITY_FEE_INR;
}

export function lifeMasteryOrderTotalInr(
  priorityDelivery: boolean,
  deliverable: NumerologyDeliverable = "report",
): number {
  const base =
    deliverable === "video"
      ? LIFE_MASTERY_VIDEO_PRICE_INR
      : LIFE_MASTERY_UI_PRICING.offerInr;
  return base + (priorityDelivery ? numerologyPriorityFeeInr(deliverable) : 0);
}

export { STANDARD_DELIVERY_ETA };

export const LIFE_MASTERY_CHECKOUT_CONFIG = {
  /** Skip Razorpay only for local testing. Production / Play Store must stay false. */
  bypassCheckoutForTesting: false,
  /** Hide ₹ / payment UI. Must stay false so Pro uses Razorpay + admin upload. */
  hidePayment: false,
} as const;

export function numerologyProHidesPayment(): boolean {
  return LIFE_MASTERY_CHECKOUT_CONFIG.hidePayment;
}
