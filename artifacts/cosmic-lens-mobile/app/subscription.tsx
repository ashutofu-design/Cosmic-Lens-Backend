import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
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
import { usePlan, startTrial, PRICES, TRIAL_DAYS } from "@/lib/subscription";

// ── Font aliases ─────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

type BillingCycle = "monthly" | "yearly";

// ── Plans definition (mirrors backend subscription_helper.py) ────────────────
const PLANS = [
  {
    key: "basic" as const,
    name: "Basic",
    accent: "#a78bfa",
    badge: null as string | null,
    monthlyPrice: PRICES.basic_monthly,
    yearlyPrice:  PRICES.basic_yearly,
    yearlySave:   25,
    icon: "star" as const,
    tagline: "Roz ke liye basics",
    features: [
      "10 AI Questions / day",
      "Marriage Compatibility (Basic)",
      "Love Compatibility (Basic)",
      "Career, Health, Finance — short summary",
      "Future Timeline — 1 month",
      "5 saved profiles",
    ],
    locked: [
      "Unlimited Questions",
      "Deep analysis with reasoning",
      "Full 6-month timeline",
      "Karmic insights & PDF report",
    ],
  },
  {
    key: "pro" as const,
    name: "Pro",
    accent: "#f59e0b",
    badge: "🔥 MOST POPULAR",
    monthlyPrice: PRICES.pro_monthly,
    yearlyPrice:  PRICES.pro_monthly,   // Pro is monthly-only — show monthly price even on yearly toggle
    yearlySave:   0,
    monthlyOnly:  true as const,
    icon: "zap" as const,
    tagline: "Full power Vedic insights",
    features: [
      "Unlimited AI Questions",
      "Marriage & Love — Full deep analysis",
      "Career, Health, Finance — Detailed",
      "Future Timeline — 6 months full",
      "D1 + D9 chart analysis",
      "Dasha (MD + AD + PD) full breakdown",
      "Karmic patterns & hidden insights",
      "PDF report download",
      "Unlimited saved profiles",
    ],
    locked: [],
  },
];

// ── Helpers ──────────────────────────────────────────────────────────────────
function planExpiryLabel(expiry: string | null | undefined): string {
  if (!expiry) return "";
  try {
    const d = new Date(expiry);
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch { return ""; }
}

function planLabel(plan: string): string {
  switch (plan) {
    case "trial": return "7-Day Trial — Active";
    case "basic": return "Basic Plan — Active";
    case "pro":   return "Pro Plan — Active";
    case "elite": return "Pro Plan — Active";
    default:      return "Free Plan";
  }
}

function planDot(plan: string): string {
  switch (plan) {
    case "trial": return "#22c55e";
    case "basic": return "#a78bfa";
    case "pro":   return "#f59e0b";
    case "elite": return "#f59e0b";
    default:      return "#64748b";
  }
}

// ── Trial banner ─────────────────────────────────────────────────────────────
function TrialBanner({
  eligible,
  isTrial,
  daysLeft,
  onStart,
  loading,
}: {
  eligible: boolean;
  isTrial:  boolean;
  daysLeft: number | null;
  onStart:  () => void;
  loading:  boolean;
}) {
  const C = useC();

  if (isTrial) {
    return (
      <View style={[tb.activeCard, { borderColor: "#22c55e60", backgroundColor: C.isDark ? "#16a34a10" : "#dcfce7" }]}>
        <View style={[tb.iconWrap, { backgroundColor: "#22c55e20" }]}>
          <Feather name="gift" size={16} color="#22c55e" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[tb.title, { color: C.text }]}>Trial Active 🎉</Text>
          <Text style={[tb.sub, { color: C.textMid }]}>
            {daysLeft != null && daysLeft > 0
              ? `${daysLeft} din bache hain — Basic features unlocked`
              : "Aaj trial khatam ho raha hai"}
          </Text>
        </View>
      </View>
    );
  }

  if (eligible) {
    return (
      <Pressable
        onPress={() => { try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {} ; onStart(); }}
        disabled={loading}
        style={({ pressed }) => [{ opacity: pressed || loading ? 0.85 : 1 }]}
      >
        <LinearGradient
          colors={["#16a34a", "#22c55e"]}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
          style={tb.startCard}
        >
          <View style={[tb.iconWrap, { backgroundColor: "rgba(255,255,255,0.18)" }]}>
            {loading
              ? <ActivityIndicator size="small" color="#fff" />
              : <Feather name="gift" size={16} color="#fff" />}
          </View>
          <View style={{ flex: 1 }}>
            <Text style={tb.startTitle}>₹1 — 7-Day Trial Start</Text>
            <Text style={tb.startSub}>Sirf ₹1 mein 7 din Basic features unlock — one-time</Text>
          </View>
          <Feather name="arrow-right" size={16} color="#fff" />
        </LinearGradient>
      </Pressable>
    );
  }

  return null;
}

