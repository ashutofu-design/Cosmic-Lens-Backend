import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Modal,
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { WebView, WebViewNavigation } from "react-native-webview";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import { finalizeCoupleReportPayment } from "@/lib/coupleReportCheckoutFlow";
import { finalizeNumerologyReportPayment } from "@/lib/numerologyReportCheckoutFlow";
import { finalizePalmistryReportPayment } from "@/lib/palmistryReportCheckoutFlow";
import { finalizeBirthTimeRectificationPayment } from "@/lib/birthTimeRectificationCheckoutFlow";
import { finalizeBusinessVastuPayment } from "@/lib/businessVastuCheckoutFlow";

function payLog(...args: unknown[]) {
  if (__DEV__) console.log(...args);
}
function payWarn(...args: unknown[]) {
  if (__DEV__) console.warn(...args);
}
import { buildRazorpayCheckoutHtml, openRazorpayCheckoutWeb } from "@/lib/razorpayCheckout";
import {
  getPendingAstrovastuRoomUpload,
  markPendingAstrovastuRoomPaidReady,
} from "@/lib/pendingAstrovastuRoomUpload";
import {
  getPendingAstrovastuFloorPlan,
  markPendingAstrovastuFloorPaidReady,
} from "@/lib/pendingAstrovastuFloorPlan";
import { PRICES } from "@/lib/subscription";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

type Phase = "creating" | "paying" | "verifying" | "success" | "failed" | "cancelled" | "pending_verify";

const PLAN_LABELS: Record<string, string> = {
  trial:      "7-Day Trial",
  basic:      "Basic",
  pro:        "Pro",
  elite:      "Pro",
  astrovastu: "AstroVastu",
  ask_v1:     "V1 Question Pack",
  ask_v3:     "V3 Live Session",
};
const PLAN_ICONS: Record<string, string> = {
  trial:      "🎁",
  basic:      "✨",
  pro:        "⚡",
  elite:      "⚡",
  astrovastu: "🏠",
  ask_v1:     "💬",
  ask_v3:     "⚡",
};
const CYCLE_LABELS: Record<string, string> = {
  weekly:  "7 Days",
  monthly: "Monthly",
  yearly:  "Yearly",
  onetime: "Lifetime",
};
const PLAN_PRICES: Record<string, number> = {
  trial_weekly:  PRICES.trial_weekly,
  basic_monthly: PRICES.basic_monthly,
  basic_yearly:  PRICES.basic_yearly,
  pro_monthly:   PRICES.pro_monthly,
  elite_monthly: PRICES.pro_monthly,
};

