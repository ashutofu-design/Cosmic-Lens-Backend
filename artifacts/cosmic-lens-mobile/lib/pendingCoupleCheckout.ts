/**
 * In-memory pending couple checkout (birth payloads too large for route params).
 */
import type { BirthData } from "@/types";

export type CoupleReportProduct = "milan_pro" | "love_reality_pro";

export type PendingCoupleCheckout = {
  product: CoupleReportProduct;
  p1: Record<string, unknown>;
  p2: Record<string, unknown>;
  lang: string;
  /** Set true after Cashfree success — parent screen resumes PDF flow */
  paidReady?: boolean;
};

let _pending: PendingCoupleCheckout | null = null;

export function setPendingCoupleCheckout(v: PendingCoupleCheckout): void {
  _pending = { ...v, paidReady: false };
}

export function getPendingCoupleCheckout(): PendingCoupleCheckout | null {
  return _pending;
}

export function markPendingCouplePaidReady(): void {
  if (_pending) _pending = { ..._pending, paidReady: true };
}

export function clearPendingCoupleCheckout(): void {
  _pending = null;
}

export function packBirthForApi(bd: BirthData, name: string, gender?: string): Record<string, unknown> {
  return {
    name: name || "Partner",
    gender: gender || undefined,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute ?? 0,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place || "",
  };
}
