/**
 * Cosmic Intelligence V1 pack checkout — Razorpay via /payment-webview.
 */
import { router } from "expo-router";
import { Alert } from "react-native";

import {
  ASK_V1_PACKS,
  createAskV1PackOrder,
  fetchAskV1Wallet,
  type AskV1PackId,
} from "@/lib/askV1PackBilling";

type AuthUser = { id: number; api_key?: string | null };

/**
 * After language pick: if wallet already has questions, enter chat;
 * otherwise show pack picker (caller) or start payment for a chosen pack.
 */
export async function hasActiveAskV1Wallet(
  user: AuthUser | null | undefined,
): Promise<{
  active: boolean;
  questions_left: number;
  questions_total?: number;
  questions_used?: number;
  free_questions_left?: number;
  free_questions_used?: number;
  pack_active?: boolean;
  pack_id?: string;
  expires_at?: string | null;
  /** False when wallet API failed — caller must not block Ask; let server decide quota. */
  fetchOk: boolean;
}> {
  if (!user?.id || !user.api_key) {
    return {
      active: false,
      questions_left: 0,
      free_questions_left: 0,
      free_questions_used: 0,
      fetchOk: true,
    };
  }
  try {
    const w = await fetchAskV1Wallet(user);
    const packLeft = Number(w.questions_left || 0);
    const freeUsed = Math.max(0, Number(w.free_questions_used ?? 0));
    const freeLeftFromApi = w.free_questions_left;
    const freeLeft =
      freeLeftFromApi != null && Number.isFinite(Number(freeLeftFromApi))
        ? Math.max(0, Number(freeLeftFromApi))
        : Math.max(0, 3 - freeUsed);
    const packActive = Boolean(w.active && packLeft > 0);
    return {
      active: Boolean(packActive || freeLeft > 0),
      pack_active: packActive,
      pack_id: packActive ? String(w.pack_id || "") : "",
      questions_left: packActive ? packLeft : freeLeft,
      questions_total: packActive
        ? Number(w.questions_total || packLeft)
        : 3,
      questions_used: packActive
        ? Number(w.questions_used || 0)
        : freeUsed,
      free_questions_left: freeLeft,
      free_questions_used: freeUsed,
      expires_at: packActive ? w.expires_at : null,
      fetchOk: true,
    };
  } catch {
    return {
      active: true,
      questions_left: 1,
      free_questions_left: 1,
      free_questions_used: 0,
      fetchOk: false,
    };
  }
}

export async function startAskV1PackPayment(
  user: AuthUser | null | undefined,
  packId: AskV1PackId,
): Promise<"paid_bypass" | "checkout" | "error"> {
  if (!user?.id || !user.api_key) {
    Alert.alert("Login required", "Please sign in to buy a question pack.", [{ text: "OK" }]);
    return "error";
  }

  const pack = ASK_V1_PACKS.find((p) => p.id === packId);
  if (!pack) {
    Alert.alert("Invalid pack", "Please choose a pack again.");
    return "error";
  }

  try {
    const order = await createAskV1PackOrder(user, packId);

    // Dev / Razorpay off — already credited.
    if (order.already_entitled || order.payment_bypass || order.active) {
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
        plan: "ask_v1",
        cycle: "onetime",
        kind: "ask_v1_pack",
        orderId: order.order_id || "",
        purchaseId: String(order.purchase_id),
        sessionId,
        razorpayKeyId: keyId,
        amountPaise: String(order.amount_paise ?? pack.price_inr * 100),
        customerName: order.customer_name || "",
        customerEmail: order.customer_email || "",
        customerPhone: order.customer_phone || "",
        amount: String(order.amount ?? pack.price_inr),
        label: order.label || `V1 ${pack.label} · ${pack.questions} questions`,
        returnTo: "ask",
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
