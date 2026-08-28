/**
 * In-memory pending Palmistry checkout (scans too large for route params).
 */

export type PendingPalmistryCheckout = {
  plan: "pdf" | "vip";
  urgent: boolean;
  purchaseId?: number;
  sessionId?: string;
  writingHand?: "left" | "right";
  contactValue?: string;
  lang?: "en" | "hn" | "hi";
  leftScan?: unknown;
  rightScan?: unknown;
  /** Set true after Razorpay success — parent resumes admin upload */
  paidReady?: boolean;
};

let _pending: PendingPalmistryCheckout | null = null;

export function setPendingPalmistryCheckout(v: PendingPalmistryCheckout): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingPalmistryCheckout(): PendingPalmistryCheckout | null {
  return _pending;
}

export function markPendingPalmistryPaidReady(): void {
  if (_pending) _pending = { ..._pending, paidReady: true };
}

export function clearPendingPalmistryCheckout(): void {
  _pending = null;
}
