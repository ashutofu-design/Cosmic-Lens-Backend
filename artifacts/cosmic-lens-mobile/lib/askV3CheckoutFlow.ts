/**
 * Cosmic Intelligence V3 live pack checkout — Razorpay via /payment-webview.
 * Session is created only after payment succeeds.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import { ASK_V3_PACKS, createAskV3PackOrder, type AskV3PackId } from "@/lib/askV3Billing";

type AuthUser = { id: number; api_key?: string | null };

export async function startAskV3PackPayment(
  user: AuthUser | null | undefined,
  packId: AskV3PackId | string,
  preferredLanguage?: string,
): Promise<"paid_bypass" | "checkout" | "error"> {
  if (!user?.id || !user.api_key) {
    Alert.alert("Login required", "Please sign in to book a V3 live session.", [{ text: "OK" }]);
    return "error";
  }

  const pack = ASK_V3_PACKS.find((p) => p.id === String(packId)) ?? ASK_V3_PACKS[1];

  try {
    const order = await createAskV3PackOrder(user, pack.id, preferredLanguage);

    // Dev / Razorpay off — session already queued.
    if (order.already_entitled || order.payment_bypass || order.granted) {
      router.replace("/(tabs)/ask?resumeV3=1" as any);
      return "paid_bypass";
    }

    const sessionId = order.payment_session_id || order.razorpay_order_id;
    const keyId = order.razorpay_key_id || process.env.EXPO_PUBLIC_RAZORPAY_KEY_ID || "";
    if (!sessionId || !keyId || !order.purchase_id) {
      Alert.alert(
        "Payment error",
        "Could not start Razorpay checkout. Restart the API server and try again.",
      );
      return "error";
    }

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "ask_v3",
        cycle: "onetime",
        kind: "ask_v3_live",
        orderId: order.order_id || "",
        purchaseId: String(order.purchase_id),
        sessionId,
        razorpayKeyId: keyId,
        amountPaise: String(order.amount_paise ?? pack.price_inr * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? pack.price_inr),
        label: order.label || `V3 Live · ${pack.label}`,
        returnTo: "ask_v3",
      },
    });
    return "checkout";
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    if (msg.includes("razorpay_not_configured")) {
      Alert.alert("Payment unavailable", "Razorpay is not configured on the server yet.");
      return "error";
    }
    Alert.alert("Could not start payment", msg, [{ text: "OK" }]);
    return "error";
  }
}
