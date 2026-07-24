/** Cosmic Intelligence V3 — live pack catalog + create-order API. */
import { API_BASE } from "@/lib/apiConfig";

export type AskV3PackId = "15" | "30" | "45" | "60";

export type AskV3Pack = {
  id: AskV3PackId;
  price_inr: number;
  minutes: number;
  label: string;
};

/** Locked catalog (must match api-server/ask_v3_billing.py). */
export const ASK_V3_PACKS: AskV3Pack[] = [
  { id: "15", price_inr: 399, minutes: 15, label: "15 min" },
  { id: "30", price_inr: 699, minutes: 30, label: "30 min" },
  { id: "45", price_inr: 999, minutes: 45, label: "45 min" },
  { id: "60", price_inr: 1299, minutes: 60, label: "60 min" },
];

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function createAskV3PackOrder(
  user: { id: number; api_key?: string | null },
  packId: AskV3PackId | string,
  preferredLanguage?: string,
): Promise<{
  already_entitled?: boolean;
  payment_required?: boolean;
  payment_bypass?: boolean;
  payment_session_id?: string;
  razorpay_key_id?: string;
  razorpay_order_id?: string;
  amount_paise?: number;
  order_id?: string;
  purchase_id?: number;
  amount?: number;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  label?: string;
  pack_id?: string;
  session_id?: string;
  granted?: boolean;
  entitled?: boolean;
  minutes?: number;
}> {
  const resp = await fetch(`${API_BASE}/api/ask-v3/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      pack_id: packId,
      ...(preferredLanguage ? { preferred_language: preferredLanguage } : {}),
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const d = data as { error?: string; detail?: string; message?: string };
    throw new Error(d.detail || d.message || d.error || `order failed ${resp.status}`);
  }
  return data as any;
}

export async function fetchAskV3PurchaseStatus(
  user: { id: number; api_key?: string | null },
  purchaseId: number,
): Promise<{
  status?: string;
  granted?: boolean;
  paid?: boolean;
  entitled?: boolean;
  session_id?: string;
}> {
  const resp = await fetch(`${API_BASE}/api/ask-v3/purchase-status/${purchaseId}`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status ${resp.status}`);
  }
  return data as any;
}
