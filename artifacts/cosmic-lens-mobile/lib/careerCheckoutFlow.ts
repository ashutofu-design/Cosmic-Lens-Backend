/**
 * Career — ₹1 Razorpay (same as couple report). Life Map tap → payment page first.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  CAREER_UNLOCK_PRICE_INR,
  checkCareerAccess,
  createCareerUnlockOrder,
} from "@/lib/careerBilling";

type AuthUser = { id: number; api_key?: string | null };

/** Set true only for local QA — skips Razorpay. */
export const CAREER_CHECKOUT_CONFIG = {
  bypassCheckoutForTesting: false,
} as const;

/** Life Map → Career: check access or open career directly (no Razorpay gate in dev). */
export async function gateCareerLifeMapAccess(opts: {
  user: AuthUser | null | undefined;
}): Promise<void> {
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert(
      "Login required",
      "Please sign in to view Career Analysis.",
      [{ text: "OK" }],
    );
    return;
  }

  if (CAREER_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
    router.push("/career" as const);
    return;
  }

  try {
    const access = await checkCareerAccess(opts.user);
    if (access.entitled || !access.payment_required) {
      router.push("/career" as const);
      return;
    }
  } catch {
    // fall through to payment attempt
  }

  await startCareerPayment(opts.user);
}

/** Razorpay ₹1 — opens /payment-webview with session (like couple report). */
export async function startCareerPayment(
  user: AuthUser | null | undefined,
): Promise<void> {
  if (!user?.id || !user.api_key) {
    Alert.alert(
      "Login required",
      "Please sign in to unlock Career Analysis.",
      [{ text: "OK" }],
    );
    return;
  }

  try {
    const order = await createCareerUnlockOrder(user);
    if (order.already_entitled) {
      router.replace("/career" as const);
      return;
    }

    const sessionId = order.payment_session_id || order.razorpay_order_id;
    const keyId = order.razorpay_key_id || process.env.EXPO_PUBLIC_RAZORPAY_KEY_ID || "";
    if (!sessionId || !keyId) {
      Alert.alert(
        "Payment error",
        "Could not start Razorpay checkout. Restart the API server and try again.",
      );
      return;
    }

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "career",
        cycle: "onetime",
        kind: "career_unlock",
        orderId: order.order_id || "",
        sessionId,
        razorpayKeyId: keyId,
        amountPaise: String(
          order.amount_paise ?? (order.amount ?? CAREER_UNLOCK_PRICE_INR) * 100,
        ),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? CAREER_UNLOCK_PRICE_INR),
        label: order.label || "Career Analysis Unlock",
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    if (msg.includes("razorpay_not_configured")) {
      router.replace("/career" as const);
      return;
    }
    Alert.alert("Could not start payment", msg, [{ text: "OK" }]);
  }
}
