import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { LoveRealitySocialProof } from "@/components/loveReality/LoveRealitySocialProof";
import { FOUNDER_PROFILE } from "@/lib/founderProfile";
import {
  LOVE_PRO_UNLOCK_ITEMS,
  LOVE_REALITY_BASIC_TO_PRO_BRIDGE,
  LOVE_REALITY_CORE_QUESTIONS,
  LOVE_REALITY_CORE_QUESTIONS_TITLE,
  LOVE_REALITY_DELIVERY_OPTIONS,
  LOVE_REALITY_FOUNDER_TRUST,
  LOVE_REALITY_PRO_CTA_MICROCOPY,
  LOVE_REALITY_PRO_TRUST_BAR,
  LOVE_REALITY_PRO_HERO,
  LOVE_REALITY_REPORT_SECTION_TITLE,
  loveRealityPartnerReportTitle,
  loveRealitySavingsMessage,
} from "@/lib/loveRealityProCopy";
import {
  LOVE_REALITY_PRO_UI_PRICING,
  LOVE_REALITY_URGENT_SURCHARGE_INR,
  loveRealityFirstTimeSavingsInr,
  loveRealityOrderTotalInr,
} from "@/lib/loveRealityProOffer";

export function LoveRealityProPurchase({
  isDark,
  primaryName,
  partnerName,
  priorityDelivery,
  onPriorityDeliveryChange,
}: {
  isDark: boolean;
  primaryName?: string | null;
  partnerName?: string | null;
  priorityDelivery: boolean;
  onPriorityDeliveryChange: (value: boolean) => void;
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
  const savingsInr = loveRealityFirstTimeSavingsInr();
  const totalInr = loveRealityOrderTotalInr(priorityDelivery);
  const savingsGreen = isDark ? "#86efac" : "#15803d";
  const standardDelivery = LOVE_REALITY_DELIVERY_OPTIONS[0];
  const priorityOption = LOVE_REALITY_DELIVERY_OPTIONS[1];
  const showPartnerBanner = !!(primaryName?.trim() && partnerName?.trim());

  return (
    <Animated.View style={{ opacity: fadeAnim, gap: 14 }}>
      {showPartnerBanner ? (
        <View style={[s.partnerBanner, { backgroundColor: cardBg, borderColor: border }]}>
          <Feather name="heart" size={14} color="#f472b6" />
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={[s.partnerTitle, { color: titleColor }]}>
              {loveRealityPartnerReportTitle(primaryName!.trim(), partnerName!.trim())}
            </Text>
            <Text style={[s.partnerBridge, { color: bodyColor }]}>{LOVE_REALITY_BASIC_TO_PRO_BRIDGE}</Text>
          </View>
        </View>
      ) : null}

      {/* Hero — top hook */}
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

      {/* Founder trust */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <View style={s.founderHead}>
          {FOUNDER_PROFILE.photoUri ? (
            <Image source={{ uri: FOUNDER_PROFILE.photoUri }} style={s.founderPhoto} />
          ) : (
            <LinearGradient colors={["#9333ea", "#ec4899"]} style={s.founderPhoto}>
              <Text style={s.founderInitials}>{FOUNDER_PROFILE.initials}</Text>
            </LinearGradient>
          )}
          <View style={{ flex: 1, gap: 3 }}>
            <Text style={[s.founderName, { color: titleColor }]}>{FOUNDER_PROFILE.displayName}</Text>
            <Text style={[s.founderRole, { color: bodyColor }]}>{FOUNDER_PROFILE.roleLine}</Text>
          </View>
        </View>
        <Text style={[s.founderSectionTitle, { color: titleColor }]}>{LOVE_REALITY_FOUNDER_TRUST.title}</Text>
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

      {/* Delivery */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>Delivery</Text>
        <View style={{ gap: 10, marginTop: 12 }}>
          <View style={[s.deliveryRow, { borderColor: border }]}>
            <Text style={s.deliveryEmoji}>{standardDelivery.emoji}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.deliveryTitle, { color: titleColor }]}>{standardDelivery.title}</Text>
              <Text style={[s.deliveryEta, { color: bodyColor }]}>{standardDelivery.eta}</Text>
            </View>
          </View>
          <Pressable
            onPress={() => {
              onPriorityDeliveryChange(!priorityDelivery);
              Haptics.selectionAsync();
            }}
            style={[
              s.deliveryRow,
              {
                borderColor: priorityDelivery ? (isDark ? "#f59e0b" : "#d97706") : border,
                backgroundColor: priorityDelivery ? (isDark ? "rgba(245,158,11,0.08)" : "rgba(245,158,11,0.06)") : "transparent",
              },
            ]}
          >
            <View style={[s.priorityCheck, { borderColor: priorityDelivery ? "#f59e0b" : border, backgroundColor: priorityDelivery ? "#f59e0b" : "transparent" }]}>
              {priorityDelivery ? <Feather name="check" size={12} color="#fff" /> : null}
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.deliveryTitle, { color: titleColor }]}>
                Priority Delivery (+₹{priorityOption.surchargeInr})
              </Text>
              <Text style={[s.deliveryEta, { color: bodyColor }]}>{priorityOption.eta}</Text>
            </View>
          </Pressable>
        </View>
      </View>

      <LoveRealitySocialProof visible={false} />

      {/* Pricing */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <View style={s.priceBlock}>
          <Text style={[s.priceRegularLabel, { color: bodyColor }]}>Regular Price</Text>
          <Text style={[s.priceStrike, { color: bodyColor }]}>₹{regularInr}</Text>
          <Text style={[s.priceTodayLabel, { color: bodyColor }]}>Total</Text>
          <Text style={[s.priceToday, { color: titleColor }]}>₹{totalInr}</Text>
          {priorityDelivery ? (
            <Text style={[s.priceAddonNote, { color: bodyColor }]}>
              Base ₹{todayInr} + Priority ₹{LOVE_REALITY_URGENT_SURCHARGE_INR}
            </Text>
          ) : null}
        </View>
        <View style={[s.discountBadge, { backgroundColor: isDark ? "rgba(34,197,94,0.15)" : "rgba(34,197,94,0.1)", borderColor: isDark ? "rgba(34,197,94,0.35)" : "rgba(34,197,94,0.3)" }]}>
          <Text style={[s.discountBadgeTxt, { color: savingsGreen }]}>
            ✅ {firstTimeDiscountBadge}
          </Text>
          <Text style={[s.savingsTxt, { color: savingsGreen }]}>{loveRealitySavingsMessage(savingsInr)}</Text>
        </View>
      </View>

      <Text style={[s.trustBar, { color: bodyColor }]}>{LOVE_REALITY_PRO_TRUST_BAR}</Text>
      <Text style={[s.microcopy, { color: bodyColor }]}>{LOVE_REALITY_PRO_CTA_MICROCOPY}</Text>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  partnerBanner: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
  },
  partnerTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", lineHeight: 21 },
  partnerBridge: { fontSize: 12.5, fontFamily: "Nunito_500Medium", lineHeight: 18 },
  card: { borderRadius: 18, borderWidth: 1, padding: 16 },
  founderHead: { flexDirection: "row", alignItems: "center", gap: 12, marginBottom: 14 },
  founderPhoto: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  founderInitials: { color: "#fff", fontSize: 16, fontFamily: "Nunito_800ExtraBold" },
  founderName: { fontSize: 15, fontFamily: "Nunito_800ExtraBold" },
  founderRole: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  founderSectionTitle: { fontSize: 14, fontFamily: "Nunito_700Bold", marginBottom: 6 },
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
  priorityCheck: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  priceBlock: { alignItems: "center", gap: 2, marginBottom: 12 },
  priceAddonNote: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 4 },
  priceRegularLabel: { fontSize: 12, fontFamily: "Nunito_500Medium" },
  priceStrike: { fontSize: 16, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceTodayLabel: { fontSize: 12, fontFamily: "Nunito_500Medium", marginTop: 6 },
  priceToday: { fontSize: 32, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.5 },
  discountBadge: {
    alignSelf: "center",
    alignItems: "center",
    gap: 3,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
  },
  discountBadgeTxt: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  savingsTxt: { fontSize: 11, fontFamily: "Nunito_700Bold" },
  trustBar: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    textAlign: "center",
    lineHeight: 16,
    paddingHorizontal: 4,
  },
  microcopy: {
    fontSize: 11.5,
    fontFamily: "Nunito_500Medium",
    lineHeight: 17,
    textAlign: "center",
    paddingHorizontal: 8,
    marginBottom: 8,
  },
});
