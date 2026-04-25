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
import { useT } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import { usePlan, startTrial, PRICES, TRIAL_DAYS } from "@/lib/subscription";
import { Linking } from "react-native";

// ── Font aliases ─────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
} as const;

// ── Plans definition (mirrors backend subscription_helper.py) ────────────────
const PLANS = [
  {
    key: "basic" as const,
    nameKey: "sub_planBasicName",
    accent: "#a78bfa",
    badge: null as string | null,
    monthlyPrice: PRICES.basic_monthly,
    icon: "star" as const,
    taglineKey: "planBasicTagline",
    features: ["sub_bF1", "sub_bF2", "sub_bF3", "sub_bF4", "sub_bF5", "sub_bF6"],
    locked:   ["sub_bL1", "sub_bL2", "sub_bL3", "sub_bL4"],
  },
  {
    key: "pro" as const,
    nameKey: "sub_planProName",
    accent: "#f59e0b",
    badge: "🔥 MOST POPULAR",
    monthlyPrice: PRICES.pro_monthly,
    icon: "zap" as const,
    taglineKey: "planProTagline",
    features: ["sub_pF1", "sub_pF2", "sub_pF3", "sub_pF4", "sub_pF5", "sub_pF6", "sub_pF7", "sub_pF8", "sub_pF9"],
    locked: [] as string[],
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

// ── Plan Card ────────────────────────────────────────────────────────────────
function PlanCard({
  plan,
  isCurrent,
  onPress,
}: {
  plan: typeof PLANS[number];
  isCurrent: boolean;
  onPress: () => void;
}) {
  const C = useC();
  const t = useT();
  const price = plan.monthlyPrice;
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
            <Text style={[pl.planName, { color: plan.accent }]}>{(t as unknown as Record<string, string>)[plan.nameKey] ?? plan.key}</Text>
            <Text style={[pl.planTagline, { color: C.textMuted }]}>
              {plan.taglineKey === "planBasicTagline" ? t.planBasicTagline
                : plan.taglineKey === "planProTagline" ? t.planProTagline
                : ""}
            </Text>
          </View>
        </View>
        {isCurrent && (
          <View style={[pl.activeBadge, { backgroundColor: `${plan.accent}20`, borderColor: `${plan.accent}40` }]}>
            <Text style={[pl.activeBadgeText, { color: plan.accent }]}>{t.sub_active}</Text>
          </View>
        )}
      </View>

      {/* Price */}
      <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 3, marginTop: 12, marginBottom: 10 }}>
        <Text style={[pl.priceCurrency, { color: plan.accent }]}>₹</Text>
        <Text style={[pl.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
        <Text style={[pl.pricePer, { color: C.textMuted }]}>/month</Text>
      </View>

      <View style={[pl.sep, { backgroundColor: `${plan.accent}18` }]} />

      {/* Features */}
      <View style={{ gap: 9, marginBottom: 14 }}>
        {plan.features.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: `${plan.accent}22` }]}>
              <Feather name="check" size={10} color={plan.accent} />
            </View>
            <Text style={[pl.featureText, { color: C.text }]}>{(t as unknown as Record<string, string>)[f] ?? f}</Text>
          </View>
        ))}
        {plan.locked.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: C.bgCard2 }]}>
              <Feather name="x" size={10} color={C.textMuted} />
            </View>
            <Text style={[pl.featureText, { color: C.textMuted, textDecorationLine: "line-through" }]}>{(t as unknown as Record<string, string>)[f] ?? f}</Text>
          </View>
        ))}
      </View>

      {/* CTA */}
      {isCurrent ? (
        <View style={[pl.ctaActive, { borderColor: `${plan.accent}40`, backgroundColor: `${plan.accent}10` }]}>
          <Feather name="check-circle" size={14} color={plan.accent} />
          <Text style={[pl.ctaActiveText, { color: plan.accent }]}>{t.currentPlan}</Text>
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
            <Text style={pl.ctaBtnText}>{isPopular ? t.sub_upgradeBtn : t.sub_getBasic}</Text>
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
  const t      = useT();
  const { user } = useUser();
  const isDark = C.isDark;
  const {
    plan,
    isTrial,
    sub,
  } = usePlan();

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const expiryISO   = isTrial ? sub.trial_expires_at : sub.plan_expires_at;
  const expiryLabel = planExpiryLabel(expiryISO);

  function _notify(title: string, msg: string) {
    if (Platform.OS === "web" && typeof window !== "undefined") {
      try { (window as any).alert(`${title}\n\n${msg}`); } catch {}
    } else {
      Alert.alert(title, msg);
    }
  }

  function handlePlanPress(planKey: string) {
    console.log("[Subscription] handlePlanPress:", planKey, "user.id=", user?.id, "current plan=", plan);
    if (!user?.id) {
      _notify("Login Required", "Please login to purchase a plan.");
      router.push("/login");
      return;
    }
    if (planKey === plan) {
      _notify("Already Active", `You are already on the ${planKey} plan.`);
      return;
    }
    router.push({ pathname: "/payment-webview", params: { plan: planKey, cycle: "monthly" } });
  }

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* ── Header ── */}
      <View style={[s.header, { paddingTop: topPad + 6, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={8}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>{t.subscription}</Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>{t.chooseYourPlan}</Text>
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
            {t.unlockVedicTitle}
          </Text>
          <Text style={[s.heroSub, { color: C.textMuted }]}>
            Kundli · Dasha · Jyotish Chat · Forecast
          </Text>

          <View style={[s.currentChip, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={[s.chipDot, { backgroundColor: planDot(plan) }]} />
            <Text style={[s.currentChipText, { color: C.textMid }]}>
              {planLabel(plan)}
              {expiryLabel ? `  ·  till ${expiryLabel}` : ""}
            </Text>
          </View>
        </LinearGradient>

        {/* Trial banner removed per user request — trial is now offered as a regular plan card */}

        {/* ── Plan cards ── */}
        <View style={s.plansWrap}>
          {PLANS.map(p => (
            <PlanCard
              key={p.key}
              plan={p}
              isCurrent={p.key === plan}
              onPress={() => handlePlanPress(p.key)}
            />
          ))}
        </View>

        {/* ── AstroVastu Pricing Card (one-time purchases — separate from subscription) ── */}
        <AstroVastuPricingCard C={C} />


        {/* ── Comparison Table ── */}
        <View style={[s.compareCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.compareTitle, { color: C.text }]}>Basic vs Pro — Quick Compare</Text>
          {[
            { label: t.sub_cmpJyotishQ, basic: "10/day",         pro: "Unlimited" },
            { label: t.sub_cmpMarriage, basic: "Score + summary", pro: "Full breakdown" },
            { label: t.sub_cmpTimeline, basic: "1 month",     pro: "6 months" },
            { label: t.sub_cmpDasha,    basic: "Overview",    pro: "MD + AD + PD" },
            { label: t.sub_cmpKarmic,   basic: "—",            pro: "✓ Included" },
            { label: t.sub_cmpPdf,      basic: "—",            pro: "✓ Download" },
            { label: t.sub_cmpProfiles, basic: "5",            pro: "Unlimited" },
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
          • ₹1 — {TRIAL_DAYS}-day trial (one-time, for new users){"\n"}
          • Subscription renews every month{"\n"}
          • Cancel anytime{"\n"}
          • Powered by Cashfree — PCI DSS compliant
        </Text>

        {/* ── Legal links ── */}
        <View style={{ flexDirection: "row", justifyContent: "center", flexWrap: "wrap", marginTop: 18, gap: 14 }}>
          <Pressable onPress={() => Linking.openURL(`${API_BASE}/legal#refund`)}>
            <Text style={{ color: "#8b5cf6", fontFamily: F.semibold, fontSize: 13, textDecorationLine: "underline" }}>
              Refund Policy
            </Text>
          </Pressable>
          <Text style={{ color: C.textMuted, fontSize: 13 }}>·</Text>
          <Pressable onPress={() => Linking.openURL(`${API_BASE}/legal#terms`)}>
            <Text style={{ color: "#8b5cf6", fontFamily: F.semibold, fontSize: 13, textDecorationLine: "underline" }}>
              Terms
            </Text>
          </Pressable>
          <Text style={{ color: C.textMuted, fontSize: 13 }}>·</Text>
          <Pressable onPress={() => Linking.openURL(`${API_BASE}/legal#privacy`)}>
            <Text style={{ color: "#8b5cf6", fontFamily: F.semibold, fontSize: 13, textDecorationLine: "underline" }}>
              Privacy
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

// ── AstroVastu Pricing Card ──────────────────────────────────────────────────
// Separate from subscription tiers — these are ONE-TIME purchases per scan/property.
// All prices are listed transparently so user knows the full Vastu pricing ladder.
function AstroVastuPricingCard({ C }: { C: any }) {
  const t = useT();
  const goAstroVastu = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    router.push("/astrovastu" as any);
  };

  const tiers = [
    { emoji: "🧭", name: "AstroVastu Compass + Guide", price: t.sub_free,      sub: t.sub_alwaysFree,                color: "#10b981" },
    { emoji: "🔮", name: "1 Room — Quick Check",        price: "₹199",     sub: "One-time",                   color: "#a78bfa" },
    { emoji: "🏠", name: "3 Rooms — Spot Check Bundle", price: "₹499",     sub: "One-time · Save ₹98",        color: "#a78bfa" },
    { emoji: "🌟", name: "Full Home Advanced",          price: "₹2,999",   sub: "Lifetime per property",      color: "#f9d76b", best: true },
    { emoji: "🏪", name: "Shop Vastu",                  price: "₹999",     sub: "One-time scan",              color: "#06b6d4" },
    { emoji: "🏢", name: "Office Vastu",                price: "₹1,499",   sub: "One-time scan",              color: "#06b6d4" },
    { emoji: "🏭", name: "Factory Vastu",               price: "₹2,999",   sub: "One-time scan",              color: "#06b6d4" },
  ];

  return (
    <View style={[av.wrap, { backgroundColor: C.bgCard, borderColor: "#f9d76b" }]}>
      {/* Premium gold header */}
      <LinearGradient
        colors={["#f9d76b22", "#f59e0b15", "transparent"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={av.headerGrad}
      >
        <View style={av.titleRow}>
          <Feather name="award" size={16} color="#f9d76b" />
          <Text style={[av.title, { color: C.text }]}>{t.sub_avPricing}</Text>
          <View style={av.premBadge}>
            <Text style={av.premBadgeText}>PREMIUM</Text>
          </View>
        </View>
        <Text style={[av.subtitle, { color: C.textMuted }]}>
          {t.sub_avSubtitle}
        </Text>
      </LinearGradient>

      {/* Tier rows */}
      <View style={av.tiers}>
        {tiers.map((t, i) => (
          <View
            key={t.name}
            style={[
              av.tierRow,
              i > 0 && { borderTopWidth: 1, borderTopColor: C.border },
              t.best && { backgroundColor: "#f9d76b0d" },
            ]}
          >
            <Text style={av.tierEmoji}>{t.emoji}</Text>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Text style={[av.tierName, { color: C.text }]}>{t.name}</Text>
                {t.best && (
                  <View style={av.bestBadge}>
                    <Text style={av.bestBadgeText}>BEST VALUE</Text>
                  </View>
                )}
              </View>
              <Text style={[av.tierSub, { color: C.textMuted }]}>{t.sub}</Text>
            </View>
            <Text style={[av.tierPrice, { color: t.color }]}>{t.price}</Text>
          </View>
        ))}
      </View>

      {/* Pro discount note */}
      <View style={[av.noteRow, { borderTopColor: C.border, backgroundColor: C.isDark ? "#0a0604" : "#fff8e1" }]}>
        <Feather name="zap" size={13} color="#f59e0b" />
        <Text style={[av.noteText, { color: C.textMuted }]}>
          <Text style={{ fontWeight: "800", color: "#f59e0b" }}>{t.sub_proSubsLabel}</Text> {t.sub_proGetSuffix}{" "}
          <Text style={{ fontWeight: "800", color: C.text }}>20%</Text> {t.sub_offSuffix}
        </Text>
      </View>

      {/* CTA */}
      <Pressable onPress={goAstroVastu} style={av.cta}>
        <Feather name="external-link" size={14} color="#3a2404" />
        <Text style={av.ctaText}>{t.sub_openAv}</Text>
      </Pressable>
    </View>
  );
}

const av = StyleSheet.create({
  wrap:           { borderRadius: 16, borderWidth: 2, marginTop: 16, overflow: "hidden" },
  headerGrad:     { paddingHorizontal: 14, paddingVertical: 12, gap: 6 },
  titleRow:       { flexDirection: "row", alignItems: "center", gap: 8 },
  title:          { fontSize: 14, fontWeight: "800", flex: 1 },
  premBadge:      { backgroundColor: "#f9d76b", paddingHorizontal: 7, paddingVertical: 2, borderRadius: 5 },
  premBadgeText:  { fontSize: 8, fontWeight: "900", color: "#3a2404", letterSpacing: 0.8 },
  subtitle:       { fontSize: 10.5, lineHeight: 15 },
  tiers:          { paddingHorizontal: 0 },
  tierRow:        { flexDirection: "row", alignItems: "center", gap: 11, paddingHorizontal: 14, paddingVertical: 11 },
  tierEmoji:      { fontSize: 20 },
  tierName:       { fontSize: 12.5, fontWeight: "700" },
  tierSub:        { fontSize: 10, marginTop: 2 },
  tierPrice:      { fontSize: 14, fontWeight: "900", letterSpacing: 0.3 },
  bestBadge:      { backgroundColor: "#f9d76b", paddingHorizontal: 5, paddingVertical: 1.5, borderRadius: 4 },
  bestBadgeText:  { fontSize: 7.5, fontWeight: "900", color: "#3a2404", letterSpacing: 0.6 },
  noteRow:        { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 14, paddingVertical: 10, borderTopWidth: 1 },
  noteText:       { fontSize: 10.5, lineHeight: 15, flex: 1 },
  cta:            { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, backgroundColor: "#f9d76b", paddingVertical: 12, marginHorizontal: 14, marginVertical: 12, borderRadius: 10 },
  ctaText:        { fontSize: 13, fontWeight: "800", color: "#3a2404", letterSpacing: 0.3 },
});

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
