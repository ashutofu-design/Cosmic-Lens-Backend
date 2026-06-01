/**
 * Life Mastery report: after language pick → check entitlement → Cashfree or PDF.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  checkNumerologyReportEntitlement,
  createNumerologyReportOrder,
} from "@/lib/numerologyReportBilling";
import {
  getPendingNumerologyCheckout,
  markPendingNumerologyPaidReady,
  setPendingNumerologyCheckout,
} from "@/lib/pendingNumerologyCheckout";

type AuthUser = { id: number; api_key?: string | null };

export function pdfAuthHeaders(user: AuthUser): Record<string, string> {
  return {
    Accept: "application/pdf",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

/** Resume PDF step after successful Life Mastery payment. */
export function consumeNumerologyPaidReady(): boolean {
  const p = getPendingNumerologyCheckout();
  if (!p?.paidReady) return false;
  setPendingNumerologyCheckout({ ...p, paidReady: false });
  return true;
}

/**
 * After user picks PDF language: verify login, check paid entitlement, or open checkout.
 */
export async function gateNumerologyReportAfterLangPick(opts: {
  user: AuthUser | null | undefined;
  params: Record<string, unknown>;
  lang: string;
  label: string;
  amountInr: number;
  bypassCheckout: boolean;
  onEntitled: () => void;
}): Promise<void> {
  if (opts.bypassCheckout) {
    opts.onEntitled();
    return;
  }
  if (!opts.user?.id || !opts.user.api_key) {
    Alert.alert(
      "Login required",
      "Please sign in to unlock and download your Life Mastery Report.",
      [{ text: "OK" }],
    );
    return;
  }
  try {
    const check = await checkNumerologyReportEntitlement(opts.user, opts.params, opts.lang);
    if (check.entitled || !check.payment_required) {
      opts.onEntitled();
      return;
    }

    const order = await createNumerologyReportOrder(opts.user, opts.params, opts.lang);
    if (order.already_entitled) {
      opts.onEntitled();
      return;
    }
    if (!order.payment_session_id || !order.purchase_id) {
      Alert.alert("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    setPendingNumerologyCheckout({
      params: opts.params,
      lang: opts.lang,
    });

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "numerology_report",
        cycle: "onetime",
        kind: "numerology_report",
        purchaseId: String(order.purchase_id),
        orderId: order.order_id || "",
        sessionId: order.payment_session_id,
        razorpayKeyId: order.razorpay_key_id || "",
        amountPaise: String(order.amount_paise ?? (order.amount ?? opts.amountInr) * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? opts.amountInr),
        label: opts.label,
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    Alert.alert("Could not verify payment", msg, [{ text: "OK" }]);
  }
}

/** Call on payment-webview success for Life Mastery report. */
export function finalizeNumerologyReportPayment(): void {
  markPendingNumerologyPaidReady();
}
