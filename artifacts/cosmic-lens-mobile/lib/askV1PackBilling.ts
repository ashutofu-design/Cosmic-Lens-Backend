/** Cosmic Intelligence V1 — question pack catalog + API helpers. */
import { API_BASE } from "@/lib/apiConfig";

export type AskV1PackId = "starter" | "popular" | "power";

export type AskV1Pack = {
  id: AskV1PackId;
  price_inr: number;
  questions: number;
  days: number;
  label: string;
  feel: string;
  badge: "popular" | "best" | null;
};

/** Locked catalog (must match api-server/ask_v1_billing.py). */
export const ASK_V1_PACKS: AskV1Pack[] = [
  {
    id: "starter",
    price_inr: 49,
    questions: 8,
    days: 7,
    label: "Starter",
    feel: "Try Cosmic Intelligence",
    badge: null,
  },
  {
    id: "popular",
    price_inr: 99,
    questions: 15,
    days: 14,
    label: "Popular",
    feel: "Most popular for daily clarity",
    badge: "popular",
  },
  {
    id: "power",
    price_inr: 299,
    questions: 45,
    days: 30,
    label: "Power",
    feel: "Best value for deep seekers",
    badge: "best",
  },
];

export type AskV1Wallet = {
  active: boolean;
  unlimited?: boolean;
  questions_left: number;
  questions_total?: number;
  questions_used?: number;
  free_questions_left?: number;
  free_questions_used?: number;
  expires_at?: string | null;
  pack_id?: string;
  packs?: AskV1Pack[];
  payment_bypass?: boolean;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function fetchAskV1Wallet(
  user: { id: number; api_key?: string | null },
): Promise<AskV1Wallet> {
  const resp = await fetch(`${API_BASE}/api/ask-v1/wallet`, {
    headers: authHeaders(user),
  });
  const data = (await resp.json().catch(() => ({}))) as AskV1Wallet & {
    ok?: boolean;
    error?: string;
    wallet?: AskV1Wallet;
  };
  if (!resp.ok) {
    throw new Error(data.error || `wallet ${resp.status}`);
  }
  // Some proxies wrap payload; prefer flat wallet fields.
  if (data.wallet && typeof data.wallet === "object") {
    return { ...data, ...data.wallet } as AskV1Wallet;
  }
  return data as AskV1Wallet;
}

export async function createAskV1PackOrder(
  user: { id: number; api_key?: string | null },
  packId: AskV1PackId,
  referralCode?: string,
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
  questions_left?: number;
  active?: boolean;
}> {
  const resp = await fetch(`${API_BASE}/api/ask-v1/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      pack_id: packId,
      ...(referralCode?.trim() ? { referral_code: referralCode.trim() } : {}),
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const d = data as { error?: string; detail?: string };
    throw new Error(d.detail || d.error || `order failed ${resp.status}`);
  }
  return data as any;
}

export async function pollAskV1PurchaseStatus(
  user: { id: number; api_key?: string | null },
  purchaseId: number,
): Promise<{
  status: string;
  granted?: boolean;
  paid?: boolean;
  entitled?: boolean;
  active?: boolean;
  questions_left?: number;
}> {
  const resp = await fetch(
    `${API_BASE}/api/ask-v1/purchase-status/${purchaseId}`,
    { headers: authHeaders(user) },
  );
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status ${resp.status}`);
  }
  return data as any;
}

export function formatAskV1Expiry(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

/** Longer expiry for plan card — e.g. 28 Jul 2026 */
export function formatAskV1ExpiryLong(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
