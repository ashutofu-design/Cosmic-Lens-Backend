import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import type { ProPdfLangCode } from "@/lib/proPdfLang";
import { coerceProPdfLang } from "@/lib/proPdfLang";
import { loveRealityProPurchaseCopy } from "@/lib/loveRealityProCopyI18n";

export function LoveRealityProStickyCta({
  isDark,
  canPro,
  loading,
  regularInr,
  totalInr,
  onUnlock,
  lang = "en",
  isVideo = false,
}: {
  isDark: boolean;
  canPro: boolean;
  loading: boolean;
  regularInr: number;
  totalInr: number;
  onUnlock: () => void;
  lang?: ProPdfLangCode;
  isVideo?: boolean;
}) {
  const copy = loveRealityProPurchaseCopy(coerceProPdfLang(lang));
  const insets = useSafeAreaInsets();
  const border = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const bg = isDark ? "rgba(15,10,31,0.96)" : "rgba(255,255,255,0.97)";

  return (
    <View
      style={[
        s.wrap,
        {
          paddingBottom: Math.max(insets.bottom, 12),
          backgroundColor: bg,
          borderTopColor: border,
        },
      ]}
    >
      <View style={s.row}>
        <View style={s.priceCol}>
          {isVideo ? null : (
            <Text style={[s.priceStrike, { color: isDark ? "rgba(226,232,240,0.45)" : "#94a3b8" }]}>₹{regularInr}</Text>
          )}
          <Text style={[s.priceVal, { color: isDark ? "#f8fafc" : "#0f172a" }]}>₹{totalInr}</Text>
        </View>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            onUnlock();
          }}
          disabled={loading || !canPro}
          style={({ pressed }) => [s.ctaPress, { flex: 1, opacity: !canPro ? 0.55 : pressed ? 0.9 : 1 }]}
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
              <Text style={s.ctaText} numberOfLines={2}>
                {canPro ? (isVideo ? copy.ctaVideoTitle : copy.ctaTitle) : copy.addPartnerCta}
              </Text>
            )}
          </LinearGradient>
        </Pressable>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    borderTopWidth: 1,
    paddingTop: 10,
    paddingHorizontal: 16,
    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOpacity: 0.12,
        shadowRadius: 8,
        shadowOffset: { width: 0, height: -3 },
      },
      android: { elevation: 12 },
    }),
  },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  priceCol: { minWidth: 56 },
  priceStrike: { fontSize: 10, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceVal: { fontSize: 20, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.5, marginTop: -2 },
  ctaPress: { borderRadius: 14, overflow: "hidden" },
  ctaGrad: { paddingVertical: 14, paddingHorizontal: 12, alignItems: "center", justifyContent: "center", minHeight: 48 },
  ctaText: { color: "#fff", fontSize: 13, fontFamily: "Nunito_800ExtraBold", textAlign: "center" },
});
