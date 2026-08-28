/**
 * Palmistry Pro: CTA → check entitlement → Razorpay or upload to admin.
 */
import { router } from "expo-router";
import { Alert, Platform } from "react-native";

import {
  checkPalmistryReportEntitlement,
  createPalmistryReportOrder,
} from "@/lib/palmistryReportBilling";
import {
  getPendingPalmistryCheckout,
  markPendingPalmistryPaidReady,
  setPendingPalmistryCheckout,
} from "@/lib/pendingPalmistryCheckout";

type AuthUser = { id: number; api_key?: string | null };

/** Resume admin-upload after successful Palmistry payment. */
export function consumePalmistryPaidReady(): boolean {
  const p = getPendingPalmistryCheckout();
  if (!p?.paidReady) return false;
  setPendingPalmistryCheckout({ ...p, paidReady: false });
  return true;
}

function alertMsg(title: string, msg: string) {
  if (Platform.OS === "web") window.alert(`${title}\n${msg}`);
  else Alert.alert(title, msg);
}

/**
 * After palms are ready: verify login, check paid entitlement, or open Razorpay.
 */
export async function gatePalmistryAfterReady(opts: {
  user: AuthUser | null | undefined;
  plan: "pdf" | "vip";
  urgent: boolean;
  amountInr: number;
  label: string;
  sessionId: string;
  writingHand: "left" | "right";
  contactValue?: string;
  lang?: "en" | "hn" | "hi";
  leftScan: unknown;
  rightScan: unknown;
  bypassCheckout: boolean;
  onEntitled: (purchaseId?: number) => void;
}): Promise<void> {
  if (opts.bypassCheckout) {
    opts.onEntitled();
    return;
  }
  if (!opts.user?.id || !opts.user.api_key) {
    alertMsg(
      "Login required",
      "Please sign in to pay and place your Palmistry order.",
    );
    return;
  }
  try {
    const check = await checkPalmistryReportEntitlement(opts.user, {
      plan: opts.plan,
      urgent: opts.urgent,
      sessionId: opts.sessionId,
    });
    if (check.entitled || !check.payment_required) {
      opts.onEntitled(check.purchase_id || undefined);
      return;
    }

    const order = await createPalmistryReportOrder(opts.user, {
      plan: opts.plan,
      urgent: opts.urgent,
      sessionId: opts.sessionId,
    });
    if (order.already_entitled) {
      opts.onEntitled(order.purchase_id);
      return;
    }
    if (!order.payment_session_id || !order.purchase_id) {
      alertMsg("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    setPendingPalmistryCheckout({
      plan: opts.plan,
      urgent: opts.urgent,
      purchaseId: order.purchase_id,
      sessionId: opts.sessionId,
      writingHand: opts.writingHand,
      contactValue: opts.contactValue,
      lang: opts.lang,
      leftScan: opts.leftScan,
      rightScan: opts.rightScan,
    });

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "palmistry_report",
        cycle: "onetime",
        kind: "palmistry_report",
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
    alertMsg("Could not verify payment", msg);
  }
}

/** Call on payment-webview success for Palmistry. */
export function finalizePalmistryReportPayment(): void {
  markPendingPalmistryPaidReady();
}
