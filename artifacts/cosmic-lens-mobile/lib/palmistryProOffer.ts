import {
  PRIORITY_SLA_HOURS,
  STANDARD_DELIVERY_ETA,
  VIDEO_PRIORITY_FEE_INR,
  type DeliveryDeliverable,
} from "@/lib/deliverySla";

export type PalmistryProPlan = "pdf" | "vip";

export const PALMISTRY_PRO_PLANS = {
  pdf: {
    id: "pdf" as const,
    title: "PDF Report",
    priceInr: 1499,
    deliveryLine: "📄 4–6 days",
    includes: ["Founder-reviewed PDF", "Both-hand reading", "My Reports delivery"],
  },
  vip: {
    id: "vip" as const,
    title: "VIP Video Explanation",
    priceInr: 2999,
    badge: "Most Recommended · VIP",
    deliveryLine: "🎥 Video explanation in 4–6 days",
    includes: ["Personal video explanation", "Both-hand reading on camera", "WhatsApp delivery"],
  },
} as const;

export const PALMISTRY_REPORT_PRIORITY_FEE_INR = 299 as const;
export const PALMISTRY_VIDEO_PRIORITY_FEE_INR = VIDEO_PRIORITY_FEE_INR;

/** Set true only for local QA — skips Razorpay. */
export const PALMISTRY_CHECKOUT_CONFIG = {
  bypassCheckoutForTesting: false,
} as const;

export function palmistryDeliverable(plan: PalmistryProPlan): DeliveryDeliverable {
  return plan === "vip" ? "video" : "report";
}

export function palmistryPriorityFeeInr(plan: PalmistryProPlan): number {
  return palmistryDeliverable(plan) === "video"
    ? PALMISTRY_VIDEO_PRIORITY_FEE_INR
    : PALMISTRY_REPORT_PRIORITY_FEE_INR;
}

export function palmistryPlanTotalInr(
  plan: PalmistryProPlan,
  priorityDelivery = false,
): number {
  const base = PALMISTRY_PRO_PLANS[plan].priceInr;
  return base + (priorityDelivery ? palmistryPriorityFeeInr(plan) : 0);
}

export function palmistryPlanEtaLabel(
  plan: PalmistryProPlan,
  priorityDelivery = false,
): string {
  if (priorityDelivery) {
    return plan === "vip"
      ? `Video on WhatsApp within ${PRIORITY_SLA_HOURS} hrs`
      : `Report in My Reports within ${PRIORITY_SLA_HOURS} hrs`;
  }
  return plan === "vip"
    ? `Video explanation · ${STANDARD_DELIVERY_ETA}`
    : STANDARD_DELIVERY_ETA;
}

export { STANDARD_DELIVERY_ETA };
