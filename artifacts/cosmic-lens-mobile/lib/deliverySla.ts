/** Shared delivery SLAs for founder-prepared reports and videos. */

export const STANDARD_DELIVERY_ETA = "4–6 business days" as const;
export const PRIORITY_SLA_HOURS = 12 as const;

export const REPORT_PRIORITY_FEE_INR = 149 as const;
export const VIDEO_PRIORITY_FEE_INR = 299 as const;

export type DeliveryDeliverable = "report" | "video";

export function priorityFeeInr(deliverable: DeliveryDeliverable = "report"): number {
  return deliverable === "video" ? VIDEO_PRIORITY_FEE_INR : REPORT_PRIORITY_FEE_INR;
}

/** Shown before payment whenever Priority is offered. */
export const PRIORITY_GUARANTEE =
  "12-hour Priority Guarantee — If we miss the 12-hour delivery window, your Priority fee is 100% refunded." as const;
