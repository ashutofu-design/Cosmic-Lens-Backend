import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { LoveRealitySocialProof } from "@/components/loveReality/LoveRealitySocialProof";
import {
  LOVE_PRO_UNLOCK_ITEMS,
  LOVE_REALITY_CORE_QUESTIONS,
  LOVE_REALITY_CORE_QUESTIONS_TITLE,
  LOVE_REALITY_DELIVERY_OPTIONS,
  LOVE_REALITY_FOUNDER_TRUST,
  LOVE_REALITY_PRO_CTA_MICROCOPY,
  LOVE_REALITY_PRO_CTA_TITLE,
  LOVE_REALITY_PRO_HERO,
  LOVE_REALITY_REPORT_SECTION_TITLE,
} from "@/lib/loveRealityProCopy";
import { LOVE_REALITY_PRO_UI_PRICING } from "@/lib/loveRealityProOffer";

export function LoveRealityProPurchase({
  isDark,
  canPro,
  loading,
  onUnlock,
}: {
  isDark: boolean;
  canPro: boolean;
  loading: boolean;
  onUnlock: () => void;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  const cardBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.92)";
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const titleColor = isDark ? "#f8fafc" : "#0f172a";
  const bodyColor = isDark ? "rgba(226,232,240,0.72)" : "#64748b";
  const { regularInr, todayInr, firstTimeDiscountBadge } = LOVE_REALITY_PRO_UI_PRICING;

  return (
    <Animated.View style={{ opacity: fadeAnim, gap: 14 }}>
      {/* Founder trust */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <View style={s.founderHead}>
          <View style={s.founderIcon}>
            <Feather name="award" size={18} color="#c084fc" />
          </View>
          <Text style={[s.founderTitle, { color: titleColor }]}>{LOVE_REALITY_FOUNDER_TRUST.title}</Text>
        </View>
        <Text style={[s.founderDesc, { color: bodyColor }]}>{LOVE_REALITY_FOUNDER_TRUST.description}</Text>
        <View style={s.bulletList}>
          {LOVE_REALITY_FOUNDER_TRUST.bullets.map(b => (
            <View key={b} style={s.bulletRow}>
              <Feather name="check" size={14} color="#22c55e" />
              <Text style={[s.bulletTxt, { color: titleColor }]}>{b}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Hero selling card */}
      <View style={[s.heroCard, { borderColor: isDark ? "rgba(236,72,153,0.5)" : "rgba(236,72,153,0.35)" }]}>
        <LinearGradient
          colors={isDark ? ["rgba(236,72,153,0.22)", "rgba(168,85,247,0.14)"] : ["rgba(236,72,153,0.1)", "rgba(168,85,247,0.06)"]}
          style={StyleSheet.absoluteFill}
        />
        <Text style={s.heroEmoji}>{LOVE_REALITY_PRO_HERO.emoji}</Text>
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={[s.heroTitle, { color: titleColor }]}>{LOVE_REALITY_PRO_HERO.title}</Text>
          <Text style={[s.heroLine, { color: bodyColor }]}>{LOVE_REALITY_PRO_HERO.line}</Text>
        </View>
      </View>

      {/* Core questions */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>{LOVE_REALITY_CORE_QUESTIONS_TITLE}</Text>
        <View style={s.coreQList}>
          {LOVE_REALITY_CORE_QUESTIONS.map((q, i) => (
            <View key={q} style={[s.coreQRow, { borderColor: border }]}>
              <Text style={[s.coreQNum, { color: isDark ? "#c084fc" : "#9333ea" }]}>{i + 1}</Text>
              <Text style={[s.coreQText, { color: titleColor }]}>{q}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Report content */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>{LOVE_REALITY_REPORT_SECTION_TITLE}</Text>
        <View style={{ gap: 10, marginTop: 12 }}>
          {LOVE_PRO_UNLOCK_ITEMS.map(sec => (
            <View key={sec.title} style={[s.reportRow, { borderColor: border }]}>
              <Text style={s.reportEmoji}>{sec.emoji}</Text>
              <View style={{ flex: 1, gap: 3 }}>
                <Text style={[s.reportTitle, { color: titleColor }]}>{sec.title}</Text>
                <Text style={[s.reportHook, { color: bodyColor }]}>{sec.shortHook}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* Delivery promise */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>Delivery</Text>
        <View style={{ gap: 10, marginTop: 12 }}>
          {LOVE_REALITY_DELIVERY_OPTIONS.map(opt => (
            <View key={opt.title} style={[s.deliveryRow, { borderColor: border }]}>
              <Text style={s.deliveryEmoji}>{opt.emoji}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[s.deliveryTitle, { color: titleColor }]}>{opt.title}</Text>
                <Text style={[s.deliveryEta, { color: bodyColor }]}>{opt.eta}</Text>
              </View>
              {opt.surchargeInr > 0 ? (
                <Text style={[s.deliverySurcharge, { color: isDark ? "#fbbf24" : "#d97706" }]}>
                  +₹{opt.surchargeInr}
                </Text>
              ) : null}
            </View>
          ))}
        </View>
      </View>

      <LoveRealitySocialProof visible={false} />

      {/* Pricing */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <View style={s.priceBlock}>
          <Text style={[s.priceRegularLabel, { color: bodyColor }]}>Regular Price</Text>
          <Text style={[s.priceStrike, { color: bodyColor }]}>₹{regularInr}</Text>
          <Text style={[s.priceTodayLabel, { color: bodyColor }]}>Today</Text>
          <Text style={[s.priceToday, { color: titleColor }]}>₹{todayInr}</Text>
        </View>
        <View style={[s.discountBadge, { backgroundColor: isDark ? "rgba(34,197,94,0.15)" : "rgba(34,197,94,0.1)", borderColor: isDark ? "rgba(34,197,94,0.35)" : "rgba(34,197,94,0.3)" }]}>
          <Text style={[s.discountBadgeTxt, { color: isDark ? "#86efac" : "#15803d" }]}>
            ✅ {firstTimeDiscountBadge}
          </Text>
        </View>
      </View>

      {/* CTA */}
      <Pressable
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          onUnlock();
        }}
        disabled={loading || !canPro}
        style={({ pressed }) => ({ opacity: !canPro ? 0.55 : pressed ? 0.9 : 1 })}
      >
        <LinearGradient
          colors={canPro ? ["#7c3aed", "#db2777"] : ["#4b5563", "#374151"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={s.ctaGrad}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={s.ctaText}>
              {canPro ? LOVE_REALITY_PRO_CTA_TITLE : "Add partner kundli to unlock"}
            </Text>
          )}
        </LinearGradient>
      </Pressable>

      <Text style={[s.microcopy, { color: bodyColor }]}>{LOVE_REALITY_PRO_CTA_MICROCOPY}</Text>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 16 },
  founderHead: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 10 },
  founderIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: "rgba(168,85,247,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  founderTitle: { flex: 1, fontSize: 16, fontFamily: "Nunito_700Bold", lineHeight: 22 },
  founderDesc: { fontSize: 13, fontFamily: "Nunito_400Regular", lineHeight: 20, marginBottom: 12 },
  bulletList: { gap: 8 },
  bulletRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  bulletTxt: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
  heroCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 16,
    borderRadius: 18,
    borderWidth: 1,
    overflow: "hidden",
  },
  heroEmoji: { fontSize: 30 },
  heroTitle: { fontSize: 16, fontFamily: "Nunito_800ExtraBold" },
  heroLine: { fontSize: 13, fontFamily: "Nunito_500Medium", lineHeight: 19 },
  sectionTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  coreQList: { gap: 10, marginTop: 14 },
  coreQRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  coreQNum: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", width: 20 },
  coreQText: { flex: 1, fontSize: 16, fontFamily: "Nunito_700Bold", lineHeight: 22 },
  reportRow: {
    flexDirection: "row",
    gap: 10,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  reportEmoji: { fontSize: 18, marginTop: 1 },
  reportTitle: { fontSize: 13.5, fontFamily: "Nunito_700Bold" },
  reportHook: { fontSize: 12, fontFamily: "Nunito_400Regular", lineHeight: 17 },
  deliveryRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  deliveryEmoji: { fontSize: 20 },
  deliveryTitle: { fontSize: 13.5, fontFamily: "Nunito_700Bold" },
  deliveryEta: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 2 },
  deliverySurcharge: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  priceBlock: { alignItems: "center", gap: 2, marginBottom: 12 },
  priceRegularLabel: { fontSize: 12, fontFamily: "Nunito_500Medium" },
  priceStrike: { fontSize: 16, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceTodayLabel: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 6 },
  priceToday: { fontSize: 32, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.5 },
  discountBadge: {
    alignSelf: "center",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
  },
  discountBadgeTxt: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  ctaGrad: { borderRadius: 14, paddingVertical: 16, alignItems: "center" },
  ctaText: { color: "#fff", fontSize: 15, fontFamily: "Nunito_800ExtraBold", textAlign: "center" },
  microcopy: {
    fontSize: 11.5,
    fontFamily: "Nunito_500Medium",
    lineHeight: 17,
    textAlign: "center",
    paddingHorizontal: 8,
  },
});