// ── Plan Card ────────────────────────────────────────────────────────────────
function PlanCard({
  plan,
  cycle,
  isCurrent,
  onPress,
}: {
  plan: typeof PLANS[number];
  cycle: BillingCycle;
  isCurrent: boolean;
  onPress: () => void;
}) {
  const C = useC();
  const monthlyOnly = (plan as any).monthlyOnly === true;
  const effectiveCycle: BillingCycle = monthlyOnly ? "monthly" : cycle;
  const price = effectiveCycle === "yearly" ? plan.yearlyPrice : plan.monthlyPrice;
  const isPopular = plan.key === "pro";

  return (
    <View
      style={[
        pl.card,
        {
          borderColor: isPopular ? `${plan.accent}55` : `${plan.accent}30`,
          backgroundColor: C.bgCard,
          borderWidth: isPopular ? 2 : 1.5,
        },
      ]}
    >
      {plan.badge && (
        <View style={[pl.popularBadge, { backgroundColor: plan.accent }]}>
          <Text style={pl.popularBadgeText}>{plan.badge}</Text>
        </View>
      )}

      {/* Header row */}
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          <View style={[pl.iconWrap, { backgroundColor: `${plan.accent}18`, borderColor: `${plan.accent}30` }]}>
            <Feather name={plan.icon} size={16} color={plan.accent} />
          </View>
          <View>
            <Text style={[pl.planName, { color: plan.accent }]}>{plan.name}</Text>
            <Text style={[pl.planTagline, { color: C.textMuted }]}>{plan.tagline}</Text>
          </View>
        </View>
        {isCurrent && (
          <View style={[pl.activeBadge, { backgroundColor: `${plan.accent}20`, borderColor: `${plan.accent}40` }]}>
            <Text style={[pl.activeBadgeText, { color: plan.accent }]}>ACTIVE</Text>
          </View>
        )}
      </View>

      {/* Price */}
      <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 3, marginTop: 12, marginBottom: 4 }}>
        <Text style={[pl.priceCurrency, { color: plan.accent }]}>₹</Text>
        <Text style={[pl.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
        <Text style={[pl.pricePer, { color: C.textMuted }]}>/{effectiveCycle === "yearly" ? "year" : "month"}</Text>
      </View>

      {/* Monthly-only note for Pro */}
      {monthlyOnly && cycle === "yearly" && (
        <Text style={[pl.perMonthEq, { color: C.textMid, marginBottom: 6 }]}>
          Monthly billing only
        </Text>
      )}

      {/* Per-month equivalent for yearly */}
      {!monthlyOnly && effectiveCycle === "yearly" && (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <Text style={[pl.perMonthEq, { color: C.textMid }]}>
            ≈ ₹{Math.round(plan.yearlyPrice / 12).toLocaleString("en-IN")}/month
          </Text>
          <View style={pl.savePill}>
            <Text style={pl.saveText}>Save {plan.yearlySave}%</Text>
          </View>
        </View>
      )}

      <View style={[pl.sep, { backgroundColor: `${plan.accent}18` }]} />

      {/* Features */}
      <View style={{ gap: 9, marginBottom: 14 }}>
        {plan.features.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: `${plan.accent}22` }]}>
              <Feather name="check" size={10} color={plan.accent} />
            </View>
            <Text style={[pl.featureText, { color: C.text }]}>{f}</Text>
          </View>
        ))}
        {plan.locked.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: C.bgCard2 }]}>
              <Feather name="x" size={10} color={C.textMuted} />
            </View>
            <Text style={[pl.featureText, { color: C.textMuted, textDecorationLine: "line-through" }]}>{f}</Text>
          </View>
        ))}
      </View>

      {/* CTA */}
      {isCurrent ? (
        <View style={[pl.ctaActive, { borderColor: `${plan.accent}40`, backgroundColor: `${plan.accent}10` }]}>
          <Feather name="check-circle" size={14} color={plan.accent} />
          <Text style={[pl.ctaActiveText, { color: plan.accent }]}>Current Plan</Text>
        </View>
      ) : (
        <Pressable
          onPress={() => { try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {} ; onPress(); }}
          style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1 }]}
        >
          <LinearGradient
            colors={isPopular ? ["#d97706", "#f59e0b"] : ["#7c3aed", "#a78bfa"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={pl.ctaBtn}
          >
            <Feather name={isPopular ? "zap" : "star"} size={14} color="#fff" />
            <Text style={pl.ctaBtnText}>{isPopular ? "Upgrade to Pro 🔓" : "Get Basic"}</Text>
          </LinearGradient>
        </Pressable>
      )}
    </View>
  );
}

