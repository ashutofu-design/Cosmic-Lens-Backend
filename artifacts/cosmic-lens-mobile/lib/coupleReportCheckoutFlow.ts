/**
 * Pay-per-couple flow: after language pick → check entitlement → Cashfree or confirm PDF.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  checkCoupleReportEntitlement,
  createCoupleReportOrder,
  type CoupleReportProduct,
} from "@/lib/coupleReportBilling";
import {
  getPendingCoupleCheckout,
  markPendingCouplePaidReady,
  setPendingCoupleCheckout,
} from "@/lib/pendingCoupleCheckout";

type AuthUser = { id: number; api_key?: string | null };

export function pdfAuthHeaders(user: AuthUser): Record<string, string> {
  return {
    "Content-Type": "application/json",
    Accept: "application/pdf",
    "X-User-Id": String(user.id),
    ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
  };
}

/** Resume confirm/PDF step after successful couple-report payment. */
export function consumeCouplePaidReady(): boolean {
  const p = getPendingCoupleCheckout();
  if (!p?.paidReady) return false;
  setPendingCoupleCheckout({ ...p, paidReady: false });
  return true;
}

/**
 * After user picks PDF language: verify login, check paid entitlement, or open checkout.
 */
export async function gateCoupleReportAfterLangPick(opts: {
  user: AuthUser | null | undefined;
  product: CoupleReportProduct;
  p1: Record<string, unknown>;
  p2: Record<string, unknown>;
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
      "Please sign in to unlock and download your couple report.",
      [{ text: "OK" }],
    );
    return;
  }
  try {
    const check = await checkCoupleReportEntitlement(
      opts.user,
      opts.product,
      opts.p1,
      opts.p2,
      opts.lang,
    );
    if (check.entitled || !check.payment_required) {
      opts.onEntitled();
      return;
    }

    const order = await createCoupleReportOrder(
      opts.user,
      opts.product,
      opts.p1,
      opts.p2,
      opts.lang,
    );
    if (order.already_entitled) {
      opts.onEntitled();
      return;
    }
    if (!order.payment_session_id || !order.purchase_id) {
      Alert.alert("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    setPendingCoupleCheckout({
      product: opts.product,
      p1: opts.p1,
      p2: opts.p2,
      lang: opts.lang,
    });

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "couple_report",
        cycle: "onetime",
        kind: "couple_report",
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

/** Call on payment-webview success for couple reports. */
export function finalizeCoupleReportPayment(): void {
  markPendingCouplePaidReady();
}
