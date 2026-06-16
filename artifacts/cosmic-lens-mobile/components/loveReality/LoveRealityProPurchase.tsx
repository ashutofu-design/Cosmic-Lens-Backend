import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef, useState } from "react";
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
import { loveRealityProPurchaseCopy } from "@/lib/loveRealityProCopyI18n";
import type { ProPdfLangCode } from "@/lib/proPdfLang";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import {
  LOVE_REALITY_PRO_UI_PRICING,
  loveRealityFirstTimeSavingsInr,
  loveRealityOrderTotalInr,
} from "@/lib/loveRealityProOffer";

export function LoveRealityProPurchase({
  isDark,
  primaryName,
  partnerName,
  priorityDelivery,
  onPriorityDeliveryChange,
  lang = "en",
}: {
  isDark: boolean;
  primaryName?: string | null;
  partnerName?: string | null;
  priorityDelivery: boolean;
  onPriorityDeliveryChange: (value: boolean) => void;
  lang?: ProPdfLangCode;
}) {
  const lane = coerceProPdfLang(lang);
  const copy = loveRealityProPurchaseCopy(lane);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const [founderExpanded, setFounderExpanded] = useState(false);

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
  const { regularInr } = LOVE_REALITY_PRO_UI_PRICING;
  const savingsInr = loveRealityFirstTimeSavingsInr();
  const totalInr = loveRealityOrderTotalInr(priorityDelivery);
  const savingsGreen = isDark ? "#86efac" : "#15803d";
  const standardDelivery = copy.deliveryOptions[0];
  const priorityOption = copy.deliveryOptions[1];
  const showPartnerBanner = !!(primaryName?.trim() && partnerName?.trim());

  return (
    <Animated.View style={{ opacity: fadeAnim, gap: 10 }}>
      {showPartnerBanner ? (
        <View style={[s.partnerBanner, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[s.partnerLine, { color: titleColor }]} numberOfLines={2}>
            <Text style={s.partnerHeart}>💕 </Text>
            <Text style={s.partnerNames}>
              {primaryName!.trim()} & {partnerName!.trim()}
            </Text>
            <Text style={[s.partnerMeta, { color: bodyColor }]}>{copy.partnerMeta}</Text>
          </Text>
        </View>
      ) : null}

      {/* Hero — top hook */}
      <View style={[s.heroCard, { borderColor: isDark ? "rgba(236,72,153,0.5)" : "rgba(236,72,153,0.35)" }]}>
        <LinearGradient
          colors={isDark ? ["rgba(236,72,153,0.22)", "rgba(168,85,247,0.14)"] : ["rgba(236,72,153,0.1)", "rgba(168,85,247,0.06)"]}
          style={StyleSheet.absoluteFill}
        />
        <Text style={s.heroEmoji}>{copy.hero.emoji}</Text>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={[s.heroTitle, { color: titleColor }]}>{copy.hero.title}</Text>
          <Text style={[s.heroLine, { color: bodyColor }]} numberOfLines={2}>
            {copy.hero.line}
          </Text>
        </View>
      </View>

      {/* Founder trust — compact, expandable */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Pressable
          onPress={() => {
            setFounderExpanded(v => !v);
            Haptics.selectionAsync();
          }}
          style={s.founderHead}
        >
          {FOUNDER_PROFILE.photoUri ? (
            <Image source={{ uri: FOUNDER_PROFILE.photoUri }} style={s.founderPhoto} />
          ) : (
            <LinearGradient colors={["#9333ea", "#ec4899"]} style={s.founderPhoto}>
              <Text style={s.founderInitials}>{FOUNDER_PROFILE.initials}</Text>
            </LinearGradient>
          )}
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={[s.founderName, { color: titleColor }]}>{FOUNDER_PROFILE.displayName}</Text>
            <Text style={[s.founderRole, { color: bodyColor }]} numberOfLines={founderExpanded ? 3 : 1}>
              {founderExpanded ? copy.founderTrust.description : copy.founderTrust.bullets[0]}
            </Text>
          </View>
          <Feather
            name={founderExpanded ? "chevron-up" : "chevron-down"}
            size={18}
            color={isDark ? "#c084fc" : "#9333ea"}
          />
        </Pressable>
        {founderExpanded ? (
          <View style={s.founderBulletGrid}>
            {copy.founderTrust.bullets.map(b => (
              <View key={b} style={[s.founderBulletChip, { borderColor: border }]}>
                <Feather name="check" size={11} color="#22c55e" />
                <Text style={[s.founderBulletTxt, { color: titleColor }]}>{b}</Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={s.founderChipRow}>
            {copy.founderTrust.bullets.slice(0, 2).map(b => (
              <View key={b} style={[s.founderBulletChip, { borderColor: border }]}>
                <Feather name="check" size={10} color="#22c55e" />
                <Text style={[s.founderBulletTxt, { color: titleColor }]} numberOfLines={1}>{b}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Core questions — compact */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>{copy.coreQuestionsTitle}</Text>
        <Text style={[s.reportSummary, { color: bodyColor }]}>{copy.coreQuestions.join(" · ")}</Text>
        <View style={s.coreQChipRow}>
          {copy.coreQuestions.map((q, i) => (
            <View key={q} style={[s.coreQChip, { borderColor: border }]}>
              <Text style={[s.coreQChipNum, { color: isDark ? "#c084fc" : "#9333ea" }]}>{i + 1}</Text>
              <Text style={[s.coreQChipTxt, { color: titleColor }]} numberOfLines={1}>
                {q}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Report content — compact */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>{copy.reportSectionTitle}</Text>
        <Text style={[s.reportSummary, { color: bodyColor }]}>{copy.unlockItems.length} personalized sections</Text>
        <View style={s.reportChipRow}>
          {copy.unlockItems.map(sec => (
            <View key={sec.title} style={[s.reportChip, { borderColor: border }]}>
              <Text style={s.reportChipEmoji}>{sec.emoji}</Text>
              <Text style={[s.reportChipTxt, { color: titleColor }]} numberOfLines={1}>
                {sec.title.split(" / ")[0]}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Delivery — compact */}
      <View style={[s.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[s.sectionTitle, { color: titleColor }]}>{copy.deliveryOptions[0].title}</Text>
        <Text style={[s.deliveryStandardLine, { color: bodyColor }]} numberOfLines={1}>
          📁 My Reports · {standardDelivery.eta.toLowerCase()}
        </Text>
        <Pressable
          onPress={() => {
            onPriorityDeliveryChange(!priorityDelivery);
            Haptics.selectionAsync();
          }}
          style={[
            s.deliveryPriorityRow,
            {
              borderColor: priorityDelivery ? (isDark ? "#f59e0b" : "#d97706") : border,
              backgroundColor: priorityDelivery ? (isDark ? "rgba(245,158,11,0.08)" : "rgba(245,158,11,0.06)") : "transparent",
            },
          ]}
        >
          <View style={[s.priorityCheck, { borderColor: priorityDelivery ? "#f59e0b" : border, backgroundColor: priorityDelivery ? "#f59e0b" : "transparent" }]}>
            {priorityDelivery ? <Feather name="check" size={10} color="#fff" /> : null}
          </View>
          <Text style={[s.deliveryPriorityTxt, { color: titleColor }]} numberOfLines={1}>
            {priorityOption.emoji} Priority +₹{priorityOption.surchargeInr} · {priorityOption.eta.toLowerCase()}
          </Text>
        </Pressable>
        <Text style={[s.deliveryRefundNote, { color: bodyColor }]} numberOfLines={2}>
          {copy.priorityRefund}
        </Text>
        <View style={[s.priceDivider, { backgroundColor: border }]} />
        <Text style={[s.priceInline, { color: titleColor }]}>
          <Text style={[s.priceStrikeTiny, { color: bodyColor }]}>₹{regularInr}</Text>
          <Text style={s.priceArrow}> → </Text>
          <Text style={s.priceTotalTiny}>₹{totalInr}</Text>
          <Text style={[s.priceSavedTiny, { color: savingsGreen }]}> · {copy.savings(savingsInr)}</Text>
        </Text>
      </View>

      <LoveRealitySocialProof visible={false} />

      <Text style={[s.trustBar, { color: bodyColor }]}>{copy.trustBar}</Text>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  partnerBanner: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  partnerLine: { fontSize: 12.5, lineHeight: 17 },
  partnerHeart: { fontSize: 12 },
  partnerNames: { fontFamily: "Nunito_800ExtraBold" },
  partnerMeta: { fontFamily: "Nunito_500Medium" },
  card: { borderRadius: 18, borderWidth: 1, padding: 16 },
  founderHead: { flexDirection: "row", alignItems: "center", gap: 10 },
  founderPhoto: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  founderInitials: { color: "#fff", fontSize: 13, fontFamily: "Nunito_800ExtraBold" },
  founderName: { fontSize: 13.5, fontFamily: "Nunito_800ExtraBold" },
  founderRole: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 15 },
  founderChipRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  founderBulletGrid: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  founderBulletChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    maxWidth: "48%",
    flexGrow: 1,
  },
  founderBulletTxt: { fontSize: 10, fontFamily: "Nunito_700Bold", flexShrink: 1 },
  heroCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
  },
  heroEmoji: { fontSize: 22 },
  heroTitle: { fontSize: 14.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 19 },
  heroLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  sectionTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  coreQChipRow: { gap: 6, marginTop: 10 },
  coreQChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 7,
    paddingHorizontal: 10,
    borderRadius: 9,
    borderWidth: 1,
  },
  coreQChipNum: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", width: 14 },
  coreQChipTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_700Bold" },
  reportSummary: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
  reportChipRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 10 },
  reportChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 5,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    maxWidth: "48%",
    flexGrow: 1,
  },
  reportChipEmoji: { fontSize: 12 },
  reportChipTxt: { fontSize: 10.5, fontFamily: "Nunito_700Bold", flexShrink: 1 },
  deliveryStandardLine: {
    fontSize: 11.5,
    fontFamily: "Nunito_500Medium",
    marginTop: 6,
  },
  deliveryPriorityRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginTop: 6,
    paddingVertical: 7,
    paddingHorizontal: 9,
    borderRadius: 9,
    borderWidth: 1,
  },
  deliveryPriorityTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold" },
  deliveryRefundNote: {
    fontSize: 10,
    fontFamily: "Nunito_500Medium",
    marginTop: 5,
    lineHeight: 14,
  },
  priorityCheck: {
    width: 16,
    height: 16,
    borderRadius: 4,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  priceDivider: { height: 1, marginTop: 10, marginBottom: 8 },
  priceInline: { fontSize: 12, lineHeight: 17 },
  priceStrikeTiny: { fontSize: 12, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceArrow: { fontSize: 12, fontFamily: "Nunito_500Medium", color: "rgba(148,163,184,0.9)" },
  priceTotalTiny: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  priceSavedTiny: { fontSize: 10.5, fontFamily: "Nunito_700Bold" },
  trustBar: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    textAlign: "center",
    lineHeight: 16,
    paddingHorizontal: 4,
  },
});
