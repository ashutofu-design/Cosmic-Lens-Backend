/**
 * Business Vastu — room-photo vs full-PDF pricing (must match server).
 */
import { API_BASE } from "@/lib/apiConfig";

export type BusinessVastuType = "shop" | "office" | "factory";
export type BusinessVastuUploadMode = "photos" | "pdf";

/** Per-room photo rate (Razorpay when user submits photos, no PDF). */
export const BUSINESS_VASTU_ROOM_PHOTO_PRICES: Record<BusinessVastuType, number> = {
  shop: 399,
  office: 499,
  factory: 999,
};

/** Full floor-plan PDF rate (Razorpay when PDF is uploaded). */
export const BUSINESS_VASTU_PDF_PRICES: Record<BusinessVastuType, number> = {
  shop: 2999,
  office: 6999,
  factory: 14999,
};

export const BUSINESS_VASTU_PRIORITY_FEE_INR = 149;

/** @deprecated legacy package sticker — prefer room/PDF quote */
export const BUSINESS_VASTU_PRICES: Record<BusinessVastuType, number> = {
  shop: 999,
  office: 1499,
  factory: 2999,
};

export type BusinessVastuQuoteInput = {
  businessType: BusinessVastuType;
  priorityDelivery?: boolean;
  hasPdf?: boolean;
  roomCount?: number;
};

export function businessVastuUploadMode(opts: {
  hasPdf?: boolean;
  roomCount?: number;
}): BusinessVastuUploadMode {
  return opts.hasPdf ? "pdf" : "photos";
}

/** Exact Razorpay total — keep in sync with server business_vastu_billing.amount_for */
export function businessVastuOrderTotalInr(opts: BusinessVastuQuoteInput): number {
  const type = opts.businessType;
  const urgent = !!opts.priorityDelivery;
  let base: number;
  if (opts.hasPdf) {
    base = BUSINESS_VASTU_PDF_PRICES[type] ?? BUSINESS_VASTU_PDF_PRICES.shop;
  } else {
    const per = BUSINESS_VASTU_ROOM_PHOTO_PRICES[type] ?? BUSINESS_VASTU_ROOM_PHOTO_PRICES.shop;
    const n = Math.max(1, Math.min(6, Math.floor(opts.roomCount || 1)));
    base = per * n;
  }
  return base + (urgent ? BUSINESS_VASTU_PRIORITY_FEE_INR : 0);
}

export type BusinessVastuCheckResult = {
  entitled: boolean;
  payment_required: boolean;
  already_paid: boolean;
  amount_inr: number;
  label: string;
  product: string;
  params_hash?: string;
  payment_bypass?: boolean;
};

export type BusinessVastuOrderOpts = {
  business_type: BusinessVastuType;
  property_name: string;
  urgent?: boolean;
  upload_mode?: BusinessVastuUploadMode;
  room_count?: number;
};

function authHeaders(user: { id: number; api_key?: string | null }): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

export async function checkBusinessVastuEntitlement(
  user: { id: number; api_key?: string | null },
  opts: BusinessVastuOrderOpts,
): Promise<BusinessVastuCheckResult> {
  const resp = await fetch(`${API_BASE}/api/business-vastu/check`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify(opts),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((data as { error?: string }).error || `check failed ${resp.status}`);
  }
  return data as BusinessVastuCheckResult;
}

export async function createBusinessVastuOrder(
  user: { id: number; api_key?: string | null },
  opts: BusinessVastuOrderOpts,
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
  const resp = await fetch(`${API_BASE}/api/business-vastu/create-order`, {
    method: "POST",
    headers: authHeaders(user),
    body: JSON.stringify(opts),
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
