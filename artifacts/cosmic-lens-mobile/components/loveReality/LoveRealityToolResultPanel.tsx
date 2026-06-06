import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { LoveRealityResultHero, LoyaltyCompareCard } from "@/components/loveReality/LoveRealityBasicScreen";
import type { LoveRealityBasicDisplay, LoveRealityToolKey, LoyaltyCompareData } from "@/lib/loveRealityToolMappers";

export function LoveRealityToolResultPanel({
  toolKey,
  toolTitle,
  userName,
  partnerName,
  display,
  loyaltyCompare,
  isDark,
  bottomPad,
  accentGradient,
  showHeader = false,
  onBack,
  onRefresh,
  refreshing = false,
}: {
  toolKey?: LoveRealityToolKey;
  toolTitle: string;
  userName: string;
  partnerName: string;
  display: LoveRealityBasicDisplay;
  loyaltyCompare?: LoyaltyCompareData;
  isDark: boolean;
  bottomPad: number;
  accentGradient: [string, string];
  onOpenPro?: () => void;
  showHeader?: boolean;
  onBack?: () => void;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const textHi = isDark ? "#fff" : "#0F172A";
  const compare = loyaltyCompare ?? display.loyaltyCompare;
  const isLoyaltyTool = toolKey === "loyalty";

  return (
    <View style={p.root}>
      {showHeader && (
        <View style={p.header}>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              onBack?.();
            }}
            hitSlop={8}
          >
            <View
              style={[
                p.backCircle,
                {
                  borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
                  backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                },
              ]}
            >
              <Feather name="chevron-left" size={22} color={textHi} />
            </View>
          </Pressable>
          <Text style={[p.headerTitle, { color: textHi }]} numberOfLines={1}>
            {toolTitle}
          </Text>
          {onRefresh ? (
            <Pressable
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                onRefresh();
              }}
              hitSlop={8}
              disabled={refreshing}
            >
              <Feather name="refresh-cw" size={18} color={refreshing ? textHi + "55" : textHi} />
            </Pressable>
          ) : (
            <View style={{ width: 40 }} />
          )}
        </View>
      )}

      <ScrollView
        style={p.bodyScroll}
        contentContainerStyle={[p.body, { paddingBottom: bottomPad + 12 }]}
        showsVerticalScrollIndicator={false}
        bounces={false}
      >
        <LoveRealityResultHero
          display={display}
          isDark={isDark}
          accentGradient={accentGradient}
          compact
          hideLoyaltyCompare
        />
        {isLoyaltyTool && compare ? (
          <LoyaltyCompareCard
            compare={compare}
            youName={userName}
            partnerName={partnerName}
            isDark={isDark}
            compact
          />
        ) : isLoyaltyTool && !compare ? (
          <Text style={[p.hook, { color: isDark ? "rgba(203,213,225,0.72)" : "#64748B" }]}>
            Dono ka compare load nahi hua — neeche &quot;Refresh loyalty reading&quot; dabao. Agar phir bhi na aaye to server update chahiye.
          </Text>
        ) : null}
        {display.hookLine ? (
          <Text
            style={[
              p.hook,
              { color: isDark ? "rgba(203,213,225,0.72)" : "#64748B" },
            ]}
          >
            {display.hookLine}
          </Text>
        ) : null}
      </ScrollView>
    </View>
  );
}

const p = StyleSheet.create({
  root: { flex: 1, minHeight: 0 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingBottom: 6,
    gap: 10,
  },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  headerTitle: { flex: 1, fontSize: 17, fontFamily: "Nunito_700Bold", textAlign: "center" },
  bodyScroll: { flex: 1, minHeight: 0 },
  body: {
    flexGrow: 1,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  hook: {
    marginTop: 12,
    fontSize: 12,
    fontFamily: "Nunito_600SemiBold",
    lineHeight: 17,
    textAlign: "center",
    maxWidth: 300,
    paddingHorizontal: 8,
  },
});
