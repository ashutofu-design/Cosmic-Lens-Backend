/**
 * Birth Time Rectification — check entitlement + create Razorpay order.
 */
import { API_BASE } from "@/lib/apiConfig";

export const BIRTH_TIME_RECTIFICATION_PRICE_INR = 999;

export type BirthTimeRectificationCheckResult = {
  entitled: boolean;
  payment_required: boolean;
  already_paid: boolean;
  amount_inr: number;
  label: string;
  product: string;
  params_hash?: string;
  payment_bypass?: boolean;
};

export type BirthTimeFormParams = {
  full_name: string;
  gender: string;
  dob: string;
  approx_tob: string;
  birth_place: string;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function checkBirthTimeRectificationEntitlement(
  user: { id: number; api_key?: string | null },
  params: BirthTimeFormParams,
): Promise<BirthTimeRectificationCheckResult> {
  const resp = await fetch(`${API_BASE}/api/birth-time-rectification/check`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify(params),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `check failed ${resp.status}`);
  }
  return data as BirthTimeRectificationCheckResult;
}

export async function createBirthTimeRectificationOrder(
  user: { id: number; api_key?: string | null },
  params: BirthTimeFormParams,
): Promise<{
  already_entitled?: boolean;
  purchase_id?: number;
  payment_session_id?: string;
  payment_link?: string;
  order_id?: string;
  amount?: number;
  amount_paise?: number;
  label?: string;
  razorpay_key_id?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}> {
  const resp = await fetch(`${API_BASE}/api/birth-time-rectification/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify(params),
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
    amount_paise?: number;
    label?: string;
    razorpay_key_id?: string;
    customer_name?: string;
    customer_email?: string;
    customer_phone?: string;
  };
}

export async function pollBirthTimeRectificationPurchase(
  user: { id: number; api_key?: string | null },
  purchaseId: number,
): Promise<{ status: string; entitled?: boolean }> {
  const resp = await fetch(
    `${API_BASE}/api/birth-time-rectification/purchase-status/${purchaseId}`,
    { headers: authHeaders(user) },
  );
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);
  }
  return data as { status: string; entitled?: boolean };
}
