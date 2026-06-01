/**
 * Room photo scan pricing — client defaults (matches backend SKU_CATALOG).
 * Used when API catalog is missing or server not yet redeployed.
 */
export type RoomScanSkuSpec = {
  price: number;
  label: string;
  grants: "credits";
  credits: number;
};

export const ROOM_SCAN_SKUS = ["1room_99", "bundle_249", "bundle_399"] as const;
export type RoomScanSku = (typeof ROOM_SCAN_SKUS)[number];

export const ROOM_SCAN_CATALOG: Record<RoomScanSku, RoomScanSkuSpec> = {
  "1room_99": {
    price: 99,
    label: "1 Room Scan",
    grants: "credits",
    credits: 1,
  },
  bundle_249: {
    price: 249,
    label: "3 Room Scans",
    grants: "credits",
    credits: 3,
  },
  bundle_399: {
    price: 399,
    label: "5 Room Scans",
    grants: "credits",
    credits: 5,
  },
};

export function mergeRoomScanCatalog(
  api?: Record<string, Partial<RoomScanSkuSpec> & { grants?: string }> | null,
): Record<RoomScanSku, RoomScanSkuSpec> {
  const out = { ...ROOM_SCAN_CATALOG };
  if (!api) return out;
  for (const sku of ROOM_SCAN_SKUS) {
    const row = api[sku];
    if (row && typeof row.price === "number") {
      out[sku] = {
        ...out[sku],
        price: row.price,
        label: row.label || out[sku].label,
        credits: row.credits ?? out[sku].credits,
      };
    }
  }
  return out;
}
