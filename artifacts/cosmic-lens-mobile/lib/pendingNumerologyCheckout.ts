/**
 * In-memory pending Life Mastery checkout (inputs too large for route params).
 */

export type PendingNumerologyCheckout = {
  params: Record<string, unknown>;
  lang: string;
  purchaseId?: number;
  /** Set true after Cashfree success — parent screen resumes founder-order flow */
  paidReady?: boolean;
  urgent?: boolean;
  deliverable?: "report" | "video";
  contactMethod?: "whatsapp";
  contactValue?: string;
};

let _pending: PendingNumerologyCheckout | null = null;

export function setPendingNumerologyCheckout(v: PendingNumerologyCheckout): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingNumerologyCheckout(): PendingNumerologyCheckout | null {
  return _pending;
}

export function markPendingNumerologyPaidReady(): void {
  if (_pending) _pending = { ..._pending, paidReady: true };
}

export function clearPendingNumerologyCheckout(): void {
  _pending = null;
}
