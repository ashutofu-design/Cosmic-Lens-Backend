import { router } from "expo-router";
import { Alert } from "react-native";

import { createGemstoneOrder } from "@/lib/gemstoneBilling";
import { getGemstoneSkuPricing } from "@/lib/gemstonePricing";

type AuthUser = { id: number; api_key?: string | null };

export async function startGemstoneCheckout(opts: {
  user: AuthUser | null | undefined;
  sku: string;
  referralCode?: string;
  label?: string;
}): Promise<void> {
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert("Login required", "Please sign in to buy gemstones.", [{ text: "OK" }]);
    return;
  }

  const shop = getGemstoneSkuPricing(opts.sku);
  const label = opts.label || (shop
    ? `Ceylon Pukhraj — ${shop.ratti} Ratti`
    : "Gemstone");

  try {
    const order = await createGemstoneOrder(opts.user, opts.sku, opts.referralCode);
    const purchaseId = order.purchase_id ?? order.gemstone_order_id;
    const sessionId = order.payment_session_id || order.razorpay_order_id;
    const keyId = order.razorpay_key_id || process.env.EXPO_PUBLIC_RAZORPAY_KEY_ID || "";

    if (!purchaseId || !sessionId || !order.order_id) {
      Alert.alert("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "gemstone",
        cycle: "onetime",
        kind: "gemstone",
        purchaseId: String(purchaseId),
        orderId: order.order_id,
        sessionId,
        razorpayKeyId: keyId,
        amountPaise: String(order.amount_paise ?? (order.amount ?? 0) * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? 0),
        label,
        returnTo: "/gemstones",
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    if (msg === "self_referral_not_allowed") {
      Alert.alert("Invalid code", "You cannot use your own referral code.");
      return;
    }
    if (msg.includes("razorpay_not_configured")) {
      Alert.alert("Payments unavailable", "Payment gateway is not configured yet. Try again later.");
      return;
    }
    Alert.alert("Could not start payment", msg, [{ text: "OK" }]);
  }
}
