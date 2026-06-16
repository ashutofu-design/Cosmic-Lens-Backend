import { API_BASE } from "@/lib/apiConfig";

export type GemstoneQuote = {
  sku: string;
  label?: string;
  mrp_inr: number;
  discount_inr: number;
  discount_type: "self" | "referral";
  amount_inr: number;
  referral_code_used?: string | null;
  referrer_user_id?: number | null;
  referrer_reward_inr?: number;
  referrer_payout_note?: string | null;
};

export type GemstoneOrderResponse = {
  order_id?: string;
  payment_session_id?: string;
  razorpay_order_id?: string;
  razorpay_key_id?: string;
  amount?: number;
  amount_paise?: number;
  purchase_id?: number;
  gemstone_order_id?: number;
  label?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  error?: string;
};

export type MyReferralInfo = {
  referral_code: string;
  reward_inr?: number;
  buyer_discount_inr?: number;
  share_message: string;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function fetchGemstoneQuote(
  user: { id: number; api_key?: string | null },
  sku: string,
  referralCode?: string,
): Promise<GemstoneQuote> {
  const resp = await fetch(`${API_BASE}/api/gemstone/quote`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      sku,
      referral_code: referralCode?.trim() || undefined,
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `quote failed ${resp.status}`);
  }
  return data as GemstoneQuote;
}

export async function createGemstoneOrder(
  user: { id: number; api_key?: string | null },
  sku: string,
  referralCode?: string,
): Promise<GemstoneOrderResponse> {
  const resp = await fetch(`${API_BASE}/api/gemstone/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify({
      sku,
      referral_code: referralCode?.trim() || undefined,
    }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `create-order failed ${resp.status}`);
  }
  return data as GemstoneOrderResponse;
}

export async function fetchMyReferralCode(
  user: { id: number; api_key?: string | null },
): Promise<MyReferralInfo> {
  const resp = await fetch(`${API_BASE}/api/gemstone/my-referral`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `referral fetch failed ${resp.status}`);
  }
  return data as MyReferralInfo;
}

export async function pollGemstonePurchaseStatus(
  user: { id: number; api_key?: string | null },
  orderRowId: number,
): Promise<{ paid: boolean; granted: boolean; status: string }> {
  const resp = await fetch(`${API_BASE}/api/gemstone/purchase-status/${orderRowId}`, {
    headers: authHeaders(user),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `status failed ${resp.status}`);
  }
  return {
    paid: !!(data as { paid?: boolean }).paid,
    granted: !!(data as { granted?: boolean }).granted,
    status: String((data as { status?: string }).status || ""),
  };
}
