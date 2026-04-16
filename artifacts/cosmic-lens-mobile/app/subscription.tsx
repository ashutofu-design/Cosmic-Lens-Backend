import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

// ── Font aliases ───────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

// ── Plans data ─────────────────────────────────────────────────────────────────
type BillingCycle = "monthly" | "yearly";

const PLANS = [
  {
    key: "free", name: "Free",
    accent: "#64748b", accentBg: "rgba(71,85,105,0.08)",
    border: "rgba(71,85,105,0.22)", badge: null,
    monthlyPrice: 0, yearlyPrice: 0,
    cta: "Current Plan", ctaActive: false,
    icon: "circle" as const,
    features: ["1 Profile", "Basic Kundli Chart", "3 AI Questions / day", "Demo Insights", "Basic Planet View"],
    featureOff: ["Full Dasha Timeline", "7-Day Forecast", "PDF Report", "Kundli Milan"],
  },
  {
    key: "pro", name: "Pro",
    accent: "#f59e0b", accentBg: "rgba(245,158,11,0.05)",
    border: "rgba(245,158,11,0.30)", badge: "POPULAR",
    monthlyPrice: 149, yearlyPrice: 999, yearlySave: 44,
    cta: "Get Pro", ctaActive: true,
    icon: "zap" as const,
    features: ["5 Profiles", "Full Kundli + Dasha Timeline", "Unlimited AI Chat", "7-Day Forecast", "Planet Positions + Nakshatra", "Monthly Category Insights"],
    featureOff: ["PDF Report", "Kundli Milan"],
  },
  {
    key: "elite", name: "Elite",
    accent: "#a78bfa", accentBg: "rgba(167,139,250,0.05)",
    border: "rgba(167,139,250,0.30)", badge: "PREMIUM",
    monthlyPrice: 399, yearlyPrice: 2999, yearlySave: 37,
    cta: "Get Elite", ctaActive: true,
    icon: "star" as const,
    features: ["Unlimited Profiles", "All Pro Features", "Monthly PDF Report", "Kundli Milan (Vivah Yog)", "Career & Finance Deep Analysis", "Priority Astrologer Chat", "Yearly Forecast"],
    featureOff: [],
  },
];

// ── Plan Card ──────────────────────────────────────────────────────────────────
function PlanCard({ plan, cycle, isCurrent, onPress }: {
  plan: typeof PLANS[0]; cycle: BillingCycle;
  isCurrent: boolean; onPress: () => void;
}) {
  const C = useC();
  const price  = cycle === "yearly" ? plan.yearlyPrice : plan.monthlyPrice;
  const isFree = plan.key === "free";

  return (
    <View style={[pl.card, { borderColor: C.isDark ? plan.border : `${plan.accent}30`, backgroundColor: C.isDark ? plan.accentBg : C.bgCard }, isCurrent && pl.cardCurrent]}>
      {/* Top row */}
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <View style={[pl.iconWrap, { backgroundColor: `${plan.accent}18`, borderColor: `${plan.accent}30` }]}>
            <Feather name={plan.icon} size={14} color={plan.accent} />
          </View>
          <Text style={[pl.planName, { color: plan.accent }]}>{plan.name}</Text>
          {isCurrent && (
            <View style={[pl.badge, { backgroundColor: `${plan.accent}20`, borderColor: `${plan.accent}40` }]}>
              <Text style={[pl.badgeText, { color: plan.accent }]}>ACTIVE</Text>
            </View>
          )}
        </View>
        {plan.badge && !isCurrent && (
          <View style={[pl.badge, { backgroundColor: `${plan.accent}15`, borderColor: `${plan.accent}35` }]}>
            <Text style={[pl.badgeText, { color: plan.accent }]}>{plan.badge}</Text>
          </View>
        )}
      </View>

      {/* Price */}
      <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 3, marginBottom: 6 }}>
        {isFree ? (
          <Text style={[pl.price, { color: plan.accent }]}>FREE</Text>
        ) : (
          <>
            <Text style={[pl.priceCurrency, { color: plan.accent }]}>₹</Text>
            <Text style={[pl.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
            <Text style={pl.pricePer}>/{cycle === "yearly" ? "year" : "month"}</Text>
          </>
        )}
      </View>

      {/* Save pill */}
      {cycle === "yearly" && !isFree && (plan as any).yearlySave && (
        <View style={pl.savePill}>
          <Feather name="tag" size={9} color="#4ade80" />
          <Text style={pl.saveText}>Save {(plan as any).yearlySave}% vs monthly</Text>
        </View>
      )}

      <View style={[pl.sep, { backgroundColor: `${plan.accent}18` }]} />

      {/* Features */}
      <View style={{ gap: 7, marginBottom: 14 }}>
        {plan.features.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: `${plan.accent}22` }]}>
              <Feather name="check" size={9} color={plan.accent} />
            </View>
            <Text style={pl.featureText}>{f}</Text>
          </View>
        ))}
        {plan.featureOff.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: C.bgCard2 }]}>
              <Feather name="minus" size={9} color={C.textMuted} />
            </View>
            <Text style={[pl.featureText, { color: C.textMuted }]}>{f}</Text>
          </View>
        ))}
      </View>

      {/* CTA */}
      {plan.ctaActive ? (
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onPress(); }}
          style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1 }]}
        >
          <LinearGradient
            colors={plan.key === "pro" ? ["#d97706", "#f59e0b"] : ["#7c3aed", "#a78bfa"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={pl.ctaBtn}
          >
            <Feather name={plan.icon} size={14} color="#fff" />
            <Text style={pl.ctaBtnText}>{plan.cta}</Text>
          </LinearGradient>
        </Pressable>
      ) : (
        <View style={[pl.ctaBtnOutline, { borderColor: `${plan.accent}30` }]}>
          <Feather name="check-circle" size={14} color={plan.accent} />
          <Text style={[pl.ctaBtnText, { color: plan.accent }]}>{plan.cta}</Text>
        </View>
      )}
    </View>
  );
}

