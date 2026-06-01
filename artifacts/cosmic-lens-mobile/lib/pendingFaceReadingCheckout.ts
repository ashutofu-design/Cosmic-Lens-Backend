/**

 * Pending Face Reading PRO checkout (session too large for route params).

 */



export type PendingFaceReadingCheckout = {

  sessionId: string;

  lang: string;

  age?: string;

  gender?: string;

  paidReady?: boolean;

};



let _pending: PendingFaceReadingCheckout | null = null;



export function setPendingFaceReadingCheckout(v: PendingFaceReadingCheckout): void {

  _pending = { ...v, paidReady: false };

}



export function getPendingFaceReadingCheckout(): PendingFaceReadingCheckout | null {

  return _pending;

}



export function markPendingFaceReadingPaidReady(): void {

  if (_pending) _pending = { ..._pending, paidReady: true };

}



export function clearPendingFaceReadingCheckout(): void {

  _pending = null;

}

