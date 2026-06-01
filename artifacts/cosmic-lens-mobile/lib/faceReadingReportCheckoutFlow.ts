/**

 * Face Reading PRO: after analyze → check entitlement → Cashfree or PDF.

 */

import { router } from "expo-router";

import { Alert } from "react-native";



import {

  checkFaceReadingReportEntitlement,

  createFaceReadingReportOrder,

  FACE_READING_PRO_PRICE_INR,

} from "@/lib/faceReadingReportBilling";

import {

  getPendingFaceReadingCheckout,

  markPendingFaceReadingPaidReady,

  setPendingFaceReadingCheckout,

  type PendingFaceReadingCheckout,

} from "@/lib/pendingFaceReadingCheckout";



type AuthUser = { id: number; api_key?: string | null };



export function consumeFaceReadingPaidReady(): PendingFaceReadingCheckout | null {

  const p = getPendingFaceReadingCheckout();

  if (!p?.paidReady) return null;

  setPendingFaceReadingCheckout({ ...p, paidReady: false });

  return p;

}



export function finalizeFaceReadingReportPayment(): void {

  markPendingFaceReadingPaidReady();

}



export async function gateFaceReadingReportAfterAnalyze(opts: {

  user: AuthUser | null | undefined;

  sessionId: string;

  lang: string;

  age?: string;

  gender?: string;

  onEntitled: () => void;

}): Promise<void> {

  if (!opts.user?.id || !opts.user.api_key) {

    Alert.alert(

      "Login required",

      "Please sign in to unlock your Face Reading PRO report.",

      [{ text: "OK" }],

    );

    return;

  }



  try {

    const check = await checkFaceReadingReportEntitlement(

      opts.user,

      opts.sessionId,

      opts.lang,

      opts.age,

      opts.gender,

    );

    if (check.entitled || !check.payment_required) {

      opts.onEntitled();

      return;

    }



    const order = await createFaceReadingReportOrder(

      opts.user,

      opts.sessionId,

      opts.lang,

      opts.age,

      opts.gender,

    );

    if (order.already_entitled) {

      opts.onEntitled();

      return;

    }

    if (!order.payment_session_id || !order.purchase_id) {

      Alert.alert("Payment error", "Could not start checkout. Please try again.");

      return;

    }



    setPendingFaceReadingCheckout({

      sessionId: opts.sessionId,

      lang: opts.lang,

      age: opts.age,

      gender: opts.gender,

    });



    router.push({

      pathname: "/payment-webview",

      params: {

        plan: "face_reading_report",

        cycle: "onetime",

        kind: "face_reading_report",

        purchaseId: String(order.purchase_id),

        orderId: order.order_id || "",

        sessionId: order.payment_session_id,

        razorpayKeyId: order.razorpay_key_id || "",

        amountPaise: String(order.amount_paise ?? (order.amount ?? FACE_READING_PRO_PRICE_INR) * 100),

        customerName: order.customer_name || "",

        customerEmail: order.customer_email || "",

        customerPhone: order.customer_phone || "",

        amount: String(order.amount ?? FACE_READING_PRO_PRICE_INR),

        label: order.label || "Face Reading PRO Report",

      },

    });

  } catch (e: unknown) {

    const msg = e instanceof Error ? e.message : "Network error";

    Alert.alert("Could not verify payment", msg, [{ text: "OK" }]);

  }

}

