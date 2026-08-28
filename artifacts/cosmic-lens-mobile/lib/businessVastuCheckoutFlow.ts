/**
 * Business Vastu: validate → check entitlement → Razorpay or submit.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  businessVastuOrderTotalInr,
  businessVastuUploadMode,
  checkBusinessVastuEntitlement,
  createBusinessVastuOrder,
  type BusinessVastuType,
} from "@/lib/businessVastuBilling";
import {
  getPendingBusinessVastuCheckout,
  markPendingBusinessVastuPaidReady,
  setPendingBusinessVastuCheckout,
  type BusinessVastuSubmitPayload,
} from "@/lib/pendingBusinessVastuCheckout";

type AuthUser = { id: number; api_key?: string | null };

export function consumeBusinessVastuPaidReady(): {
  payload: BusinessVastuSubmitPayload;
  planFileUri?: string;
} | null {
  const p = getPendingBusinessVastuCheckout();
  if (!p?.paidReady) return null;
  const payload = p.params;
  const purchaseId = p.purchaseId;
  const planFileUri = p.planFileUri;
  setPendingBusinessVastuCheckout({
    params: payload,
    purchaseId,
    planFileUri,
    paidReady: false,
  });
  return { payload, planFileUri };
}

export function getPendingBusinessVastuPurchaseId(): number | undefined {
  return getPendingBusinessVastuCheckout()?.purchaseId;
}

function quoteFromPayload(payload: BusinessVastuSubmitPayload) {
  const hasPdf = !!payload.floor_plan_upload;
  const roomCount = Array.isArray(payload.room_photos) ? payload.room_photos.length : 0;
  const upload_mode = businessVastuUploadMode({ hasPdf, roomCount });
  const identity = {
    business_type: payload.business_type as BusinessVastuType,
    property_name: payload.property_name,
    urgent: !!payload.urgent,
    upload_mode,
    room_count: hasPdf ? 0 : Math.max(1, roomCount),
  };
  const fallbackAmount = businessVastuOrderTotalInr({
    businessType: identity.business_type,
    priorityDelivery: identity.urgent,
    hasPdf,
    roomCount: identity.room_count,
  });
  return { identity, fallbackAmount };
}

export async function gateBusinessVastuCheckout(opts: {
  user: AuthUser | null | undefined;
  payload: BusinessVastuSubmitPayload;
  /** Local PDF path — kept out of create-order body; used after pay. */
  planFileUri?: string;
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
      "Please sign in to pay and submit Business Vastu.",
      [{ text: "OK" }],
    );
    return;
  }

  const { identity, fallbackAmount } = quoteFromPayload(opts.payload);

  try {
    const check = await checkBusinessVastuEntitlement(opts.user, identity);
    if (check.entitled || !check.payment_required) {
      opts.onEntitled(getPendingBusinessVastuPurchaseId());
      return;
    }

    const order = await createBusinessVastuOrder(opts.user, identity);
    if (order.already_entitled) {
      opts.onEntitled(order.purchase_id);
      return;
    }
    if (!order.payment_session_id || !order.purchase_id) {
      Alert.alert("Payment error", "Could not start checkout. Please try again.");
      return;
    }

    // Store stub payload (no heavy base64) + local URI for post-pay hydrate
    setPendingBusinessVastuCheckout({
      params: opts.payload,
      purchaseId: order.purchase_id,
      planFileUri: opts.planFileUri,
    });

    router.push({
      pathname: "/payment-webview",
      params: {
        plan: "business_vastu",
        cycle: "onetime",
        kind: "business_vastu",
        purchaseId: String(order.purchase_id),
        orderId: order.order_id || "",
        sessionId: order.payment_session_id,
        razorpayKeyId: order.razorpay_key_id || "",
        amountPaise: String(
          order.amount_paise ?? (order.amount ?? fallbackAmount) * 100,
        ),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? fallbackAmount),
        label: order.label || "Business Vastu",
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Network error";
    Alert.alert("Could not start payment", msg, [{ text: "OK" }]);
  }
}

export function finalizeBusinessVastuPayment(): void {
  markPendingBusinessVastuPaidReady();
}
