/**
 * Couple report pay-per-couple — check entitlement + create Cashfree order.
 */
import { API_BASE } from "@/lib/apiConfig";

export type CoupleReportProduct = "milan_pro" | "love_reality_pro";

export type CoupleCheckResult = {
  entitled: boolean;
  payment_required: boolean;
  cache_hit: boolean;
  already_paid: boolean;
  amount_inr: number;
  label: string;
  product: string;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function checkCoupleReportEntitlement(
  user: { id: number; api_key?: string | null },
  product: CoupleReportProduct,
  p1: Record<string, unknown>,
  p2: Record<string, unknown>,
  lang: string,
): Promise<CoupleCheckResult> {
  const resp = await fetch(`${API_BASE}/api/couple-report/check`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({ product, p1, p2, lang }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `check failed ${resp.status}`);
  }
  return data as CoupleCheckResult;
}

export async function createCoupleReportOrder(
  user: { id: number; api_key?: string | null },
  product: CoupleReportProduct,
  p1: Record<string, unknown>,
  p2: Record<string, unknown>,
  lang: string,
): Promise<{
  already_entitled?: boolean;
  purchase_id?: number;
  payment_session_id?: string;
  payment_link?: string;
  order_id?: string;
  amount?: number;
}> {
  const resp = await fetch(`${API_BASE}/api/couple-report/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({ product, p1, p2, lang }),
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
  };
}

export async function pollCoupleReportPurchase(
  user: { id: number; api_key?: string | null },
  purchaseId: number,
): Promise<{ status: string; entitled?: boolean }> {
  const resp = await fetch(`${API_BASE}/api/couple-report/purchase-status/${purchaseId}`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);
  }
  return data as { status: string; entitled?: boolean };
}
