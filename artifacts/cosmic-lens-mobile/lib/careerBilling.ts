import { API_BASE } from "@/lib/apiConfig";

export const CAREER_UNLOCK_PRICE_INR = 1;

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export type CareerAccessResult = {
  entitled: boolean;
  payment_required: boolean;
  amount_inr: number;
  label: string;
  career_unlocked?: boolean;
  payment_bypass?: boolean;
};

export async function checkCareerAccess(
  user: { id: number; api_key?: string | null },
): Promise<CareerAccessResult> {
  const resp = await fetch(`${API_BASE}/api/career/check`, {
    method: "GET",
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const d = data as { error?: string; detail?: string };
    throw new Error(d.detail || d.error || `check failed ${resp.status}`);
  }
  return data as CareerAccessResult;
}

export async function createCareerUnlockOrder(
  user: { id: number; api_key?: string | null },
): Promise<{
  already_entitled?: boolean;
  payment_session_id?: string;
  razorpay_key_id?: string;
  razorpay_order_id?: string;
  amount_paise?: number;
  order_id?: string;
  amount?: number;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  label?: string;
}> {
  const resp = await fetch(`${API_BASE}/api/career/create-order`, {
    method: "POST",
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const d = data as { error?: string; detail?: string };
    const msg = d.detail || d.error || `order failed ${resp.status}`;
    throw new Error(msg);
  }
  return data as {
    already_entitled?: boolean;
    payment_session_id?: string;
    razorpay_key_id?: string;
    amount_paise?: number;
    order_id?: string;
    amount?: number;
    customer_name?: string;
    customer_email?: string;
    customer_phone?: string;
    label?: string;
  };
}

export async function pollCareerAccess(
  user: { id: number; api_key?: string | null },
  orderId?: string,
): Promise<CareerAccessResult & { order_id?: string | null; paid_at?: string | null }> {
  const q = orderId ? `?order_id=${encodeURIComponent(orderId)}` : "";
  const resp = await fetch(`${API_BASE}/api/career/access-status${q}`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);
  }
  return data as CareerAccessResult & { order_id?: string | null; paid_at?: string | null };
}
