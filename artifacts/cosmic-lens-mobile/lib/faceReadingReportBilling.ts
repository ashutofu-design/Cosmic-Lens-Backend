/**

 * Face Reading PRO report — check entitlement + create Cashfree order.

 */

import { API_BASE } from "@/lib/apiConfig";



export const FACE_READING_PRO_PRICE_INR = 299;



export type FaceReadingReportCheckResult = {

  entitled: boolean;

  payment_required: boolean;

  cache_hit: boolean;

  already_paid: boolean;

  is_pro?: boolean;

  amount_inr: number;

  label: string;

  product: string;

  params_hash?: string;

};



function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {

  return {

    "Content-Type": "application/json",

    "X-User-Id": String(user.id),

    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),

  };

}



export async function checkFaceReadingReportEntitlement(

  user: { id: number; api_key?: string | null },

  sessionId: string,

  lang: string,

  age?: string,

  gender?: string,

): Promise<FaceReadingReportCheckResult> {

  const resp = await fetch(`${API_BASE}/api/face-reading-report/check`, {

    method: "POST",

    headers: authHeaders(user),

    body: JSON.stringify({ session_id: sessionId, lang, age, gender }),

  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {

    throw new Error((data as { error?: string }).error || `check failed ${resp.status}`);

  }

  return data as FaceReadingReportCheckResult;

}



export async function createFaceReadingReportOrder(

  user: { id: number; api_key?: string | null },

  sessionId: string,

  lang: string,

  age?: string,

  gender?: string,

): Promise<{

  already_entitled?: boolean;

  purchase_id?: number;

  payment_session_id?: string;

  payment_link?: string;

  order_id?: string;

  amount?: number;

  label?: string;

}> {

  const resp = await fetch(`${API_BASE}/api/face-reading-report/create-order`, {

    method: "POST",

    headers: authHeaders(user),

    body: JSON.stringify({ session_id: sessionId, lang, age, gender }),

  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {

    throw new Error((data as { error?: string }).error || `order failed ${resp.status}`);

  }

  return data as {

    already_entitled?: boolean;

    purchase_id?: number;

    payment_session_id?: string;

    payment_link?: string;

    order_id?: string;

    amount?: number;

    label?: string;

  };

}



export async function pollFaceReadingReportPurchase(

  user: { id: number; api_key?: string | null },

  purchaseId: number,

): Promise<{ status: string; entitled?: boolean }> {

  const resp = await fetch(`${API_BASE}/api/face-reading-report/purchase-status/${purchaseId}`, {

    headers: authHeaders(user),

  });

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {

    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);

  }

  return data as { status: string; entitled?: boolean };

}