// ── Plan key → expiry label ─────────────────────────────────────────────────
function planExpiryLabel(expiry: string | null | undefined): string {
  if (!expiry) return "";
  try {
    const d = new Date(expiry);
    return `Expires ${d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}`;
  } catch { return ""; }
}

// ── Main Screen ────────────────────────────────────────────────────────────────
export default function SubscriptionScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const t      = useT();
  const { user } = useUser();
  const isDark = C.isDark;

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const [cycle, setCycle] = useState<BillingCycle>("monthly");

  // Derive real plan from user object
  const activePlan = user?.plan ?? (user?.is_pro ? "pro" : "free");
  const isPro      = activePlan !== "free";
  const expiryLabel = planExpiryLabel(user?.plan_expiry);

  const planDotColor: Record<string, string> = {
    free:  "#64748b",
    pro:   "#f59e0b",
    elite: "#a78bfa",
  };

  function handlePlanPress(planKey: string) {
    if (!user?.id) {
      Alert.alert("Login Required", "Please login to purchase a plan.");
      return;
    }
    if (planKey === activePlan) return;
    router.push({ pathname: "/payment-webview", params: { plan: planKey, cycle } });
  }

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* ── Header ── */}
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{t.subscriptionTitle}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>Apna plan choose karein</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: botPad + 32 }]}
        showsVerticalScrollIndicator={false}
      >

        {/* ── Hero banner ── */}
        <LinearGradient
          colors={isDark ? ["#1a1330", "#0c0818"] : ["#EEF2FF", "#F5F7FB"]}
          style={s.heroBanner}
        >
          <View style={s.heroIconRow}>
            <View style={[s.heroIcon, { backgroundColor: isDark ? "rgba(245,158,11,0.12)" : "rgba(245,158,11,0.10)" }]}>
              <Text style={{ fontSize: 22 }}>⭐</Text>
            </View>
            <View style={[s.heroIcon, { backgroundColor: isDark ? "rgba(99,102,241,0.15)" : "rgba(99,102,241,0.09)" }]}>
              <Text style={{ fontSize: 22 }}>🔭</Text>
            </View>
            <View style={[s.heroIcon, { backgroundColor: isDark ? "rgba(245,158,11,0.12)" : "rgba(245,158,11,0.10)" }]}>
              <Text style={{ fontSize: 22 }}>✨</Text>
            </View>
          </View>
          <Text style={[s.heroTitle, { color: C.text }]}>
            Poori Vedic Astrology{"\n"}Unlock Karein
          </Text>
          <Text style={[s.heroSub, { color: C.textMuted }]}>
            Kundli, Dasha, AI Chat, Forecast — sab ek jagah
          </Text>

          {/* Current plan chip */}
          <View style={[s.currentChip, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={[s.freeDot, { backgroundColor: planDotColor[activePlan] }]} />
            <Text style={[s.currentChipText, { color: C.textMid }]}>
              {activePlan === "elite" ? "Elite Plan — Active" :
               activePlan === "pro"   ? "Pro Plan — Active"  : "Free Plan — Active"}
              {expiryLabel ? `  ·  ${expiryLabel}` : ""}
            </Text>
          </View>
        </LinearGradient>

        {/* ── Billing toggle ── */}
        <View style={[s.cycleRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          {(["monthly", "yearly"] as BillingCycle[]).map(c => (
            <Pressable
              key={c}
              onPress={() => { setCycle(c); Haptics.selectionAsync(); }}
              style={[s.cycleBtn, cycle === c && s.cycleBtnActive]}
            >
              <Text style={[s.cycleTxt, { color: cycle === c ? "#f59e0b" : C.textMuted }]}>
                {c === "monthly" ? "Monthly" : "Yearly"}
              </Text>
              {c === "yearly" && (
                <View style={s.savePill}>
                  <Text style={s.savePillTxt}>44% OFF</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>

        {/* ── Plan cards ── */}
        <View style={s.plansWrap}>
          {PLANS.map(plan => (
            <PlanCard
              key={plan.key}
              plan={plan}
              cycle={cycle}
              isCurrent={plan.key === activePlan}
              onPress={() => handlePlanPress(plan.key)}
            />
          ))}
        </View>

        {/* ── Cashfree badge ── */}
        <View style={[s.payBadge, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={{ fontSize: 14 }}>🔒</Text>
          <Text style={[s.payBadgeText, { color: C.textMid }]}>
            Secured by{" "}
            <Text style={{ color: isDark ? "#f59e0b" : "#d97706", fontFamily: F.bold }}>Cashfree</Text>
            {" "}— India's trusted payment gateway
          </Text>
        </View>

        {/* ── Benefits grid ── */}
        <View style={[s.benefitsCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.benefitsTitle, { color: C.text }]}>Pro aur Elite ke fayde</Text>
          <View style={s.benefitsGrid}>
            {[
              { icon: "🔮", text: "Full Dasha Timeline" },
              { icon: "🤖", text: "Unlimited AI Chat" },
              { icon: "📊", text: "7-Day Forecast" },
              { icon: "💍", text: "Kundli Milan" },
              { icon: "📄", text: "PDF Report" },
              { icon: "🌟", text: "Nakshatra Analysis" },
            ].map(b => (
              <View key={b.text} style={[s.benefitItem, { backgroundColor: isDark ? "rgba(245,158,11,0.05)" : C.warningBg, borderColor: isDark ? "rgba(245,158,11,0.20)" : C.warningBorder }]}>
                <Text style={{ fontSize: 18 }}>{b.icon}</Text>
                <Text style={[s.benefitText, { color: C.textMid }]}>{b.text}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* ── Footer note ── */}
        <Text style={[s.footerNote, { color: C.textMuted }]}>
          • Subscription monthly ya yearly renew hoti hai{"\n"}
          • Kabhi bhi cancel kar sakte hain{"\n"}
          • Powered by Cashfree — PCI DSS compliant
        </Text>

      </ScrollView>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root: { flex: 1 },

  header: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.06)",
    alignItems: "center", justifyContent: "center",
  },
  headerTitle: { fontSize: 18, fontFamily: F.bold, letterSpacing: -0.3 },
  headerSub:   { fontSize: 11, fontFamily: F.regular, marginTop: 2 },

  scroll: { paddingHorizontal: 16, gap: 16, paddingTop: 16 },

  heroBanner: {
    borderRadius: 20, padding: 20, alignItems: "center", gap: 10,
  },
  heroIconRow: { flexDirection: "row", gap: 10, marginBottom: 4 },
  heroIcon: {
    width: 48, height: 48, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  heroTitle: {
    fontSize: 22, fontFamily: F.bold, textAlign: "center",
    letterSpacing: -0.5, lineHeight: 30,
  },
  heroSub: {
    fontSize: 13, fontFamily: F.regular, textAlign: "center",
  },
  currentChip: {
    flexDirection: "row", alignItems: "center", gap: 7,
    paddingVertical: 7, paddingHorizontal: 14,
    borderRadius: 20, borderWidth: 1, marginTop: 4,
  },
  freeDot: { width: 7, height: 7, borderRadius: 3.5, backgroundColor: "#64748b" },
  currentChipText: { fontSize: 12, fontFamily: F.semibold },

  cycleRow: {
    flexDirection: "row", borderRadius: 14,
    borderWidth: 1, padding: 4, gap: 4,
  },
  cycleBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 11, borderRadius: 10,
  },
  cycleBtnActive: {
    backgroundColor: "rgba(245,158,11,0.10)",
    borderWidth: 1, borderColor: "rgba(245,158,11,0.28)",
  },
  cycleTxt: { fontSize: 13, fontFamily: F.semibold },
  savePill: {
    backgroundColor: "rgba(74,222,128,0.15)", borderRadius: 6,
    paddingVertical: 2, paddingHorizontal: 6,
  },
  savePillTxt: { color: "#4ade80", fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5 },

  plansWrap: { gap: 12 },

  benefitsCard: {
    borderRadius: 16, borderWidth: 1, padding: 16, gap: 12,
  },
  benefitsTitle: { fontSize: 14, fontFamily: F.bold },
  benefitsGrid: {
    flexDirection: "row", flexWrap: "wrap", gap: 8,
  },
  benefitItem: {
    width: "47%", borderRadius: 12, borderWidth: 1,
    padding: 12, alignItems: "center", gap: 6,
  },
  benefitText: { fontSize: 11, fontFamily: F.medium, textAlign: "center" },

  footerNote: {
    fontSize: 11, fontFamily: F.regular,
    lineHeight: 18, textAlign: "center",
    paddingHorizontal: 8, marginBottom: 8,
  },

  payBadge: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderRadius: 12, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 14,
  },
  payBadgeText: { fontSize: 12, fontFamily: F.medium, flex: 1 },
});

// ── Plan card styles ───────────────────────────────────────────────────────────
const pl = StyleSheet.create({
  card: { borderRadius: 16, borderWidth: 1.5, padding: 16 },
  cardCurrent: { borderWidth: 1 },
  iconWrap: {
    width: 28, height: 28, borderRadius: 8,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  planName:    { fontSize: 16, fontFamily: F.bold, letterSpacing: -0.2 },
  badge: {
    borderWidth: 1, borderRadius: 20,
    paddingVertical: 2, paddingHorizontal: 8,
  },
  badgeText: { fontSize: 8.5, fontFamily: F.bold, letterSpacing: 0.8 },
  price:         { fontSize: 26, fontFamily: F.bold, lineHeight: 30 },
  priceCurrency: { fontSize: 15, fontFamily: F.bold, paddingBottom: 3 },
  pricePer:      { color: "#475569", fontSize: 12, fontFamily: F.medium, paddingBottom: 4 },
  savePill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(74,222,128,0.1)", borderRadius: 6,
    paddingVertical: 3, paddingHorizontal: 8, alignSelf: "flex-start",
  },
  saveText: { color: "#4ade80", fontSize: 10, fontFamily: F.semibold },
  sep: { height: 1, marginVertical: 14 },
  featureRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  featureDot: {
    width: 18, height: 18, borderRadius: 5,
    alignItems: "center", justifyContent: "center",
  },
  featureText: { color: "#94a3b8", fontSize: 12, fontFamily: F.medium, flex: 1 },
  ctaBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 13, borderRadius: 12,
  },
  ctaBtnOutline: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 13, borderRadius: 12,
    borderWidth: 1, backgroundColor: "rgba(255,255,255,0.03)",
  },
  ctaBtnText: { color: "#fff", fontSize: 14, fontFamily: F.bold },
});
