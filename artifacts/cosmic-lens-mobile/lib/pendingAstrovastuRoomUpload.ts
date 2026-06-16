/** In-memory pending paid room photo upload (too large for route params). */

export type PendingAstrovastuRoomUpload = {
  room_type: string;
  direction: string;
  data_url: string;
  base64: string;
  purchase_id?: number;
  /** Set after Cashfree success — parent submits to founder queue */
  paidReady?: boolean;
};

let _pending: PendingAstrovastuRoomUpload | null = null;

export function setPendingAstrovastuRoomUpload(v: PendingAstrovastuRoomUpload): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingAstrovastuRoomUpload(): PendingAstrovastuRoomUpload | null {
  return _pending;
}

export function markPendingAstrovastuRoomPaidReady(purchaseId: number): void {
  if (_pending) _pending = { ..._pending, paidReady: true, purchase_id: purchaseId };
}

export function clearPendingAstrovastuRoomUpload(): void {
  _pending = null;
}

export function consumeAstrovastuRoomPaidReady(): boolean {
  if (!_pending?.paidReady) return false;
  return true;
}