// ── Main Screen ──────────────────────────────────────────────────────────────
export default function SubscriptionScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const { user } = useUser();
  const isDark = C.isDark;
  const {
    plan,
    isTrial,
    trialEligible,
    daysRemaining,
    sub,
    refresh,
  } = usePlan();

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const [cycle, setCycle] = useState<BillingCycle>("monthly");
  const [trialLoading, setTrialLoading] = useState(false);

  const expiryISO   = isTrial ? sub.trial_expires_at : sub.plan_expires_at;
  const expiryLabel = planExpiryLabel(expiryISO);

  function handlePlanPress(planKey: string) {
    if (!user?.id) {
      Alert.alert("Login Required", "Please login to purchase a plan.");
      return;
    }
    if (planKey === plan) return;
    // Pro plan is monthly-only — force monthly cycle regardless of toggle.
    const effectiveCycle = planKey === "pro" ? "monthly" : cycle;
    router.push({ pathname: "/payment-webview", params: { plan: planKey, cycle: effectiveCycle } });
  }

  function handleStartTrial() {
    if (!user?.id || !user?.api_key) {
      Alert.alert("Login Required", "Please login to start your trial.");
      return;
    }
    // ₹1 paid trial — same payment flow as Basic/Pro, just plan='trial' cycle='weekly'.
    router.push({ pathname: "/payment-webview", params: { plan: "trial", cycle: "weekly" } });
  }

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* ── Header ── */}
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>Subscription</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>Apna plan choose karein</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: botPad + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero ── */}
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

          <View style={[s.currentChip, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={[s.chipDot, { backgroundColor: planDot(plan) }]} />
            <Text style={[s.currentChipText, { color: C.textMid }]}>
              {planLabel(plan)}
              {expiryLabel ? `  ·  till ${expiryLabel}` : ""}
            </Text>
          </View>
        </LinearGradient>

        {/* ── Trial banner ── */}
        <TrialBanner
          eligible={trialEligible}
          isTrial={isTrial}
          daysLeft={daysRemaining}
          onStart={handleStartTrial}
          loading={trialLoading}
        />

        {/* ── Billing toggle ── */}
        <View style={[s.cycleRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          {(["monthly", "yearly"] as BillingCycle[]).map(c => (
            <Pressable
              key={c}
              onPress={() => { setCycle(c); try { Haptics.selectionAsync(); } catch {} }}
              style={[s.cycleBtn, cycle === c && s.cycleBtnActive]}
            >
              <Text style={[s.cycleTxt, { color: cycle === c ? "#f59e0b" : C.textMuted }]}>
                {c === "monthly" ? "Monthly" : "Yearly"}
              </Text>
              {c === "yearly" && (
                <View style={s.savePillTop}>
                  <Text style={s.savePillTopTxt}>SAVE UPTO 38%</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>

        {/* ── Plan cards ── */}
        <View style={s.plansWrap}>
          {PLANS.map(p => (
            <PlanCard
              key={p.key}
              plan={p}
              cycle={cycle}
              isCurrent={p.key === plan}
              onPress={() => handlePlanPress(p.key)}
            />
          ))}
        </View>

        {/* ── Comparison Table ── */}
        <View style={[s.compareCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.compareTitle, { color: C.text }]}>Basic vs Pro — Quick Compare</Text>
          {[
            { label: "AI Questions", basic: "10/day",         pro: "Unlimited" },
            { label: "Marriage Compat", basic: "Score + summary", pro: "Full breakdown" },
            { label: "Future Timeline", basic: "1 month",     pro: "6 months" },
            { label: "Dasha Analysis",  basic: "Overview",    pro: "MD + AD + PD" },
            { label: "Karmic Insights", basic: "—",            pro: "✓ Included" },
            { label: "PDF Report",      basic: "—",            pro: "✓ Download" },
            { label: "Saved Profiles",  basic: "5",            pro: "Unlimited" },
          ].map((row, i) => (
            <View key={row.label} style={[s.compareRow, i > 0 && { borderTopWidth: 1, borderTopColor: C.border }]}>
              <Text style={[s.compareLabel, { color: C.textMid }]}>{row.label}</Text>
              <View style={s.compareCells}>
                <Text style={[s.compareCell, { color: C.textMid }]}>{row.basic}</Text>
                <Text style={[s.compareCell, { color: "#f59e0b", fontFamily: F.bold }]}>{row.pro}</Text>
              </View>
            </View>
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

        {/* ── Footer ── */}
        <Text style={[s.footerNote, { color: C.textMuted }]}>
          • ₹1 — {TRIAL_DAYS}-day trial (one-time, naye users ke liye){"\n"}
          • Subscription monthly ya yearly renew hoti hai{"\n"}
          • Kabhi bhi cancel kar sakte hain{"\n"}
          • Powered by Cashfree — PCI DSS compliant
        </Text>
      </ScrollView>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────
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

  scroll: { paddingHorizontal: 16, gap: 14, paddingTop: 16 },

  heroBanner: { borderRadius: 20, padding: 20, alignItems: "center", gap: 10 },
  heroIconRow: { flexDirection: "row", gap: 10, marginBottom: 4 },
  heroIcon: {
    width: 48, height: 48, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  heroTitle: {
    fontSize: 22, fontFamily: F.bold, textAlign: "center",
    letterSpacing: -0.5, lineHeight: 30,
  },
  heroSub: { fontSize: 13, fontFamily: F.regular, textAlign: "center" },
  currentChip: {
    flexDirection: "row", alignItems: "center", gap: 7,
    paddingVertical: 7, paddingHorizontal: 14,
    borderRadius: 20, borderWidth: 1, marginTop: 4,
  },
  chipDot: { width: 7, height: 7, borderRadius: 3.5 },
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
  savePillTop: {
    backgroundColor: "rgba(74,222,128,0.18)", borderRadius: 6,
    paddingVertical: 2, paddingHorizontal: 6,
  },
  savePillTopTxt: { color: "#16a34a", fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5 },

  plansWrap: { gap: 12 },

  compareCard: {
    borderRadius: 16, borderWidth: 1, padding: 16, gap: 4,
  },
  compareTitle: { fontSize: 14, fontFamily: F.bold, marginBottom: 8 },
  compareRow: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 10, gap: 12,
  },
  compareLabel: { flex: 1.2, fontSize: 12, fontFamily: F.semibold },
  compareCells: { flex: 1.5, flexDirection: "row", justifyContent: "space-between", gap: 8 },
  compareCell:  { flex: 1, fontSize: 11.5, fontFamily: F.medium, textAlign: "center" },

  footerNote: {
    fontSize: 11, fontFamily: F.regular,
    lineHeight: 18, textAlign: "center",
    paddingHorizontal: 8, marginBottom: 8, marginTop: 4,
  },

  payBadge: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderRadius: 12, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 14,
  },
  payBadgeText: { fontSize: 12, fontFamily: F.medium, flex: 1 },
});

// ── Trial banner styles ──────────────────────────────────────────────────────
const tb = StyleSheet.create({
  startCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 14, padding: 14,
  },
  activeCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 14, borderWidth: 1, padding: 14,
  },
  iconWrap: {
    width: 36, height: 36, borderRadius: 10,
    alignItems: "center", justifyContent: "center",
  },
  startTitle: { color: "#fff", fontSize: 14, fontFamily: F.bold, letterSpacing: -0.2 },
  startSub:   { color: "rgba(255,255,255,0.85)", fontSize: 11.5, fontFamily: F.regular, marginTop: 2 },
  title:      { fontSize: 14, fontFamily: F.bold, letterSpacing: -0.2 },
  sub:        { fontSize: 11.5, fontFamily: F.regular, marginTop: 2 },
});

// ── Plan card styles ─────────────────────────────────────────────────────────
const pl = StyleSheet.create({
  card: { borderRadius: 16, padding: 16, position: "relative" },
  popularBadge: {
    position: "absolute", top: -10, right: 16,
    paddingVertical: 4, paddingHorizontal: 10, borderRadius: 8,
    zIndex: 2,
  },
  popularBadgeText: {
    color: "#fff", fontSize: 10, fontFamily: F.bold, letterSpacing: 0.5,
  },
  iconWrap: {
    width: 34, height: 34, borderRadius: 10,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  planName:    { fontSize: 18, fontFamily: F.bold, letterSpacing: -0.2 },
  planTagline: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },

  activeBadge: {
    borderWidth: 1, borderRadius: 20,
    paddingVertical: 3, paddingHorizontal: 9,
  },
  activeBadgeText: { fontSize: 9, fontFamily: F.bold, letterSpacing: 0.8 },

  price:         { fontSize: 30, fontFamily: F.bold, lineHeight: 34 },
  priceCurrency: { fontSize: 17, fontFamily: F.bold, paddingBottom: 4 },
  pricePer:      { fontSize: 12, fontFamily: F.medium, paddingBottom: 5 },

  perMonthEq: { fontSize: 11, fontFamily: F.medium },
  savePill: {
    backgroundColor: "rgba(74,222,128,0.15)", borderRadius: 6,
    paddingVertical: 2, paddingHorizontal: 6,
  },
  saveText: { color: "#16a34a", fontSize: 10, fontFamily: F.bold, letterSpacing: 0.3 },

  sep: { height: 1, marginVertical: 14 },

  featureRow: { flexDirection: "row", alignItems: "center", gap: 9 },
  featureDot: {
    width: 18, height: 18, borderRadius: 5,
    alignItems: "center", justifyContent: "center",
  },
  featureText: { fontSize: 12.5, fontFamily: F.medium, flex: 1 },

  ctaBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 13, borderRadius: 12,
  },
  ctaBtnText: { color: "#fff", fontSize: 14, fontFamily: F.bold },

  ctaActive: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 13, borderRadius: 12,
    borderWidth: 1,
  },
  ctaActiveText: { fontSize: 14, fontFamily: F.bold },
});
