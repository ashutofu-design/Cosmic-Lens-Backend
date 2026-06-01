/**
 * Start Cashfree checkout for a room-scan SKU.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import {
  mergeRoomScanCatalog,
  ROOM_SCAN_CATALOG,
  type RoomScanSku,
} from "@/lib/astrovastuRoomPricing";

export async function purchaseRoomScanSku(opts: {
  user: { id: number; api_key: string };
  sku: RoomScanSku;
  catalog?: Record<string, { price?: number; label?: string }> | null;
}): Promise<void> {
  const merged = mergeRoomScanCatalog(opts.catalog);
  const spec = merged[opts.sku] ?? ROOM_SCAN_CATALOG[opts.sku];
  if (!spec) return;

  try {
    const orderRes = await fetch(`${API_BASE}/api/astrovastu/create-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": opts.user.api_key },
      body: JSON.stringify({ user_id: opts.user.id, sku: opts.sku, property_name: "" }),
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
        sku: opts.sku,
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
        propertyName: "",
      },
    });
  } catch (e: unknown) {
    Alert.alert("Network error", e instanceof Error ? e.message : "Try again.");
  }
}
