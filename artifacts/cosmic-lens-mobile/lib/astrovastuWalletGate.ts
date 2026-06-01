import type { PlanKind } from "@/lib/planKind";
import type { WalletStatus } from "@/components/AstroVastuWallet";

/** ₹99 room-photo credits + Pro / unlock / monthly quota. */
export function canRunRoomPhotoProScan(s: WalletStatus | null): boolean {
  if (!s) return false;
  if (s.is_pro) return true;
  if ((s.unlocked_properties?.length ?? 0) > 0) return true;
  if ((s.room_credits ?? 0) > 0) return true;
  const lim = s.monthly_pro_limit;
  if (lim === -1) return true;
  if (lim > 0 && (s.monthly_pro_used ?? 0) < lim) return true;
  return false;
}

/** Full floor-plan scan — room-photo credits do NOT count. */
export function canRunWholePlanProScan(
  s: WalletStatus | null,
  planKind?: PlanKind | null,
): boolean {
  if (!s) return false;
  if (s.is_pro) return true;
  if ((s.unlocked_properties?.length ?? 0) > 0) return true;
  if (planKind && (s.floor_scan_wallet?.[planKind] ?? 0) > 0) return true;
  const lim = s.monthly_pro_limit;
  if (lim === -1) return true;
  if (lim > 0 && (s.monthly_pro_used ?? 0) < lim) return true;
  return false;
}

export function floorScanCreditsFor(
  s: WalletStatus | null,
  planKind: PlanKind,
): number {
  return s?.floor_scan_wallet?.[planKind] ?? 0;
}

export function hasRoomPhotoCreditsOnly(s: WalletStatus | null): boolean {
  if (!s || s.is_pro) return false;
  if ((s.unlocked_properties?.length ?? 0) > 0) return false;
  if ((s.room_credits ?? 0) <= 0) return false;
  return !canRunWholePlanProScan(s);
}
