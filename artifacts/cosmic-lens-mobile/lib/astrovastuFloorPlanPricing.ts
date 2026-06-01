/**
 * Complete floor plan scan pricing by plan type (matches backend SKU_CATALOG).
 */
import type { PlanKind } from "@/lib/planKind";

export type FloorPlanSku =
  | "home_floor_799"
  | "shop_floor_1499"
  | "office_floor_2499"
  | "factory_floor_4999";

export const PLAN_KIND_TO_FLOOR_SKU: Record<PlanKind, FloorPlanSku> = {
  home: "home_floor_799",
  shop: "shop_floor_1499",
  office: "office_floor_2499",
  factory: "factory_floor_4999",
};

export type FloorPlanSkuSpec = {
  price: number;
  label: string;
  plan_kind: PlanKind;
};

export const FLOOR_PLAN_CATALOG: Record<FloorPlanSku, FloorPlanSkuSpec> = {
  home_floor_799: {
    price: 799,
    label: "Home · Full Floor Plan",
    plan_kind: "home",
  },
  shop_floor_1499: {
    price: 1499,
    label: "Shop · Full Floor Plan",
    plan_kind: "shop",
  },
  office_floor_2499: {
    price: 2499,
    label: "Office · Full Floor Plan",
    plan_kind: "office",
  },
  factory_floor_4999: {
    price: 4999,
    label: "Factory · Full Floor Plan",
    plan_kind: "factory",
  },
};

export function priceForPlanKind(
  kind: PlanKind,
  catalog?: Record<string, Partial<FloorPlanSkuSpec & { grants?: string }> | null>,
): FloorPlanSkuSpec {
  const sku = PLAN_KIND_TO_FLOOR_SKU[kind];
  const row = catalog?.[sku];
  const base = FLOOR_PLAN_CATALOG[sku];
  if (row && typeof row.price === "number") {
    return {
      ...base,
      price: row.price,
      label: row.label || base.label,
    };
  }
  return base;
}

export function mergeFloorPlanCatalog(
  api?: Record<string, Partial<FloorPlanSkuSpec & { grants?: string }> | null>,
): Record<FloorPlanSku, FloorPlanSkuSpec> {
  const out = { ...FLOOR_PLAN_CATALOG };
  if (!api) return out;
  for (const sku of Object.keys(PLAN_KIND_TO_FLOOR_SKU) as FloorPlanSku[]) {
    const row = api[sku];
    if (row && typeof row.price === "number") {
      out[sku] = { ...out[sku], price: row.price, label: row.label || out[sku].label };
    }
  }
  return out;
}
