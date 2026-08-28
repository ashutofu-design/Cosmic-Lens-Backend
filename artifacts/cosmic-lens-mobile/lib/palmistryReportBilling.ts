/**
 * Palmistry Pro — check entitlement + create Razorpay order.
 */
import { API_BASE } from "@/lib/apiConfig";

export type PalmistryReportCheckResult = {
  entitled: boolean;
  payment_required: boolean;
  already_paid: boolean;
  amount_inr: number;
  label: string;
  product: string;
  purchase_id?: number | null;
  plan?: string;
  urgent?: boolean;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function checkPalmistryReportEntitlement(
  user: { id: number; api_key?: string | null },
  opts: { plan: "pdf" | "vip"; urgent: boolean; sessionId?: string },
): Promise<PalmistryReportCheckResult> {
  const resp = await fetch(`${API_BASE}/api/palmistry-report/check`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      plan: opts.plan,
      urgent: opts.urgent,
      session_id: opts.sessionId || "",
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `check failed ${resp.status}`);
  }
  return data as PalmistryReportCheckResult;
}

export async function createPalmistryReportOrder(
  user: { id: number; api_key?: string | null },
  opts: { plan: "pdf" | "vip"; urgent: boolean; sessionId?: string },
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
  const resp = await fetch(`${API_BASE}/api/palmistry-report/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      plan: opts.plan,
      urgent: opts.urgent,
      session_id: opts.sessionId || "",
    }),
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

export async function pollPalmistryReportPurchase(
  user: { id: number; api_key?: string | null },
  purchaseId: number,
): Promise<{ status: string; entitled?: boolean }> {
  const resp = await fetch(`${API_BASE}/api/palmistry-report/purchase-status/${purchaseId}`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);
  }
  return data as { status: string; entitled?: boolean };
}
