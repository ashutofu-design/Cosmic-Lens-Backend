/**
 * Pay ₹199 per room → founder reviews photo in admin panel → manual report.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import { API_BASE } from "@/lib/apiConfig";
import { submitAstrovastuRoomHumanOrder } from "@/lib/astrovastuHumanOrder";
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

export type RoomUploadCheckoutResult =
  | "submitted" // bypass mode: photo already in founder queue
  | "payment_started" // pushed to payment webview
  | "failed";

export async function startAstrovastuRoomUploadCheckout(opts: {
  user: { id: number; api_key: string };
  payload: RoomUploadCheckoutPayload;
}): Promise<RoomUploadCheckoutResult> {
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert("Login required", "Please sign in to pay and submit your room photo.");
    return "failed";
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
    const order = await orderRes.json().catch(() => ({} as Record<string, unknown>));

    // Payment gateway off (bypass mode) → submit photo directly to the
    // founder queue. UI stays "₹199"; paid flow resumes automatically once
    // Razorpay keys are configured on the server again.
    if (orderRes.status === 503 || order?.error === "razorpay_not_configured") {
      const ok = await submitAstrovastuRoomHumanOrder({
        user: opts.user,
        purchaseId: 0,
      });
      return ok ? "submitted" : "failed";
    }

    if (!orderRes.ok || !order?.payment_session_id) {
      Alert.alert(
        "Couldn't start payment",
        order?.detail || order?.message || order?.error || "Try again.",
      );
      return "failed";
    }

    // Upload the photo as a server-side draft BEFORE payment. The server
    // auto-promotes it to the founder queue once the purchase turns paid,
    // so delivery no longer depends on the app surviving the payment
    // round-trip (app kill / reload used to lose the in-memory photo).
    try {
      await fetch(`${API_BASE}/api/astrovastu/room-upload-draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": opts.user.api_key },
        body: JSON.stringify({
          user_id: opts.user.id,
          purchase_id: order.purchase_id,
          room_type: opts.payload.room_type,
          direction: opts.payload.direction,
          data_url: opts.payload.data_url,
        }),
      });
    } catch {
      // Non-fatal: post-payment submit remains as fallback.
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
    return "payment_started";
  } catch (e: unknown) {
    Alert.alert("Network error", e instanceof Error ? e.message : "Try again.");
    return "failed";
  }
}
