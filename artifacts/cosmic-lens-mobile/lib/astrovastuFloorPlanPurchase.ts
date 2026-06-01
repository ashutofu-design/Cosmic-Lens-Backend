import { router } from "expo-router";
import { Alert } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import type { PlanKind } from "@/lib/planKind";
import {
  PLAN_KIND_TO_FLOOR_SKU,
  priceForPlanKind,
  type FloorPlanSku,
} from "@/lib/astrovastuFloorPlanPricing";

export async function purchaseFloorPlanSku(opts: {
  user: { id: number; api_key: string };
  planKind: PlanKind;
  propertyName?: string;
  catalog?: Record<string, { price?: number; label?: string }> | null;
}): Promise<void> {
  const sku: FloorPlanSku = PLAN_KIND_TO_FLOOR_SKU[opts.planKind];
  const spec = priceForPlanKind(opts.planKind, opts.catalog);

  try {
    const orderRes = await fetch(`${API_BASE}/api/astrovastu/create-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": opts.user.api_key },
      body: JSON.stringify({
        user_id: opts.user.id,
        sku,
        property_name: opts.propertyName || "",
      }),
    });
    const order = await orderRes.json();
    if (!orderRes.ok || !order?.payment_session_id) {
      Alert.alert(
        "Couldn't start payment",
        order?.detail || order?.message || order?.error || "Try again.",
      );
      return;
    }

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "astrovastu",
        cycle: "onetime",
        kind: "astrovastu",
        sku,
        purchaseId: String(order.purchase_id),
        orderId: order.order_id,
        sessionId: order.payment_session_id,
        razorpayKeyId: order.razorpay_key_id || "",
        amountPaise: String(order.amount_paise ?? (order.amount || spec.price) * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount || spec.price),
        label: spec.label,
        propertyName: opts.propertyName || "",
      },
    });
  } catch (e: unknown) {
    Alert.alert("Network error", e instanceof Error ? e.message : "Try again.");
  }
}
