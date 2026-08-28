/**
 * Kundli Milan — Marriage Compatibility Pro offer & checkout (client).
 */
import type { DeliveryDeliverable } from "@/lib/deliverySla";

export const MILAN_PRO_UI_PRICING = {
  regularInr: 999,
  todayInr: 699,
} as const;

export const MILAN_VIDEO_PRICE_INR = 1299 as const;
export type MilanProDeliverable = DeliveryDeliverable;

/** Priority fee for Kundli Milan Pro — report and video both use ₹299. */
export const MILAN_PRIORITY_FEE_INR = 299 as const;

/** @deprecated Use MILAN_PRIORITY_FEE_INR */
export const MILAN_URGENT_SURCHARGE_INR = MILAN_PRIORITY_FEE_INR;

export function milanPriorityFeeInr(_deliverable?: MilanProDeliverable): number {
  return MILAN_PRIORITY_FEE_INR;
}

export function milanOrderTotalInr(
  priorityDelivery: boolean,
  deliverable: MilanProDeliverable = "report",
): number {
  const base =
    deliverable === "video" ? MILAN_VIDEO_PRICE_INR : MILAN_PRO_UI_PRICING.todayInr;
  return base + (priorityDelivery ? milanPriorityFeeInr(deliverable) : 0);
}

export function milanFirstTimeSavingsInr(): number {
  return MILAN_PRO_UI_PRICING.regularInr - MILAN_PRO_UI_PRICING.todayInr;
}

export const MILAN_PRO_CHECKOUT_CONFIG = {
  /** Set true only for local QA — skips Razorpay. */
  bypassCheckoutForTesting: false,
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
