import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

type Phase = "creating" | "opening" | "verifying" | "success" | "failed" | "cancelled";

const PLAN_LABELS: Record<string, string> = {
  pro:   "Pro",
  elite: "Elite",
};
const PLAN_ICONS: Record<string, string> = { pro: "⚡", elite: "⭐" };
const CYCLE_LABELS: Record<string, string> = { monthly: "Monthly", yearly: "Yearly" };
const PLAN_PRICES: Record<string, number> = {
  pro_monthly: 149, pro_yearly: 999,
  elite_monthly: 399, elite_yearly: 2999,
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
  }>();

  const plan  = params.plan  ?? "pro";
  const cycle = params.cycle ?? "monthly";
  const price = PLAN_PRICES[`${plan}_${cycle}`] ?? 0;

  const [phase,   setPhase]   = useState<Phase>("creating");
  const [errMsg,  setErrMsg]  = useState("");
  const [orderId, setOrderId] = useState(params.orderId ?? "");

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(scaleAnim, { toValue: 1, friction: 7,   useNativeDriver: true }),
    ]).start();

    if (params.orderId && params.paymentLink) {
      setOrderId(params.orderId);
      setPhase("opening");
      _openBrowser(params.paymentLink, params.orderId);
    } else {
      _createOrder();
    }
  }, []);

  async function _createOrder() {
    if (!user?.id) {
      setErrMsg("Please login to purchase a plan.");
      setPhase("failed");
      return;
    }
    setPhase("creating");
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 15000);
      const resp  = await fetch(`${API_BASE}/api/payment/create-order`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ user_id: user.id, plan, cycle }),
        signal:  ctrl.signal,
      });
      clearTimeout(timer);
      const data = await resp.json();
      if (!resp.ok || data.error) {
        setErrMsg(data.error ?? "Could not create order. Try again.");
        setPhase("failed");
        return;
      }
      const { order_id, payment_link } = data as { order_id: string; payment_link: string };
      setOrderId(order_id);
      setPhase("opening");
      await _openBrowser(payment_link, order_id);
    } catch (e: any) {
      setErrMsg(e?.message ?? "Network error. Check connection.");
      setPhase("failed");
    }
  }

  async function _openBrowser(link: string, oid: string) {
    try {
      await WebBrowser.openBrowserAsync(link, {
        presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
        toolbarColor:      isDark ? "#0c0818" : "#ffffff",
        controlsColor:     ac,
        showTitle:         true,
      });
    } catch { /* browser closed without payment */ }

    // After browser closes — verify payment
    setPhase("verifying");
    await _verifyPayment(oid);
  }

  async function _verifyPayment(oid: string) {
    if (!oid) { setPhase("cancelled"); return; }
    try {
      const ctrl  = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 12000);
      const resp  = await fetch(`${API_BASE}/api/payment/status/${oid}`, { signal: ctrl.signal });
      clearTimeout(timer);
      const data = await resp.json();

      if (data.status === "SUCCESS") {
        // Update local user state with new plan
        if (data.user && user) {
          const updated = { ...user, ...data.user };
          setUser(updated);
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
    setPhase("creating");
    setErrMsg("");
    _createOrder();
  }

  const phaseIcon: Record<Phase, string> = {
    creating:  "⏳",
    opening:   "💳",
    verifying: "🔍",
    success:   "🎉",
    failed:    "❌",
    cancelled: "🌙",
  };

  const phaseTitle: Record<Phase, string> = {
    creating:  "Creating Your Order…",
    opening:   "Opening Payment Page…",
    verifying: "Verifying Payment…",
    success:   "Plan Activated!",
    failed:    "Payment Failed",
    cancelled:  "Payment Cancelled",
  };

  const phaseSubtitle: Record<Phase, string> = {
    creating:  "Securely connecting to Cashfree…",
    opening:   "Complete payment in the browser",
    verifying: "Checking your payment status…",
    success:   `${PLAN_ICONS[plan]} ${PLAN_LABELS[plan]} ${CYCLE_LABELS[cycle]} plan is now active!`,
    failed:    errMsg || "Something went wrong. Please try again.",
    cancelled: "No payment was made. You can try again anytime.",
  };

  const isLoading = ["creating", "opening", "verifying"].includes(phase);

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Text style={{ fontSize: 18 }}>←</Text>
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>{t.paymentTitle}</Text>
        <View style={[s.cfBadge, { borderColor: isDark ? "rgba(245,158,11,0.3)" : "rgba(245,158,11,0.4)" }]}>
          <Text style={{ fontSize: 9, color: isDark ? "#f59e0b" : "#d97706", fontFamily: F.bold, letterSpacing: 0.5 }}>
            🔒 Cashfree
          </Text>
        </View>
      </View>

      <Animated.View style={[s.body, { opacity: fadeAnim, transform: [{ scale: scaleAnim }] }]}>

        {/* ── Order Summary Card ── */}
        <View style={[s.summaryCard, { backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(245,158,11,0.05)", borderColor: isDark ? "rgba(245,158,11,0.25)" : "rgba(245,158,11,0.2)" }]}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
            <Text style={{ fontSize: 28 }}>{PLAN_ICONS[plan] ?? "⭐"}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.planName, { color: isDark ? "#f59e0b" : "#d97706" }]}>
                {PLAN_LABELS[plan]} {CYCLE_LABELS[cycle]}
              </Text>
              <Text style={[s.planSub, { color: C.textMuted }]}>Cosmic Lens Premium</Text>
            </View>
            <Text style={[s.price, { color: isDark ? "#f59e0b" : "#d97706" }]}>₹{price.toLocaleString("en-IN")}</Text>
          </View>
          <View style={[s.sep, { backgroundColor: isDark ? "rgba(245,158,11,0.1)" : "rgba(245,158,11,0.08)" }]} />
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Text style={[s.detailLabel, { color: C.textMuted }]}>Billing Cycle</Text>
            <Text style={[s.detailVal, { color: C.textMid }]}>{CYCLE_LABELS[cycle]}</Text>
          </View>
          <View style={{ flexDirection: "row", justifyContent: "space-between", marginTop: 4 }}>
            <Text style={[s.detailLabel, { color: C.textMuted }]}>Payment Gateway</Text>
            <Text style={[s.detailVal, { color: C.textMid }]}>Cashfree (Sandbox)</Text>
          </View>
        </View>

        {/* ── Status Area ── */}
        <View style={[s.statusCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={s.statusIcon}>{phaseIcon[phase]}</Text>
          <Text style={[s.statusTitle, { color: C.text }]}>{phaseTitle[phase]}</Text>
          <Text style={[s.statusSub, { color: C.textMuted }]}>{phaseSubtitle[phase]}</Text>

          {isLoading && (
            <ActivityIndicator
              size="large"
              color={ac}
              style={{ marginTop: 20 }}
            />
          )}

          {phase === "success" && (
            <Pressable
              onPress={() => { Haptics.selectionAsync(); router.replace("/"); }}
              style={({ pressed }) => [s.primaryBtn, { backgroundColor: ac, opacity: pressed ? 0.85 : 1 }]}
            >
              <Text style={s.primaryBtnText}>Go to Home ✨</Text>
            </Pressable>
          )}

          {phase === "failed" && (
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

          {phase === "cancelled" && (
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
                <Text style={[s.secondaryBtnText, { color: C.textMid }]}>Cancel</Text>
              </Pressable>
            </View>
          )}
        </View>

        {/* ── Trust badges ── */}
        <View style={s.trustRow}>
          {["🔒 256-bit SSL", "🏦 Cashfree Secured", "🔄 Auto-renewal"].map(b => (
            <View key={b} style={[s.trustBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Text style={[s.trustText, { color: C.textMuted }]}>{b}</Text>
            </View>
          ))}
        </View>

        <Text style={[s.footer, { color: C.textMuted }]}>
          Payment is processed securely by Cashfree.{"\n"}
          Do not share OTP or card details with anyone.
        </Text>
      </Animated.View>
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
  headerTitle: { flex: 1, fontSize: 17, fontFamily: "Nunito_700Bold", letterSpacing: -0.3 },
  cfBadge: {
    borderWidth: 1, borderRadius: 10, paddingVertical: 4, paddingHorizontal: 8,
  },

  body: { flex: 1, paddingHorizontal: 16, paddingTop: 20, gap: 16 },

  summaryCard: {
    borderRadius: 16, borderWidth: 1.5, padding: 16, gap: 8,
  },
  planName:    { fontSize: 17, fontFamily: "Nunito_700Bold" },
  planSub:     { fontSize: 12, fontFamily: "Nunito_400Regular", marginTop: 1 },
  price:       { fontSize: 22, fontFamily: "Nunito_700Bold" },
  sep:         { height: 1, marginVertical: 6 },
  detailLabel: { fontSize: 12, fontFamily: "Nunito_500Medium" },
  detailVal:   { fontSize: 12, fontFamily: "Nunito_600SemiBold" },

  statusCard: {
    borderRadius: 16, borderWidth: 1, padding: 24,
    alignItems: "center", gap: 8,
  },
  statusIcon:  { fontSize: 44, marginBottom: 4 },
  statusTitle: { fontSize: 20, fontFamily: "Nunito_700Bold", textAlign: "center" },
  statusSub:   { fontSize: 13, fontFamily: "Nunito_400Regular", textAlign: "center", lineHeight: 20 },

  primaryBtn: {
    borderRadius: 14, paddingVertical: 14,
    alignItems: "center", justifyContent: "center", width: "100%",
  },
  primaryBtnText: { color: "#fff", fontSize: 15, fontFamily: "Nunito_700Bold" },

  secondaryBtn: {
    borderRadius: 14, paddingVertical: 13, borderWidth: 1,
    alignItems: "center", justifyContent: "center", width: "100%",
  },
  secondaryBtnText: { fontSize: 14, fontFamily: "Nunito_600SemiBold" },

  trustRow:  { flexDirection: "row", flexWrap: "wrap", gap: 6, justifyContent: "center" },
  trustBadge: {
    borderRadius: 8, borderWidth: 1,
    paddingVertical: 5, paddingHorizontal: 10,
  },
  trustText: { fontSize: 10, fontFamily: "Nunito_500Medium" },

  footer: {
    fontSize: 10, fontFamily: "Nunito_400Regular",
    textAlign: "center", lineHeight: 16, paddingBottom: 8,
  },
});