export default function PaymentWebviewScreen() {
  const C      = useC();
  const t      = useT();
  const insets = useSafeAreaInsets();
  const { user, setUser, refreshUser } = useUser();
  const isDark = C.isDark;
  const ac     = isDark ? "#f59e0b" : "#7C3AED";

  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad    = Platform.OS === "android"
    ? Math.max(insets.top, androidSB)
    : insets.top;

  const params = useLocalSearchParams<{
    plan: string; cycle: string; orderId?: string; sessionId?: string; paymentLink?: string;
    // ── AstroVastu one-time purchase params ──
    kind?: string; sku?: string; purchaseId?: string;
    amount?: string; label?: string; propertyName?: string;
    returnTo?: string;
    // ── Razorpay one-time (couple report, gemstone) ──
    razorpayKeyId?: string; amountPaise?: string;
    customerName?: string; customerEmail?: string; customerPhone?: string;
  }>();

  const plan  = params.plan  ?? "pro";
  const cycle = params.cycle ?? "monthly";
  const isAstroVastu  = (params.kind === "astrovastu") || plan === "astrovastu";
  const isCoupleReport = params.kind === "couple_report" || plan === "couple_report";
  const isGemstone = params.kind === "gemstone" || plan === "gemstone";
  const isNumerologyReport =
    params.kind === "numerology_report" || plan === "numerology_report";
  const isPalmistryReport =
    params.kind === "palmistry_report" || plan === "palmistry_report";
  const isBirthTimeRectification =
    params.kind === "birth_time_rectification" || plan === "birth_time_rectification";
  const isBusinessVastu =
    params.kind === "business_vastu" || plan === "business_vastu";
  const isAskV1Pack = params.kind === "ask_v1_pack" || plan === "ask_v1";
  const isAskV3Live = params.kind === "ask_v3_live" || plan === "ask_v3";
  const avPurchaseId  = params.purchaseId ? Number(params.purchaseId) : 0;
  const avLabel       = params.label || (isAskV1Pack ? "V1 Question Pack" : isGemstone ? "Gemstone" : isCoupleReport ? "Love Reality Pro" : isPalmistryReport ? "Palmistry Pro" : isBirthTimeRectification ? "Birth Time Rectification" : isBusinessVastu ? "Business Vastu" : "AstroVastu Unlock");
  const avPropName    = params.propertyName || "";
  const avAmount      = params.amount ? Number(params.amount) : 0;
  const isRoomUploadPay = params.sku === "room_expert_199";
  const isFloorPlanPay = isAstroVastu && String(params.sku || "").includes("_floor_");
  const price = (isAstroVastu || isCoupleReport || isGemstone || isAskV1Pack || isAskV3Live || isNumerologyReport || isPalmistryReport || isBirthTimeRectification || isBusinessVastu)
    ? avAmount
    : (PLAN_PRICES[`${plan}_${cycle}`] ?? 0);

  const [phase,       setPhase]       = useState<Phase>("creating");
  const [errMsg,      setErrMsg]      = useState("");
  const [orderId,     setOrderId]     = useState(params.orderId ?? "");
  const [sessionId,   setSessionId]   = useState<string>(params.sessionId ?? "");
  const [paymentLink, setPaymentLink] = useState<string>(params.paymentLink ?? "");

  const fadeAnim  = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const handledRef = useRef(false);
  const rzKeyId = params.razorpayKeyId || process.env.EXPO_PUBLIC_RAZORPAY_KEY_ID || "";
  // Razorpay is the active gateway whenever a key is available; otherwise
  // fall back to the legacy Cashfree link/session flow.
  const isRazorpay = !!rzKeyId;
  const rzAmountPaise = params.amountPaise
    ? Number(params.amountPaise)
    : Math.round(price * 100);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(scaleAnim, { toValue: 1, friction: 7,   useNativeDriver: true }),
    ]).start();

    if (params.orderId && (params.paymentLink || params.sessionId)) {
      setOrderId(params.orderId);
      if (params.sessionId) setSessionId(params.sessionId);
      setPaymentLink(params.paymentLink || "");
      setPhase("paying");
    } else {
      _createOrder();
    }
  }, []);

  // ── Official Cashfree JS SDK loader (web only) ─────────────────────────────
  // Loads the SDK from CDN once, then calls cashfree.checkout({ paymentSessionId, paymentMethod? }).
  // We pass ONLY paymentSessionId (+ optional paymentMethod) — never the constructed payment_link.
  type PayMethod = "upi" | "card" | "netbanking" | undefined;

  async function _openCashfreeCheckout(paymentSessionId: string, method: PayMethod = undefined) {
    if (Platform.OS !== "web" || typeof window === "undefined") return;

    // Strict re-check: never call SDK without a valid session id
    if (!paymentSessionId || paymentSessionId.trim() === "") {
      payWarn("[Pay] ❌ refusing to invoke SDK with empty paymentSessionId");
      return;
    }

    const w: any = window;
    const env: "sandbox" | "production" =
      String(process.env.EXPO_PUBLIC_CASHFREE_ENV || "sandbox") === "production"
        ? "production"
        : "sandbox";

    async function _ensureSdkLoaded(): Promise<any> {
      if (w.Cashfree) return w.Cashfree;
      await new Promise<void>((resolve, reject) => {
        const existing = document.getElementById("cashfree-sdk-script");
        if (existing) {
          existing.addEventListener("load", () => resolve());
          existing.addEventListener("error", () => reject(new Error("SDK load failed")));
          return;
        }
        const s = document.createElement("script");
        s.id    = "cashfree-sdk-script";
        s.src   = "https://sdk.cashfree.com/js/v3/cashfree.js";
        s.async = true;
        s.onload  = () => resolve();
        s.onerror = () => reject(new Error("SDK load failed"));
        document.head.appendChild(s);
      });
      return w.Cashfree;
    }

    // Map our friendly method names to Cashfree's componentName so the drop-in
    // pre-selects (and on mobile UPI auto-launches GPay/PhonePe via intent).
    function _componentFor(m: PayMethod): string[] | undefined {
      switch (m) {
        case "upi":         return ["order-details", "upi"];
        case "card":        return ["order-details", "card"];
        case "netbanking":  return ["order-details", "netbanking"];
        default:            return undefined;   // full default checkout
      }
    }

    try {
      const Cashfree = await _ensureSdkLoaded();
      const cashfree = Cashfree({ mode: env });
      const components = _componentFor(method);
      payLog(
        "[Pay] 🚀 cashfree.checkout({ paymentSessionId: ...",
        paymentSessionId.slice(-12),
        "})  method=", method ?? "default",
        " mode=", env,
      );
      const opts: any = {
        paymentSessionId,                 // ONLY this — no link, no order_id
        redirectTarget: "_blank",         // open hosted checkout in a new tab
      };
      if (components) opts.components = components;
      const result = await cashfree.checkout(opts);
      payLog("[Pay] checkout result", result);
    } catch (e: any) {
      payWarn("[Pay] ❌ SDK checkout failed, falling back to link:", e?.message);
      // Hard fallback only if SDK can't load (offline / CSP / etc)
      try { window.open(paymentLink, "_blank", "noopener,noreferrer"); } catch {}
    }
  }

  function _razorpayOpts() {
    return {
      keyId: rzKeyId,
      orderId: sessionId,
      amountPaise: rzAmountPaise,
      title: "Cosmic Lens",
      description: avLabel,
      customerName: params.customerName || "",
      customerEmail: params.customerEmail || "",
      customerPhone: params.customerPhone || "",
      themeColor: ac,
    };
  }

  async function _openRazorpayCheckout() {
    if (!sessionId || !rzKeyId) {
      setErrMsg("Payment session invalid. Please go back and try again.");
      setPhase("failed");
      return;
    }
    try {
      await openRazorpayCheckoutWeb(
        _razorpayOpts(),
        () => {
          handledRef.current = true;
          setPhase("verifying");
          _verifyPayment(orderId);
        },
        () => {
          if (!handledRef.current) setPhase("cancelled");
        },
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Razorpay checkout failed";
      setErrMsg(msg);
      setPhase("failed");
    }
  }

  function _onRazorpayMessage(event: { nativeEvent: { data: string } }) {
    if (handledRef.current) return;
    try {
      const msg = JSON.parse(event.nativeEvent.data) as {
        status?: string; error?: string;
      };
      if (msg.status === "success") {
        handledRef.current = true;
        setPhase("verifying");
        _verifyPayment(orderId);
      } else if (msg.status === "dismissed") {
        setPhase("cancelled");
      } else if (msg.status === "failed") {
        setErrMsg(msg.error || "Payment failed");
        setPhase("failed");
      }
    } catch { /* ignore malformed messages */ }
  }

  async function _createOrder() {
    if (isCoupleReport || isAstroVastu || isGemstone) {
      if (params.orderId && params.sessionId) {
        setOrderId(params.orderId);
        setSessionId(params.sessionId);
        setPaymentLink(params.paymentLink || "");
        setPhase("paying");
        return;
      }
    }
    if (!user?.id) {
      setErrMsg("Please login to purchase a plan.");
      setPhase("failed");
      return;
    }
    // Always start FRESH — clear any stale link/order before creating.
    setPaymentLink("");
    setOrderId("");
    handledRef.current = false;
    setPhase("creating");
    payLog("[Pay] 🔄 creating fresh order", { plan, cycle, userId: user.id });
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 15000);
      const resp  = await fetch(`${API_BASE}/api/payment/create-order`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          ...(user.api_key ? { "X-API-Key": user.api_key } : {}),
        },
        body:    JSON.stringify({ user_id: user.id, plan, cycle }),
        signal:  ctrl.signal,
      });
      clearTimeout(timer);
      const data = await resp.json();
      // STRICT spec: log full response for debugging.
      payLog("ORDER RESPONSE:", data);
      payLog("[Pay] order response meta", { ok: resp.ok, status: resp.status });

      if (!resp.ok || data.error) {
        const msg = data.error ?? `Order creation failed (${resp.status}).`;
        payWarn("[Pay] ❌ create-order failed:", msg);
        setErrMsg(msg);
        setPhase("failed");
        return;  // do NOT open checkout on failure
      }
      const { order_id, payment_link, payment_session_id } =
        data as { order_id: string; payment_link: string; payment_session_id: string };

      // STRICT spec: log session id explicitly.
      payLog("SESSION ID:", payment_session_id);

      // STRICT validation: only payment_session_id is required to open checkout.
      // Without a valid session, do NOT open the Cashfree UI under any circumstances.
      if (!payment_session_id || payment_session_id.trim() === "") {
        payWarn("[Pay] ❌ missing payment_session_id — refusing to open checkout");
        setErrMsg("Server returned an invalid session. Please try again.");
        setPhase("failed");
        return;
      }

      payLog("[Pay] ✅ fresh session", {
        order_id,
        session_tail: "..." + payment_session_id.slice(-20),
      });

      setOrderId(order_id);
      setSessionId(payment_session_id);
      setPaymentLink(payment_link || "");
      setPhase("paying");

      // Note: We DO NOT auto-open Cashfree here. On web, the user picks a
      // method (UPI / Card / NetBanking) from the buttons in the "paying"
      // phase, and each button launches the SDK with that method preselected.
      // On native, the WebView modal will open automatically (uses paymentLink).
    } catch (e: any) {
      payWarn("[Pay] ❌ network error:", e?.message);
      setErrMsg(e?.message ?? "Network error. Check connection.");
      setPhase("failed");
    }
  }

  function _onNavChange(nav: WebViewNavigation) {
    const url = nav.url || "";
    // Cashfree redirects to our return_url after success/failure.
    // backend: /api/payment/return?order_id=...
    if (handledRef.current) return;
    if (
      url.includes("/api/payment/return") ||
      url.includes("payment/success")    ||
      url.includes("payment/failure")    ||
      url.includes("payment/cancel")
    ) {
      handledRef.current = true;
      setPhase("verifying");
      _verifyPayment(orderId);
    }
  }

  async function _verifyPayment(oid: string) {
    if (!oid && !isAstroVastu && !isGemstone && !isCoupleReport && !isNumerologyReport && !isPalmistryReport && !isBirthTimeRectification && !isBusinessVastu && !isAskV1Pack && !isAskV3Live) {
      setPhase("cancelled");
      return;
    }
    // Small grace so backend webhook can settle
    await new Promise(r => setTimeout(r, 1200));

    // ── Cosmic Intelligence V3 live packs ────────────────────────────
    if (isAskV3Live) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/ask-v3/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && (data?.granted || data?.entitled || data?.session_id)) {
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Cosmic Intelligence V1 question packs ────────────────────────
    if (isAskV1Pack) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/ask-v1/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && (data?.granted || data?.entitled || data?.active)) {
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Numerology Pro / Life Mastery: poll purchase-status ──────────
    if (isNumerologyReport) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/numerology-report/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && data?.entitled) {
            finalizeNumerologyReportPayment();
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Palmistry Pro: poll purchase-status ─────────────────────────
    if (isPalmistryReport) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/palmistry-report/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && data?.entitled) {
            finalizePalmistryReportPayment();
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Birth Time Rectification: poll purchase-status ──────────────
    if (isBirthTimeRectification) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/birth-time-rectification/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && data?.entitled) {
            finalizeBirthTimeRectificationPayment();
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Business Vastu: poll purchase-status ─────────────────────────
    if (isBusinessVastu) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/business-vastu/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && data?.entitled) {
            finalizeBusinessVastuPayment();
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── Couple report: poll purchase-status ──────────────────────────
    if (isCoupleReport) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(
            `${API_BASE}/api/couple-report/purchase-status/${avPurchaseId}`,
            { signal: ctrl.signal, headers },
          );
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && data?.entitled) {
            finalizeCoupleReportPayment();
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      setPhase("pending_verify");
      return;
    }

    // ── One-time purchases: poll purchase-status endpoint ───────────
    if (isAstroVastu || isGemstone) {
      if (!avPurchaseId) { setPhase("cancelled"); return; }
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      if (user?.id) headers["X-User-Id"] = String(user.id);
      const statusUrl = isGemstone
        ? `${API_BASE}/api/gemstone/purchase-status/${avPurchaseId}`
        : `${API_BASE}/api/astrovastu/purchase-status/${avPurchaseId}`;
      for (let attempt = 0; attempt < 6; attempt++) {
        try {
          const ctrl  = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 10000);
          const resp  = await fetch(statusUrl, { signal: ctrl.signal, headers });
          clearTimeout(timer);
          const data = await resp.json();
          if (data?.status === "paid" && (data?.granted || data?.paid)) {
            if (isRoomUploadPay && getPendingAstrovastuRoomUpload() && avPurchaseId) {
              markPendingAstrovastuRoomPaidReady(avPurchaseId);
            }
            if (isFloorPlanPay && getPendingAstrovastuFloorPlan() && avPurchaseId) {
              markPendingAstrovastuFloorPaidReady(avPurchaseId);
            }
            await refreshUser().catch(() => {});
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setPhase("success");
            return;
          }
        } catch { /* retry */ }
        await new Promise(r => setTimeout(r, 2000));
      }
      // Webhook hasn't landed yet OR user cancelled — don't assume either.
      // Show "Pending verification" with a "Check again" button (re-runs
      // _verifyPayment on the same purchase, no new Cashfree order).
      setPhase("pending_verify");
      return;
    }

    // ── Subscription plans (existing flow) ───────────────────────────────
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 12000);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;
      const resp  = await fetch(`${API_BASE}/api/payment/status/${oid}`, { signal: ctrl.signal, headers });
      clearTimeout(timer);
      const data = await resp.json();

      if (data.status === "SUCCESS") {
        if (data.user && user) {
          setUser({ ...user, ...data.user });
        } else {
          await refreshUser();
        }
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        setPhase("success");
      } else if (data.status === "CANCELLED") {
        setPhase("cancelled");
      } else {
        setPhase("cancelled");
      }
    } catch {
      setPhase("cancelled");
    }
  }

  function handleRetry() {
    handledRef.current = false;
    setPaymentLink("");
    setErrMsg("");
    setPhase("creating");
    _createOrder();
  }

  function handleClosePayment() {
    // User taps Cancel inside the paying modal
    handledRef.current = true;
    setPhase("verifying");
    _verifyPayment(orderId);
  }

  const phaseIcon: Record<Phase, string> = {
    creating:       "⏳",
    paying:         "💳",
    verifying:      "🔍",
    success:        "🎉",
    failed:         "❌",
    cancelled:      "🌙",
    pending_verify: "⌛",
  };

  const successCopy = isGemstone
    ? `💎 ${avLabel} order confirmed — we will contact you for delivery.`
    : isCoupleReport
    ? `💞 ${avLabel} unlocked — return to generate your PDF.`
    : isRoomUploadPay
      ? `🏠 Payment successful.`
    : isAstroVastu
      ? `${PLAN_ICONS.astrovastu} ${avLabel}${avPropName ? ` for "${avPropName}"` : ""} unlocked!`
      : `${PLAN_ICONS[plan]} ${PLAN_LABELS[plan]} ${CYCLE_LABELS[cycle]} plan is now active!`;

  const phaseTitle: Record<Phase, string> = {
    creating:       "Creating Your Order…",
    paying:         "Complete Your Payment",
    verifying:      "Verifying Payment…",
    success:        isGemstone ? "Order Confirmed!" : isCoupleReport ? "Payment Successful!" : isAstroVastu ? "Unlocked!" : "Plan Activated!",
    failed:         "Payment Failed",
    cancelled:      "Payment Cancelled",
    pending_verify: "Verification Pending",
  };

  const payGateway = isRazorpay ? "Razorpay" : "Cashfree";

  const phaseSubtitle: Record<Phase, string> = {
    creating:       isRazorpay ? "Connecting to Razorpay…" : "Securely connecting to Cashfree…",
    paying:         isRazorpay
      ? "Pay securely with Razorpay (UPI / Card / Net Banking)."
      : "Pay securely below — page is hosted by Cashfree.",
    verifying:      "Checking your payment status…",
    success:        successCopy,
    failed:         errMsg || "Something went wrong. Please try again.",
    cancelled:      "No payment was made. You can try again anytime.",
    pending_verify: "If you completed the payment, it can take a few seconds to confirm. Tap below to re-check — you will NOT be charged again.",
  };

  const isLoading = ["creating", "verifying"].includes(phase);

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Text style={{ fontSize: 18 }}>←</Text>
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>{t.paymentTitle}</Text>
        <View style={[s.cfBadge, { borderColor: isDark ? "rgba(245,158,11,0.3)" : "rgba(245,158,11,0.4)" }]}>
          <Text style={{ fontSize: 9, color: isDark ? "#f59e0b" : "#d97706", fontFamily: F.bold, letterSpacing: 0.5 }}>
            🔒 {payGateway}
          </Text>
        </View>
      </View>

      <Animated.View style={[s.body, { opacity: fadeAnim, transform: [{ scale: scaleAnim }] }]}>
        {/* Order Summary */}
        <View style={[s.summaryCard, {
          backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(245,158,11,0.05)",
          borderColor:     isDark ? "rgba(245,158,11,0.25)" : "rgba(245,158,11,0.2)",
        }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
            <Text style={{ fontSize: 28 }}>{PLAN_ICONS[plan] ?? "⭐"}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.planName, { color: isDark ? "#f59e0b" : "#d97706" }]}>
                {isGemstone || isCoupleReport ? avLabel : `${PLAN_LABELS[plan]} ${CYCLE_LABELS[cycle]}`}
              </Text>
              <Text style={[s.planSub, { color: C.textMuted }]}>
                {isGemstone ? "Certified gemstone · one-time" : isCoupleReport ? "One-time couple report" : "Cosmic Lens Premium"}
              </Text>
            </View>
            <Text style={[s.price, { color: isDark ? "#f59e0b" : "#d97706" }]}>
              ₹{price.toLocaleString("en-IN")}
            </Text>
          </View>
          <View style={[s.sep, { backgroundColor: isDark ? "rgba(245,158,11,0.1)" : "rgba(245,158,11,0.08)" }]} />
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Text style={[s.detailLabel, { color: C.textMuted }]}>Billing Cycle</Text>
            <Text style={[s.detailVal, { color: C.textMid }]}>{CYCLE_LABELS[cycle]}</Text>
          </View>
          <View style={{ flexDirection: "row", justifyContent: "space-between", marginTop: 4 }}>
            <Text style={[s.detailLabel, { color: C.textMuted }]}>Payment Gateway</Text>
            <Text style={[s.detailVal, { color: C.textMid }]}>{payGateway}</Text>
          </View>
        </View>

        {/* Status / actions */}
        <View style={[s.statusCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={s.statusIcon}>{phaseIcon[phase]}</Text>
          <Text style={[s.statusTitle, { color: C.text }]}>{phaseTitle[phase]}</Text>
          <Text style={[s.statusSub, { color: C.textMuted }]}>{phaseSubtitle[phase]}</Text>

          {isLoading && (
            <ActivityIndicator size="large" color={ac} style={{ marginTop: 20 }} />
          )}

          {/* Web: Razorpay one-time checkout */}
          {phase === "paying" && Platform.OS === "web" && isRazorpay && !!sessionId && !!rzKeyId && (
            <View style={{ gap: 10, marginTop: 20, width: "100%" }}>
              <Pressable
                onPress={() => { Haptics.selectionAsync(); _openRazorpayCheckout(); }}
                style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
              >
                <Text style={s.primaryBtnText}>💳 Pay with Razorpay</Text>
              </Pressable>
              <Pressable
                onPress={() => { Haptics.selectionAsync(); setPhase("verifying"); _verifyPayment(orderId); }}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>✓ I've Paid — Verify Now</Text>
              </Pressable>
              <Pressable
                onPress={() => router.back()}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>Cancel</Text>
              </Pressable>
            </View>
          )}

          {/* Web: choose a payment method — each opens Cashfree pre-selected */}
          {phase === "paying" && Platform.OS === "web" && !isRazorpay && !!sessionId && (
            <View style={{ gap: 10, marginTop: 20, width: "100%" }}>
              <Text style={[s.statusSub, { color: C.textMid, marginBottom: 4, fontFamily: F.bold }]}>
                Choose Payment Method
              </Text>

              {/* UPI — opens GPay/PhonePe app on mobile, QR on desktop */}
              <Pressable
                onPress={() => { Haptics.selectionAsync(); _openCashfreeCheckout(sessionId, "upi"); }}
                style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
              >
                <Text style={s.primaryBtnText}>📱 Pay with UPI  (GPay / PhonePe / Paytm)</Text>
              </Pressable>

              {/* Card */}
              <Pressable
                onPress={() => { Haptics.selectionAsync(); _openCashfreeCheckout(sessionId, "card"); }}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: ac, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: ac }]}>💳 Pay with Card</Text>
              </Pressable>

              {/* Net Banking */}
              <Pressable
                onPress={() => { Haptics.selectionAsync(); _openCashfreeCheckout(sessionId, "netbanking"); }}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: ac, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: ac }]}>🏦 Pay with Net Banking</Text>
              </Pressable>

              <View style={{ height: 6 }} />

              {/* After paying in the new tab, come back & verify */}
              <Pressable
                onPress={() => { Haptics.selectionAsync(); setPhase("verifying"); _verifyPayment(orderId); }}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>✓ I've Paid — Verify Now</Text>
              </Pressable>

              <Pressable
                onPress={() => router.back()}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>Cancel</Text>
              </Pressable>
            </View>
          )}

          {phase === "success" && (
            <Pressable
              onPress={() => {
                Haptics.selectionAsync();
                if (isGemstone && params.returnTo) {
                  router.replace(params.returnTo as any);
                } else if (isAskV3Live || params.returnTo === "ask_v3") {
                  router.replace("/(tabs)/ask?resumeV3=1" as any);
                } else if (isAskV1Pack || params.returnTo === "ask") {
                  router.replace("/(tabs)/ask" as any);
                } else if (isCoupleReport || isRoomUploadPay || params.returnTo === "astrovastu-pro") {
                  router.back();
                } else {
                  router.replace("/");
                }
              }}
              style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
            >
              <Text style={s.primaryBtnText}>
                {isGemstone
                  ? "Back to Gemstones →"
                  : isAskV3Live
                  ? "Open live queue →"
                  : isAskV1Pack
                  ? "Start asking →"
                  : isCoupleReport
                  ? "Continue to PDF →"
                  : isRoomUploadPay
                    ? "Continue →"
                    : "Go to Home ✨"}
              </Text>
            </Pressable>
          )}

          {phase === "pending_verify" && (
            <View style={{ gap: 10, marginTop: 20, width: "100%" }}>
              <Pressable
                onPress={() => {
                  Haptics.selectionAsync();
                  setPhase("verifying");
                  _verifyPayment(orderId);
                }}
                style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
              >
                <Text style={s.primaryBtnText}>🔄 Check Payment Status</Text>
              </Pressable>
              <Pressable
                onPress={() => router.back()}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>Close</Text>
              </Pressable>
            </View>
          )}

          {(phase === "failed" || phase === "cancelled") && (
            <View style={{ gap: 10, marginTop: 20, width: "100%" }}>
              <Pressable
                onPress={() => { Haptics.selectionAsync(); handleRetry(); }}
                style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
              >
                <Text style={s.primaryBtnText}>Try Again</Text>
              </Pressable>
              <Pressable
                onPress={() => router.back()}
                style={({ pressed }) => [s.secondaryBtn, { borderColor: C.border, opacity: pressed ? 0.7 : 1 }]}
              >
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>Go Back</Text>
              </Pressable>
            </View>
          )}
        </View>

        <View style={s.trustRow}>
          {(isRazorpay
            ? ["🔒 256-bit SSL", "🏦 Razorpay Secured", "💎 One-time payment"]
            : ["🔒 256-bit SSL", "🏦 Cashfree Secured", "🔄 Auto-renewal"]
          ).map(b => (
            <View key={b} style={[s.trustBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Text style={[s.trustText, { color: C.textMuted }]}>{b}</Text>
            </View>
          ))}
        </View>

        <Text style={[s.footer, { color: C.textMuted }]}>
          Payment is processed securely by {payGateway}.{"\n"}
          Do not share OTP or card details with anyone.
        </Text>
      </Animated.View>

      {/* Razorpay checkout (mobile — hosted in WebView) */}
      <Modal
        visible={Platform.OS !== "web" && phase === "paying" && isRazorpay && !!sessionId && !!rzKeyId}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={handleClosePayment}
      >
        <View style={[s.modalRoot, { backgroundColor: C.bg }]}>
          <View style={[s.modalHeader, { paddingTop: topPad + 6, borderBottomColor: C.border, backgroundColor: C.bg }]}>
            <Pressable onPress={handleClosePayment} hitSlop={10} style={s.modalCloseBtn}>
              <Text style={{ color: C.text, fontSize: 22, lineHeight: 22 }}>✕</Text>
            </Pressable>
            <View style={{ flex: 1 }}>
              <Text style={[s.modalTitle, { color: C.text }]}>Secure Payment</Text>
              <Text style={[s.modalSub, { color: C.textMuted }]}>
                Powered by Razorpay • ₹{price.toLocaleString("en-IN")}
              </Text>
            </View>
            <View style={[s.lockBadge, { borderColor: ac }]}>
              <Text style={{ color: ac, fontSize: 10, fontFamily: F.bold }}>🔒 SSL</Text>
            </View>
          </View>
          <WebView
            source={{ html: buildRazorpayCheckoutHtml(_razorpayOpts()) }}
            onMessage={_onRazorpayMessage}
            startInLoadingState
            renderLoading={() => (
              <View style={s.wvLoader}>
                <ActivityIndicator size="large" color={ac} />
                <Text style={{ marginTop: 10, color: C.textMuted, fontFamily: F.semibold }}>
                  Opening Razorpay…
                </Text>
              </View>
            )}
            javaScriptEnabled
            domStorageEnabled
            originWhitelist={["*"]}
            style={{ flex: 1, backgroundColor: "#0c0818" }}
          />
        </View>
      </Modal>

      {/* In-app payment WebView (mobile only — web uses new tab) */}
      <Modal
        visible={Platform.OS !== "web" && phase === "paying" && !!paymentLink && !isRazorpay}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={handleClosePayment}
      >
        <View style={[s.modalRoot, { backgroundColor: C.bg }]}>
          <View style={[s.modalHeader, { paddingTop: topPad + 6, borderBottomColor: C.border, backgroundColor: C.bg }]}>
            <Pressable onPress={handleClosePayment} hitSlop={10} style={s.modalCloseBtn}>
              <Text style={{ color: C.text, fontSize: 22, lineHeight: 22 }}>✕</Text>
            </Pressable>
            <View style={{ flex: 1 }}>
              <Text style={[s.modalTitle, { color: C.text }]}>Secure Payment</Text>
              <Text style={[s.modalSub, { color: C.textMuted }]}>
                Powered by Cashfree • ₹{price.toLocaleString("en-IN")}
              </Text>
            </View>
            <View style={[s.lockBadge, { borderColor: ac }]}>
              <Text style={{ color: ac, fontSize: 10, fontFamily: F.bold }}>🔒 SSL</Text>
            </View>
          </View>

          {paymentLink ? (
            <WebView
              source={{ uri: paymentLink }}
              onNavigationStateChange={_onNavChange}
              onShouldStartLoadWithRequest={(req) => {
                // Allow UPI deep-links to open in respective apps
                if (
                  req.url.startsWith("upi://")     ||
                  req.url.startsWith("phonepe://") ||
                  req.url.startsWith("paytmmp://") ||
                  req.url.startsWith("tez://")     ||
                  req.url.startsWith("gpay://")
                ) {
                  // Let RN handle the deep link
                  return false;
                }
                return true;
              }}
              startInLoadingState
              renderLoading={() => (
                <View style={s.wvLoader}>
                  <ActivityIndicator size="large" color={ac} />
                  <Text style={{ marginTop: 10, color: C.textMuted, fontFamily: F.semibold }}>
                    Loading secure checkout…
                  </Text>
                </View>
              )}
              javaScriptEnabled
              domStorageEnabled
              thirdPartyCookiesEnabled
              sharedCookiesEnabled
              setSupportMultipleWindows={false}
              originWhitelist={["*"]}
              mixedContentMode="always"
              style={{ flex: 1, backgroundColor: "#fff" }}
            />
          ) : (
            <View style={s.wvLoader}>
              <ActivityIndicator size="large" color={ac} />
            </View>
          )}
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 1,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.06)",
    alignItems: "center", justifyContent: "center",
  },
  headerTitle: { flex: 1, fontSize: 17, fontFamily: F.bold, letterSpacing: -0.3 },
  cfBadge: {
    borderWidth: 1, borderRadius: 10, paddingVertical: 4, paddingHorizontal: 8,
  },

  body: { flex: 1, paddingHorizontal: 16, paddingTop: 20, gap: 16 },

  summaryCard: { borderRadius: 16, borderWidth: 1.5, padding: 16, gap: 8 },
  planName:    { fontSize: 17, fontFamily: F.bold },
  planSub:     { fontSize: 12, fontFamily: F.regular, marginTop: 1 },
  price:       { fontSize: 22, fontFamily: F.bold },
  sep:         { height: 1, marginVertical: 6 },
  detailLabel: { fontSize: 12, fontFamily: F.medium },
  detailVal:   { fontSize: 12, fontFamily: F.semibold },

  statusCard: {
    borderRadius: 16, borderWidth: 1, padding: 24,
    alignItems: "center", gap: 8,
  },
  statusIcon:  { fontSize: 44, marginBottom: 4 },
  statusTitle: { fontSize: 20, fontFamily: F.bold, textAlign: "center" },
  statusSub:   { fontSize: 13, fontFamily: F.regular, textAlign: "center", lineHeight: 20 },

  primaryBtn: {
    borderRadius: 14, paddingVertical: 14,
    alignItems: "center", justifyContent: "center", width: "100%",
  },
  primaryBtnText: { color: "#fff", fontSize: 15, fontFamily: F.bold },

  secondaryBtn: {
    borderRadius: 14, paddingVertical: 13, borderWidth: 1,
    alignItems: "center", justifyContent: "center", width: "100%",
  },
  secondaryBtnText: { fontSize: 14, fontFamily: F.semibold },

  trustRow:  { flexDirection: "row", flexWrap: "wrap", gap: 6, justifyContent: "center" },
  trustBadge: {
    borderRadius: 8, borderWidth: 1,
    paddingVertical: 5, paddingHorizontal: 10,
  },
  trustText: { fontSize: 10, fontFamily: F.medium },

  footer: {
    fontSize: 10, fontFamily: F.regular,
    textAlign: "center", lineHeight: 16, paddingBottom: 8,
  },

  // Modal
  modalRoot: { flex: 1 },
  modalHeader: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 14, paddingBottom: 12,
    borderBottomWidth: 1,
  },
  modalCloseBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: "rgba(127,127,127,0.12)",
    alignItems: "center", justifyContent: "center",
  },
  modalTitle: { fontSize: 16, fontFamily: F.bold, letterSpacing: -0.2 },
  modalSub:   { fontSize: 11, fontFamily: F.medium, marginTop: 1 },
  lockBadge: {
    borderWidth: 1, borderRadius: 8,
    paddingVertical: 4, paddingHorizontal: 8,
  },
  wvLoader: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#fff" },
});
