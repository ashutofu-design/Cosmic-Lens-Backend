/** In-memory pending paid floor plan scan (too large for route params). */

import type { SmartScanUploadValue } from "@/components/SmartScanUpload";

export type PendingAstrovastuFloorPlan = {
  floor_plan_upload: SmartScanUploadValue;
  purchase_id?: number;
  /** Set after Cashfree success — parent auto-runs scan */
  paidReady?: boolean;
};

let _pending: PendingAstrovastuFloorPlan | null = null;

export function setPendingAstrovastuFloorPlan(v: PendingAstrovastuFloorPlan): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingAstrovastuFloorPlan(): PendingAstrovastuFloorPlan | null {
  return _pending;
}

export function markPendingAstrovastuFloorPaidReady(purchaseId: number): void {
  if (_pending) _pending = { ..._pending, paidReady: true, purchase_id: purchaseId };
}

export function clearPendingAstrovastuFloorPlan(): void {
  _pending = null;
}

export function consumeAstrovastuFloorPaidReady(): boolean {
  if (!_pending?.paidReady) return false;
  return true;
}

