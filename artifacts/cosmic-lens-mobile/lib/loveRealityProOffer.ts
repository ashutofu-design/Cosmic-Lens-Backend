/**
 * Love Reality Pro — unlock offer & checkout routing.
 */
import type { DeliveryDeliverable } from "@/lib/deliverySla";

export const LOVE_REALITY_PRO_UI_PRICING = {
  regularInr: 999,
  todayInr: 499,
  firstTimeDiscountBadge: "First-Time User Discount Applied",
  /** @deprecated use regularInr */
  originalInr: 999,
  /** @deprecated use todayInr */
  offerInr: 499,
} as const;

export const LOVE_REALITY_VIDEO_PRICE_INR = 999 as const;
export type CoupleProDeliverable = DeliveryDeliverable;

/** Priority fee for Love Reality Pro — report and video both use ₹299. */
export const LOVE_REALITY_PRIORITY_FEE_INR = 299 as const;

/** @deprecated Use LOVE_REALITY_PRIORITY_FEE_INR */
export const LOVE_REALITY_URGENT_SURCHARGE_INR = LOVE_REALITY_PRIORITY_FEE_INR;

export function loveRealityPriorityFeeInr(_deliverable?: CoupleProDeliverable): number {
  return LOVE_REALITY_PRIORITY_FEE_INR;
}

export function loveRealityOrderTotalInr(
  priorityDelivery: boolean,
  deliverable: CoupleProDeliverable = "report",
): number {
  const base =
    deliverable === "video"
      ? LOVE_REALITY_VIDEO_PRICE_INR
      : LOVE_REALITY_PRO_UI_PRICING.todayInr;
  return base + (priorityDelivery ? loveRealityPriorityFeeInr(deliverable) : 0);
}

export function normalizeWhatsappDigits(raw: string): string {
  let digits = (raw || "").replace(/\D/g, "");
  if (digits.startsWith("0091") && digits.length >= 14) digits = digits.slice(4);
  else if (digits.startsWith("91") && digits.length >= 12) digits = digits.slice(2);
  if (digits.startsWith("0") && digits.length === 11) digits = digits.slice(1);
  return digits.slice(0, 10);
}

export function loveRealityFirstTimeSavingsInr(): number {
  return LOVE_REALITY_PRO_UI_PRICING.regularInr - LOVE_REALITY_PRO_UI_PRICING.todayInr;
}

export const LOVE_REALITY_CHECKOUT_CONFIG = {
  /** Set true only for local QA — skips Razorpay. */
  bypassCheckoutForTesting: false,
} as const;

/** Opens language picker; payment runs after language selection (see coupleReportCheckoutFlow). */
export function runLoveRealityProUnlockCta(opts: { continueProExperience: () => void }): void {
  opts.continueProExperience();
}

/** Dedicated Pro purchase screen (separate from Basic Love Reality). */
export function loveRealityProRouteParams(partnerId?: string | null) {
  return {
    pathname: "/love-reality-pro" as const,
    params: { partnerId: partnerId ?? "" },
  };
}
