/**
 * Birth Time Rectification: validate → check entitlement → Razorpay or submit.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  BIRTH_TIME_RECTIFICATION_PRICE_INR,
  checkBirthTimeRectificationEntitlement,
  createBirthTimeRectificationOrder,
} from "@/lib/birthTimeRectificationBilling";
import {
  getPendingBirthTimeCheckout,
  markPendingBirthTimePaidReady,
  setPendingBirthTimeCheckout,
  type BirthTimeSubmitPayload,
} from "@/lib/pendingBirthTimeCheckout";

type AuthUser = { id: number; api_key?: string | null };

/** Resume submit after successful payment. */
export function consumeBirthTimePaidReady(): BirthTimeSubmitPayload | null {
  const p = getPendingBirthTimeCheckout();
  if (!p?.paidReady) return null;
  const payload = p.params;
  const purchaseId = p.purchaseId;
  setPendingBirthTimeCheckout({
    params: payload,
    purchaseId,
    paidReady: false,
  });
  return payload;
}

export function getPendingBirthTimePurchaseId(): number | undefined {
  return getPendingBirthTimeCheckout()?.purchaseId;
}

/**
 * After form validation: check paid entitlement, or open Razorpay checkout.
 */
export async function gateBirthTimeRectificationCheckout(opts: {
  user: AuthUser | null | undefined;
  payload: BirthTimeSubmitPayload;
  bypassCheckout?: boolean;
  onEntitled: (purchaseId?: number) => void;
}): Promise<void> {
  if (opts.bypassCheckout) {
    opts.onEntitled();
    return;
  }
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert(
      "Login required",
      "Please sign in to pay and submit Birth Time Rectification.",
      [{ text: "OK" }],
    );
    return;
  }

  const identity = {
    full_name: opts.payload.full_name,
    gender: opts.payload.gender,
    dob: opts.payload.dob,
    approx_tob: opts.payload.approx_tob,
    birth_place: opts.payload.birth_place,
  };

  try {
    const check = await checkBirthTimeRectificationEntitlement(opts.user, identity);
    if (check.entitled || !check.payment_required) {
      opts.onEntitled(getPendingBirthTimePurchaseId());
      return;
    }

    const order = await createBirthTimeRectificationOrder(opts.user, identity);
    if (order.already_entitled) {
      opts.onEntitled(order.purchase_id);
      return;
    }
    if (!order.payment_session_id || !order.purchase_id) {
      Alert.alert("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    setPendingBirthTimeCheckout({
      params: opts.payload,
      purchaseId: order.purchase_id,
    });

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "birth_time_rectification",
        cycle: "onetime",
        kind: "birth_time_rectification",
        purchaseId: String(order.purchase_id),
        orderId: order.order_id || "",
        sessionId: order.payment_session_id,
        razorpayKeyId: order.razorpay_key_id || "",
        amountPaise: String(
          order.amount_paise ??
            (order.amount ?? BIRTH_TIME_RECTIFICATION_PRICE_INR) * 100,
        ),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? BIRTH_TIME_RECTIFICATION_PRICE_INR),
        label: order.label || "Birth Time Rectification",
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    Alert.alert("Could not start payment", msg, [{ text: "OK" }]);
  }
}

/** Call on payment-webview success. */
export function finalizeBirthTimeRectificationPayment(): void {
  markPendingBirthTimePaidReady();
}
