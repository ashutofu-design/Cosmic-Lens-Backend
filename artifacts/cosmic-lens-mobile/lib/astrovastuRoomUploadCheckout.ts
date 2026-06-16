/**
 * Pay ₹199 per room → founder reviews photo in admin panel → manual report.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import {
  ROOM_EXPERT_UPLOAD_LABEL,
  ROOM_EXPERT_UPLOAD_PRICE_INR,
  ROOM_EXPERT_UPLOAD_SKU,
} from "@/lib/astrovastuRoomUploadPricing";
import { setPendingAstrovastuRoomUpload } from "@/lib/pendingAstrovastuRoomUpload";

export type RoomUploadCheckoutPayload = {
  room_type: string;
  direction: string;
  data_url: string;
  base64: string;
};

export async function startAstrovastuRoomUploadCheckout(opts: {
  user: { id: number; api_key: string };
  payload: RoomUploadCheckoutPayload;
}): Promise<void> {
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert("Login required", "Please sign in to pay and submit your room photo.");
    return;
  }

  setPendingAstrovastuRoomUpload({
    room_type: opts.payload.room_type,
    direction: opts.payload.direction,
    data_url: opts.payload.data_url,
    base64: opts.payload.base64,
  });

  try {
    const orderRes = await fetch(`${API_BASE}/api/astrovastu/create-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": opts.user.api_key },
      body: JSON.stringify({
        user_id: opts.user.id,
        sku: ROOM_EXPERT_UPLOAD_SKU,
        property_name: "",
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
        sku: ROOM_EXPERT_UPLOAD_SKU,
        purchaseId: String(order.purchase_id),
        orderId: order.order_id,
        sessionId: order.payment_session_id,
        razorpayKeyId: order.razorpay_key_id || "",
        amountPaise: String(order.amount_paise ?? (order.amount || ROOM_EXPERT_UPLOAD_PRICE_INR) * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount || ROOM_EXPERT_UPLOAD_PRICE_INR),
        label: order.label || ROOM_EXPERT_UPLOAD_LABEL,
        propertyName: "",
        returnTo: "astrovastu-pro",
      },
    });
  } catch (e: unknown) {
    Alert.alert("Network error", e instanceof Error ? e.message : "Try again.");
  }
}
