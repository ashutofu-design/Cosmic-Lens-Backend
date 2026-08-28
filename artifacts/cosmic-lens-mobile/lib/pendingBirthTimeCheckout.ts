/**
 * In-memory pending Birth Time Rectification checkout (form too large for route params).
 */

export type BirthTimeSubmitPayload = {
  full_name: string;
  gender: string;
  dob: string;
  approx_tob: string;
  birth_place: string;
  milestone_events: Array<{
    id: string;
    label: string;
    month: string;
    year: string;
    month_year: string;
    impact: string;
  }>;
  last_15y_events_text: string;
};

export type PendingBirthTimeCheckout = {
  params: BirthTimeSubmitPayload;
  purchaseId?: number;
  /** Set true after Razorpay success — screen resumes submit */
  paidReady?: boolean;
};

let _pending: PendingBirthTimeCheckout | null = null;

export function setPendingBirthTimeCheckout(v: PendingBirthTimeCheckout): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingBirthTimeCheckout(): PendingBirthTimeCheckout | null {
  return _pending;
}

export function markPendingBirthTimePaidReady(): void {
  if (_pending) _pending = { ..._pending, paidReady: true };
}

export function clearPendingBirthTimeCheckout(): void {
  _pending = null;
}
