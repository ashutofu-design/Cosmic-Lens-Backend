/**
 * In-memory pending Life Mastery checkout (inputs too large for route params).
 */

export type PendingNumerologyCheckout = {
  params: Record<string, unknown>;
  lang: string;
  /** Set true after Cashfree success — parent screen resumes PDF flow */
  paidReady?: boolean;
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
